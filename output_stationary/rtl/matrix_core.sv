`timescale 1ns/1ps
module matrix_core #(
    parameter int DATA_W     = 8,
    parameter int ACC_W      = 32,
    parameter int MAX_M      = 8,
    parameter int MAX_K      = 8,
    parameter int MAX_N      = 8,
    parameter int SRAM_W     = 32,
    parameter int ADDR_WIDTH = 32,
    parameter int PE_PIPE    = 1
)(
    input  logic                    clk,
    input  logic                    rst_n,

    input  logic                        core_start,
    input  logic [$clog2(MAX_M+1)-1:0]  mat_m_num,
    input  logic [$clog2(MAX_K+1)-1:0]  mat_k_num,
    input  logic [$clog2(MAX_N+1)-1:0]  mat_n_num,

    input  logic [ADDR_WIDTH-1:0]       base_addr_A,
    input  logic [ADDR_WIDTH-1:0]       row_stride_A,

    input  logic [ADDR_WIDTH-1:0]       base_addr_B,
    input  logic [ADDR_WIDTH-1:0]       row_stride_B,

    output logic                    mem_valid,
    input  logic                    mem_ready,
    output logic [31:0]             mem_addr,    // byte address
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
        S_CLEAR   = 3'd3,
        S_COMPUTE = 3'd4;

    logic [2:0] state, state_n;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= S_IDLE;
        else        state <= state_n;
    end

    // ---------------- Fetch A ----------------
    logic a_valid, a_done, a_busy, a_ready;
    logic [MAX_K*DATA_W-1:0] a_row;

    logic a_rd_valid;
    logic [ADDR_WIDTH-1:0] a_rd_addr;
    logic a_rd_ready;
    logic [SRAM_W-1:0] a_rd_data;

    wire fifoA_start = (state == S_IDLE) && (state_n == S_LOAD_A);

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
        .fetch_row_stride (row_stride_A),

        .rd_valid         (a_rd_valid),
        .rd_addr          (a_rd_addr),
        .rd_ready         (a_rd_ready),
        .rd_data          (a_rd_data),

        .fetch_row_valid  (a_valid),
        .fetch_row_data   (a_row),
        .fetch_done       (a_done),
        .fetch_busy       (a_busy),
        .fetch_row_ready  (a_ready)
    );

    // ---------------- Fetch B ----------------
    logic b_valid, b_done, b_busy, b_ready;
    logic [MAX_N*DATA_W-1:0] b_row;

    logic b_rd_valid;
    logic [ADDR_WIDTH-1:0] b_rd_addr;
    logic b_rd_ready;
    logic [SRAM_W-1:0] b_rd_data;

    wire fifoB_start = (state == S_LOAD_A) && (state_n == S_LOAD_B);

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
        .fetch_row_stride (row_stride_B),

        .rd_valid         (b_rd_valid),
        .rd_addr          (b_rd_addr),
        .rd_ready         (b_rd_ready),
        .rd_data          (b_rd_data),

        .fetch_row_valid  (b_valid),
        .fetch_row_data   (b_row),
        .fetch_done       (b_done),
        .fetch_busy       (b_busy),
        .fetch_row_ready  (b_ready)
    );

    // ---------------- Wavefront (A left, B top) ----------------
    logic left_valid, left_done, left_start;
    logic [MAX_M*DATA_W-1:0] left_wave;

    matrix_leftright_wavefront #(
        .DATA_W (DATA_W),
        .MAX_M  (MAX_M),
        .MAX_K  (MAX_K)
    ) u_left (
        .clk                   (clk),
        .rst_n                 (rst_n),
        .mat_row_num           (mat_m_num),
        .mat_col_num           (mat_k_num),
        .preproc_load_row_valid(a_valid && (state == S_LOAD_A)),
        .preproc_load_row_data (a_row),
        .preproc_load_clear    (fifoA_start),
        .preproc_start         (left_start),
        .wavefront_valid       (left_valid),
        .wavefront_data        (left_wave),
        .preproc_done          (left_done)
    );

    logic top_valid, top_done, top_start;
    logic [MAX_N*DATA_W-1:0] top_wave;

    matrix_topdown_wavefront #(
        .DATA_W (DATA_W),
        .MAX_K  (MAX_K),
        .MAX_N  (MAX_N)
    ) u_top (
        .clk                   (clk),
        .rst_n                 (rst_n),
        .mat_k_num             (mat_k_num),
        .mat_n_num             (mat_n_num),
        .preproc_load_row_valid(b_valid && (state == S_LOAD_B)),
        .preproc_load_row_data (b_row),
        .preproc_load_clear    (fifoB_start),
        .preproc_start         (top_start),
        .wavefront_valid       (top_valid),
        .wavefront_data        (top_wave),
        .preproc_done          (top_done)
    );

    assign a_ready = (state == S_LOAD_A);
    assign b_ready = (state == S_LOAD_B);

    assign left_start = (state == S_CLEAR) && (state_n == S_COMPUTE);
    assign top_start  = (state == S_CLEAR) && (state_n == S_COMPUTE);

    // ---------------- Systolic array ----------------
    logic sys_started;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) sys_started <= 1'b0;
        else if (state != S_COMPUTE) sys_started <= 1'b0;
        else if (!sys_started && left_valid && top_valid) sys_started <= 1'b1;
    end

    wire sys_top_start  = (state == S_COMPUTE) && (!sys_started) && top_valid;
    wire sys_left_start = (state == S_COMPUTE) && (!sys_started) && left_valid;

    wire sys_top_valid  = (state == S_COMPUTE) && top_valid;
    wire sys_left_valid = (state == S_COMPUTE) && left_valid;

    logic clear_acc;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) clear_acc <= 1'b0;
        else        clear_acc <= (state == S_CLEAR);
    end

    matrix_systolic_array #(
        .DATA_W (DATA_W),
        .ACC_W  (ACC_W),
        .MAX_M  (MAX_M),
        .MAX_N  (MAX_N)
    ) u_sys (
        .clk                 (clk),
        .rst_n               (rst_n),
        .mat_m_num           (mat_m_num),
        .mat_n_num           (mat_n_num),
        .start_top_wavefront (sys_top_start),
        .start_left_wavefront(sys_left_start),
        .top_wavefront_valid (sys_top_valid),
        .left_wavefront_valid(sys_left_valid),
        .top_wavefront_vec   (top_wave),
        .left_wavefront_vec  (left_wave),
        .clear_acc           (clear_acc),
        .partial_sum_flat    (partial_sum_flat)
    );

    // ---------------- Compute done (latency register, reduced width) ----------------
    localparam int LAT_MAX = (MAX_M + MAX_N + MAX_K) + ((PE_PIPE > 0) ? PE_PIPE : 0);
    localparam int LAT_W   = (LAT_MAX <= 1) ? 1 : $clog2(LAT_MAX + 1);

    logic                 started;
    logic [LAT_W-1:0]     lat_runtime_reg;
    logic [LAT_W-1:0]     cnt;

    // latch latency when entering COMPUTE (keeps comb shallow)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lat_runtime_reg <= '0;
        end else if (left_start) begin
            if ((mat_m_num == 0) || (mat_n_num == 0) || (mat_k_num == 0)) begin
                lat_runtime_reg <= '0;
            end else begin
                // lat = M + N + K - 1 + PE_PIPE
                // widths are small; LAT_W is sized to hold max
                lat_runtime_reg <= (mat_m_num + mat_n_num + mat_k_num - 1) + PE_PIPE[LAT_W-1:0];
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            started <= 1'b0;
            cnt     <= '0;
        end else if (state != S_COMPUTE) begin
            started <= 1'b0;
            cnt     <= '0;
        end else if (!started) begin
            if (left_valid && top_valid) begin
                started <= 1'b1;
                cnt     <= '0;
            end
        end else begin
            if ((lat_runtime_reg != 0) && (cnt != (lat_runtime_reg - 1)))
                cnt <= cnt + 1'b1;
        end
    end

    wire compute_done = (lat_runtime_reg == 0) ? started
                                               : (started && (cnt == (lat_runtime_reg - 1)));

    // ---------------- Global FSM ----------------
    always_comb begin
        state_n = state;
        case (state)
            S_IDLE:    if (core_start)     state_n = S_LOAD_A;
            S_LOAD_A:  if (a_done)         state_n = S_LOAD_B;
            S_LOAD_B:  if (b_done)         state_n = S_CLEAR;
            S_CLEAR:                     state_n = S_COMPUTE;
            S_COMPUTE: if (compute_done)  state_n = S_IDLE;
            default:                      state_n = S_IDLE;
        endcase
    end

    assign core_busy = (state != S_IDLE);
    assign core_done = (state == S_COMPUTE) && (state_n == S_IDLE);

    // ---------------- Memory bus arbitration (read-only) ----------------
    always_comb begin
        a_rd_ready = 1'b0;
        b_rd_ready = 1'b0;
        a_rd_data  = '0;
        b_rd_data  = '0;

        mem_valid  = 1'b0;
        mem_addr   = 32'h0;
        mem_wdata  = 32'h0;
        mem_wstrb  = 4'b0000;

        if (state == S_LOAD_A) begin
            if (a_rd_valid) begin
                mem_valid  = 1'b1;
                mem_addr   = a_rd_addr << 2;   // word -> byte
                mem_wstrb  = 4'b0000;
                a_rd_ready = mem_ready;
                a_rd_data  = mem_rdata;
            end
        end else if (state == S_LOAD_B) begin
            if (b_rd_valid) begin
                mem_valid  = 1'b1;
                mem_addr   = b_rd_addr << 2;   // word -> byte
                mem_wstrb  = 4'b0000;
                b_rd_ready = mem_ready;
                b_rd_data  = mem_rdata;
            end
        end
    end

endmodule