`timescale 1ns/1ps
module matrix_core #(
    parameter int DATA_W     = 8,
    parameter int ACC_W      = 32,
    parameter int MAX_M      = 8,
    parameter int MAX_K      = 8,
    parameter int MAX_N      = 8,
    parameter int SRAM_W     = 32,
    parameter int ADDR_WIDTH = 32,
    parameter int PE_PIPE    = 1,
    parameter int SMT_THREADS = 4
)(
    input  logic                    clk,
    input  logic                    rst_n,

    input  logic                        core_start,
    input  logic                        allow_b_reuse,
    input  logic [$clog2(MAX_M+1)-1:0]  mat_m_num,
    input  logic [$clog2(MAX_K+1)-1:0]  mat_k_num,
    input  logic [$clog2(MAX_N+1)-1:0]  mat_n_num,

    input  logic [ADDR_WIDTH-1:0]       base_addr_A,
    input  logic [ADDR_WIDTH-1:0]       row_stride_A,

    input  logic [ADDR_WIDTH-1:0]       base_addr_B,
    input  logic [ADDR_WIDTH-1:0]       row_stride_B,

    output logic                    mem_valid,
    input  logic                    mem_ready,
    output logic [31:0]             mem_addr,
    output logic [31:0]             mem_wdata,
    output logic [3:0]              mem_wstrb,
    input  logic [31:0]             mem_rdata,

    output logic [ACC_W*MAX_M*MAX_N-1:0] partial_sum_flat,

    output logic                   core_busy,
    output logic                   core_done
);

    localparam logic [2:0]
        S_IDLE    = 3'd0,
        S_LOAD_A  = 3'd1,
        S_LOAD_B  = 3'd2,
        S_START   = 3'd3,
        S_COMPUTE = 3'd4;

    logic [2:0] state, state_n;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_IDLE;
        else
            state <= state_n;
    end

    logic a_valid, a_done, a_ready;
    logic [MAX_K*DATA_W-1:0] a_row;
    logic a_rd_valid;
    logic [ADDR_WIDTH-1:0] a_rd_addr;
    logic a_rd_ready;
    logic [SRAM_W-1:0] a_rd_data;

    logic b_valid, b_done, b_ready;
    logic [MAX_N*DATA_W-1:0] b_row;
    logic b_rd_valid;
    logic [ADDR_WIDTH-1:0] b_rd_addr;
    logic b_rd_ready;
    logic [SRAM_W-1:0] b_rd_data;

    wire fifoA_start = (state == S_IDLE)   && (state_n == S_LOAD_A);
    wire fifoB_start = (state == S_LOAD_A) && (state_n == S_LOAD_B);

    matrix_fetch #(
        .DATA_WIDTH   (DATA_W),
        .SRAM_WIDTH   (SRAM_W),
        .MAX_COL_NUM  (MAX_K),
        .MAX_ROW_NUM  (MAX_M),
        .ADDR_WIDTH   (ADDR_WIDTH)
    ) u_fifoA (
        .clk              (clk),
        .rst_n            (rst_n),
        .start            (fifoA_start),
        .col_num          (mat_k_num),
        .row_num          (mat_m_num),
        .base_addr        (base_addr_A),
        .rd_valid         (a_rd_valid),
        .rd_addr          (a_rd_addr),
        .rd_ready         (a_rd_ready),
        .rd_data          (a_rd_data),
        .fetch_row_valid  (a_valid),
        .fetch_row_data   (a_row),
        .fetch_done       (a_done),
        .fetch_busy       (),
        .fetch_row_ready  (a_ready),
        .fetch_row_stride (row_stride_A)
    );

    matrix_fetch #(
        .DATA_WIDTH   (DATA_W),
        .SRAM_WIDTH   (SRAM_W),
        .MAX_COL_NUM  (MAX_N),
        .MAX_ROW_NUM  (MAX_K),
        .ADDR_WIDTH   (ADDR_WIDTH)
    ) u_fifoB (
        .clk              (clk),
        .rst_n            (rst_n),
        .start            (fifoB_start),
        .col_num          (mat_n_num),
        .row_num          (mat_k_num),
        .base_addr        (base_addr_B),
        .rd_valid         (b_rd_valid),
        .rd_addr          (b_rd_addr),
        .rd_ready         (b_rd_ready),
        .rd_data          (b_rd_data),
        .fetch_row_valid  (b_valid),
        .fetch_row_data   (b_row),
        .fetch_done       (b_done),
        .fetch_busy       (),
        .fetch_row_ready  (b_ready),
        .fetch_row_stride (row_stride_B)
    );

    assign a_ready = (state == S_LOAD_A);
    assign b_ready = (state == S_LOAD_B);

    logic [MAX_M*MAX_K*DATA_W-1:0] a_matrix_flat;
    logic [MAX_K*MAX_N*DATA_W-1:0] b_matrix_flat;
    logic [$clog2(MAX_M+1)-1:0]    a_store_row;
    logic [$clog2(MAX_K+1)-1:0]    b_store_row;
    logic                          b_tile_cached;
    logic [ADDR_WIDTH-1:0]         b_cached_base_addr;
    logic [ADDR_WIDTH-1:0]         b_cached_row_stride;
    logic [$clog2(MAX_K+1)-1:0]    b_cached_k_num;
    logic [$clog2(MAX_N+1)-1:0]    b_cached_n_num;
    logic                          need_load_b;

    always_comb begin
        need_load_b = !allow_b_reuse
                   || !b_tile_cached
                   || (b_cached_base_addr  != base_addr_B)
                   || (b_cached_row_stride != row_stride_B)
                   || (b_cached_k_num      != mat_k_num)
                   || (b_cached_n_num      != mat_n_num);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_matrix_flat <= '0;
            b_matrix_flat <= '0;
            a_store_row   <= '0;
            b_store_row   <= '0;
            b_tile_cached <= 1'b0;
            b_cached_base_addr  <= '0;
            b_cached_row_stride <= '0;
            b_cached_k_num      <= '0;
            b_cached_n_num      <= '0;
        end else begin
            if (fifoA_start) begin
                a_matrix_flat <= '0;
                a_store_row   <= '0;
            end else if ((state == S_LOAD_A) && a_valid && a_ready) begin
                a_matrix_flat[a_store_row*MAX_K*DATA_W +: MAX_K*DATA_W] <= a_row;
                if (a_store_row < MAX_M)
                    a_store_row <= a_store_row + 1'b1;
            end

            if (fifoB_start) begin
                b_matrix_flat <= '0;
                b_store_row   <= '0;
            end else if ((state == S_LOAD_B) && b_valid && b_ready) begin
                b_matrix_flat[b_store_row*MAX_N*DATA_W +: MAX_N*DATA_W] <= b_row;
                if (b_store_row < MAX_K)
                    b_store_row <= b_store_row + 1'b1;
            end

            if ((state == S_LOAD_B) && b_done) begin
                b_tile_cached       <= 1'b1;
                b_cached_base_addr  <= base_addr_B;
                b_cached_row_stride <= row_stride_B;
                b_cached_k_num      <= mat_k_num;
                b_cached_n_num      <= mat_n_num;
            end
        end
    end

    logic ws_start, ws_busy, ws_done;
    logic [ACC_W*MAX_M*MAX_N-1:0] ws_partial_sum_flat;

    assign ws_start = (state == S_START);

    matrix_systolic_array #(
        .DATA_W     (DATA_W),
        .ACC_W      (ACC_W),
        .MAX_M      (MAX_M),
        .MAX_K      (MAX_K),
        .MAX_N      (MAX_N),
        .SMT_THREADS(SMT_THREADS)
    ) u_sys (
        .clk             (clk),
        .rst_n           (rst_n),
        .start           (ws_start),
        .mat_m_num       (mat_m_num),
        .mat_k_num       (mat_k_num),
        .mat_n_num       (mat_n_num),
        .act_matrix_flat (a_matrix_flat),
        .weight_matrix_flat(b_matrix_flat),
        .partial_sum_flat(ws_partial_sum_flat),
        .busy            (ws_busy),
        .done            (ws_done)
    );

    always_comb begin
        state_n = state;
        case (state)
            S_IDLE:    if (core_start) state_n = S_LOAD_A;
            S_LOAD_A:  if (a_done)     state_n = need_load_b ? S_LOAD_B : S_START;
            S_LOAD_B:  if (b_done)     state_n = S_START;
            S_START:                    state_n = S_COMPUTE;
            S_COMPUTE: if (ws_done)    state_n = S_IDLE;
            default:                   state_n = S_IDLE;
        endcase
    end

    assign partial_sum_flat = ws_partial_sum_flat;
    assign core_busy        = (state != S_IDLE);
    assign core_done        = (state == S_COMPUTE) && ws_done;

    always_comb begin
        a_rd_ready = 1'b0;
        b_rd_ready = 1'b0;
        a_rd_data  = '0;
        b_rd_data  = '0;

        mem_valid  = 1'b0;
        mem_addr   = 32'h0;
        mem_wdata  = 32'h0;
        mem_wstrb  = 4'b0000;

        if ((state == S_LOAD_A) && a_rd_valid) begin
            mem_valid  = 1'b1;
            mem_addr   = a_rd_addr << 2;
            a_rd_ready = mem_ready;
            a_rd_data  = mem_rdata;
        end else if ((state == S_LOAD_B) && b_rd_valid) begin
            mem_valid  = 1'b1;
            mem_addr   = b_rd_addr << 2;
            b_rd_ready = mem_ready;
            b_rd_data  = mem_rdata;
        end
    end

endmodule
