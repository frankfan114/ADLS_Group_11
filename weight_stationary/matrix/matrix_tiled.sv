`timescale 1ns/1ps
module matrix_tiled #(
    parameter int DATA_W         = 8,
    parameter int ACC_W          = 32,
    parameter int MAX_M          = 8,
    parameter int MAX_K          = 8,
    parameter int MAX_N          = 8,
    parameter int SRAM_W         = 32,
    parameter int ADDR_WIDTH     = 32,
    parameter int PE_PIPE        = 1,
    parameter int ACC_TILE_SLOTS = 256
)(
    input  logic                    clk,
    input  logic                    rst_n,

    input  logic                    start,
    input  logic [15:0]             glob_m_num,
    input  logic [15:0]             glob_k_num,
    input  logic [15:0]             glob_n_num,

    input  logic [ADDR_WIDTH-1:0]   base_addr_A,
    input  logic [ADDR_WIDTH-1:0]   base_addr_B,
    input  logic [ADDR_WIDTH-1:0]   base_addr_C,

    output logic                    mem_valid,
    input  logic                    mem_ready,
    output logic [31:0]             mem_addr,
    output logic [31:0]             mem_wdata,
    output logic [3:0]              mem_wstrb,
    input  logic [31:0]             mem_rdata,

    output logic                    busy,
    output logic                    done
);

    localparam int TILE_M = MAX_M;
    localparam int TILE_K = MAX_K;
    localparam int TILE_N = MAX_N;
    localparam int TOTAL_ELEMS_TILE = MAX_M * MAX_N;
    localparam int TILE_ACC_BITS = ACC_W * MAX_M * MAX_N;
    localparam int ELEMS_PER_WORD = SRAM_W / DATA_W;
    localparam int ELEMS_SHIFT  = $clog2(ELEMS_PER_WORD);
    localparam int TILE_M_SHIFT = $clog2(TILE_M);
    localparam int TILE_K_SHIFT = $clog2(TILE_K);
    localparam int TILE_N_SHIFT = $clog2(TILE_N);

    logic [ADDR_WIDTH-1:0] row_stride_A_words;
    logic [ADDR_WIDTH-1:0] row_stride_B_words;
    logic [ADDR_WIDTH-1:0] row_stride_C_words;

    always_comb begin
        row_stride_A_words = (glob_k_num + (ELEMS_PER_WORD-1)) >> ELEMS_SHIFT;
        row_stride_B_words = (glob_n_num + (ELEMS_PER_WORD-1)) >> ELEMS_SHIFT;
        row_stride_C_words = glob_n_num;
    end

    logic [15:0] num_tile_m, num_tile_n, num_tile_k;
    always_comb begin
        num_tile_m = (glob_m_num == 0) ? 16'd0 : ((glob_m_num + (TILE_M-1)) >> TILE_M_SHIFT);
        num_tile_n = (glob_n_num == 0) ? 16'd0 : ((glob_n_num + (TILE_N-1)) >> TILE_N_SHIFT);
        num_tile_k = (glob_k_num == 0) ? 16'd0 : ((glob_k_num + (TILE_K-1)) >> TILE_K_SHIFT);
    end

    logic [15:0] tile_m_idx, tile_n_idx, tile_k_idx;
    logic [15:0] tile_m_idx_n, tile_n_idx_n, tile_k_idx_n;
    logic [15:0] wb_tile_m_idx, wb_tile_m_idx_n;

    logic [$clog2(MAX_M+1)-1:0] cur_m_num;
    logic [$clog2(MAX_K+1)-1:0] cur_k_num;
    logic [$clog2(MAX_N+1)-1:0] cur_n_num;
    logic [$clog2(MAX_M+1)-1:0] wb_cur_m_num;

    always_comb begin
        if (num_tile_m == 0)
            cur_m_num = '0;
        else
            cur_m_num = (tile_m_idx == num_tile_m - 1) ? (glob_m_num - tile_m_idx * TILE_M) : TILE_M;

        if (num_tile_n == 0)
            cur_n_num = '0;
        else
            cur_n_num = (tile_n_idx == num_tile_n - 1) ? (glob_n_num - tile_n_idx * TILE_N) : TILE_N;

        if (num_tile_k == 0)
            cur_k_num = '0;
        else
            cur_k_num = (tile_k_idx == num_tile_k - 1) ? (glob_k_num - tile_k_idx * TILE_K) : TILE_K;

        if (num_tile_m == 0)
            wb_cur_m_num = '0;
        else
            wb_cur_m_num = (wb_tile_m_idx == num_tile_m - 1) ? (glob_m_num - wb_tile_m_idx * TILE_M) : TILE_M;
    end

    typedef enum logic [2:0] {
        TS_IDLE       = 3'd0,
        TS_INIT_TILE  = 3'd1,
        TS_START_CORE = 3'd2,
        TS_WAIT_CORE  = 3'd3,
        TS_ACCUM      = 3'd4,
        TS_WB_START   = 3'd5,
        TS_WB_WAIT    = 3'd6,
        TS_DONE       = 3'd7
    } t_state_e;

    t_state_e t_state, t_state_n;

    logic [ADDR_WIDTH-1:0] base_addr_A_tile_r;
    logic [ADDR_WIDTH-1:0] base_addr_B_tile_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            base_addr_A_tile_r <= '0;
            base_addr_B_tile_r <= '0;
        end else if (t_state == TS_INIT_TILE) begin
            base_addr_A_tile_r <= base_addr_A
                               + (tile_m_idx * TILE_M) * row_stride_A_words
                               + ((tile_k_idx * TILE_K) >> ELEMS_SHIFT);

            base_addr_B_tile_r <= base_addr_B
                               + (tile_k_idx * TILE_K) * row_stride_B_words
                               + ((tile_n_idx * TILE_N) >> ELEMS_SHIFT);
        end
    end

    logic core_start, core_busy, core_done;
    logic core_allow_b_reuse;
    logic core_mem_valid;
    logic [31:0] core_mem_addr;
    logic [31:0] core_mem_wdata;
    logic [3:0]  core_mem_wstrb;
    logic [TILE_ACC_BITS-1:0] core_partial_flat;
    logic [TILE_ACC_BITS-1:0] core_partial_flat_r;

    matrix_core #(
        .DATA_W     (DATA_W),
        .ACC_W      (ACC_W),
        .MAX_M      (MAX_M),
        .MAX_K      (MAX_K),
        .MAX_N      (MAX_N),
        .SRAM_W     (SRAM_W),
        .ADDR_WIDTH (ADDR_WIDTH),
        .PE_PIPE    (PE_PIPE)
    ) u_core (
        .clk          (clk),
        .rst_n        (rst_n),

        .core_start   (core_start),
        .allow_b_reuse(core_allow_b_reuse),
        .mat_m_num    (cur_m_num),
        .mat_k_num    (cur_k_num),
        .mat_n_num    (cur_n_num),

        .base_addr_A  (base_addr_A_tile_r),
        .row_stride_A (row_stride_A_words),
        .base_addr_B  (base_addr_B_tile_r),
        .row_stride_B (row_stride_B_words),

        .mem_valid    (core_mem_valid),
        .mem_ready    (mem_ready),
        .mem_addr     (core_mem_addr),
        .mem_wdata    (core_mem_wdata),
        .mem_wstrb    (core_mem_wstrb),
        .mem_rdata    (mem_rdata),

        .partial_sum_flat(core_partial_flat),

        .core_busy    (core_busy),
        .core_done    (core_done)
    );

    // In system-level WS mode, one B tile is reused across all M tiles for a fixed (K, N) pair.
    assign core_allow_b_reuse = (tile_m_idx != 16'd0);

    logic [TILE_ACC_BITS-1:0] c_tile_spad [0:ACC_TILE_SLOTS-1];
    logic [TILE_ACC_BITS-1:0] wb_partial_flat;
    integer ii;

    wire last_tm = (num_tile_m != 0) && (tile_m_idx == (num_tile_m - 1));
    wire last_tk = (num_tile_k != 0) && (tile_k_idx == (num_tile_k - 1));
    wire last_tn = (num_tile_n != 0) && (tile_n_idx == (num_tile_n - 1));
    wire last_wb_tm = (num_tile_m != 0) && (wb_tile_m_idx == (num_tile_m - 1));
    wire first_tk = (tile_k_idx == 16'd0);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            core_partial_flat_r <= '0;
        end else if ((t_state == TS_WAIT_CORE) && core_done) begin
            core_partial_flat_r <= core_partial_flat;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (ii = 0; ii < ACC_TILE_SLOTS; ii++) begin
                c_tile_spad[ii] <= '0;
            end
        end else if (t_state == TS_ACCUM) begin
            if (first_tk) begin
                c_tile_spad[tile_m_idx] <= core_partial_flat_r;
            end else begin
                for (ii = 0; ii < TOTAL_ELEMS_TILE; ii++) begin
                    c_tile_spad[tile_m_idx][ii*ACC_W +: ACC_W] <=
                        c_tile_spad[tile_m_idx][ii*ACC_W +: ACC_W] + core_partial_flat_r[ii*ACC_W +: ACC_W];
                end
            end
        end
    end

    always_comb begin
        wb_partial_flat = c_tile_spad[wb_tile_m_idx];
    end

    logic wb_start;
    logic wb_valid, wb_ready;
    logic [ADDR_WIDTH-1:0] wb_addr_word;
    logic [SRAM_W-1:0]     wb_wdata;
    logic [3:0]            wb_wstrb;
    logic wb_busy, wb_done;
    logic [ADDR_WIDTH-1:0] wb_base_addr_word;

    always_comb begin
        wb_base_addr_word = base_addr_C
                          + (wb_tile_m_idx * TILE_M) * glob_n_num
                          + (tile_n_idx * TILE_N);
    end

    matrix_writeback #(
        .ACC_W      (ACC_W),
        .MAX_M      (MAX_M),
        .MAX_N      (MAX_N),
        .ADDR_WIDTH (ADDR_WIDTH),
        .SRAM_W     (SRAM_W)
    ) u_wb (
        .clk                      (clk),
        .rst_n                    (rst_n),

        .writeback_start          (wb_start),
        .writeback_base_addr      (wb_base_addr_word),
        .writeback_mat_m_num      (wb_cur_m_num),
        .writeback_mat_n_num      (cur_n_num),

        .writeback_partial_sum_flat(wb_partial_flat),

        .wb_valid                 (wb_valid),
        .wb_ready                 (wb_ready),
        .wb_addr                  (wb_addr_word),
        .wb_wdata                 (wb_wdata),
        .wb_wstrb                 (wb_wstrb),

        .writeback_row_stride_words(row_stride_C_words),

        .writeback_busy           (wb_busy),
        .writeback_done           (wb_done)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t_state <= TS_IDLE;
        end else begin
            t_state <= t_state_n;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tile_m_idx    <= 16'd0;
            tile_n_idx    <= 16'd0;
            tile_k_idx    <= 16'd0;
            wb_tile_m_idx <= 16'd0;
        end else begin
            tile_m_idx    <= tile_m_idx_n;
            tile_n_idx    <= tile_n_idx_n;
            tile_k_idx    <= tile_k_idx_n;
            wb_tile_m_idx <= wb_tile_m_idx_n;
        end
    end

    always_comb begin
        tile_m_idx_n    = tile_m_idx;
        tile_n_idx_n    = tile_n_idx;
        tile_k_idx_n    = tile_k_idx;
        wb_tile_m_idx_n = wb_tile_m_idx;

        case (t_state)
            TS_IDLE: if (start) begin
                tile_m_idx_n    = 16'd0;
                tile_n_idx_n    = 16'd0;
                tile_k_idx_n    = 16'd0;
                wb_tile_m_idx_n = 16'd0;
            end

            TS_ACCUM: begin
                if (!last_tm) begin
                    tile_m_idx_n = tile_m_idx + 16'd1;
                end else if (!last_tk) begin
                    tile_m_idx_n = 16'd0;
                    tile_k_idx_n = tile_k_idx + 16'd1;
                end else begin
                    tile_m_idx_n    = 16'd0;
                    tile_k_idx_n    = 16'd0;
                    wb_tile_m_idx_n = 16'd0;
                end
            end

            TS_WB_WAIT: if (wb_done) begin
                if (!last_wb_tm) begin
                    wb_tile_m_idx_n = wb_tile_m_idx + 16'd1;
                end else if (!last_tn) begin
                    tile_n_idx_n    = tile_n_idx + 16'd1;
                    tile_m_idx_n    = 16'd0;
                    tile_k_idx_n    = 16'd0;
                    wb_tile_m_idx_n = 16'd0;
                end
            end

            default: ;
        endcase
    end

    always_comb begin
        t_state_n  = t_state;
        core_start = 1'b0;
        wb_start   = 1'b0;

        case (t_state)
            TS_IDLE: begin
                if (start) begin
                    if ((glob_m_num == 0) || (glob_k_num == 0) || (glob_n_num == 0))
                        t_state_n = TS_DONE;
                    else
                        t_state_n = TS_INIT_TILE;
                end
            end

            TS_INIT_TILE: begin
                t_state_n = TS_START_CORE;
            end

            TS_START_CORE: begin
                core_start = 1'b1;
                t_state_n  = TS_WAIT_CORE;
            end

            TS_WAIT_CORE: begin
                if (core_done)
                    t_state_n = TS_ACCUM;
            end

            TS_ACCUM: begin
                if (last_tm && last_tk)
                    t_state_n = TS_WB_START;
                else
                    t_state_n = TS_INIT_TILE;
            end

            TS_WB_START: begin
                wb_start  = 1'b1;
                t_state_n = TS_WB_WAIT;
            end

            TS_WB_WAIT: begin
                if (wb_done) begin
                    if (last_wb_tm) begin
                        if (last_tn)
                            t_state_n = TS_DONE;
                        else
                            t_state_n = TS_INIT_TILE;
                    end else begin
                        t_state_n = TS_WB_START;
                    end
                end
            end

            TS_DONE: begin
                t_state_n = TS_IDLE;
            end

            default: begin
                t_state_n = TS_IDLE;
            end
        endcase
    end

    assign busy = (t_state != TS_IDLE) && (t_state != TS_DONE);
    assign done = (t_state == TS_DONE);

    always_comb begin
        mem_valid = 1'b0;
        mem_addr  = 32'h0;
        mem_wdata = 32'h0;
        mem_wstrb = 4'b0000;
        wb_ready  = 1'b0;

        if ((t_state == TS_INIT_TILE) ||
            (t_state == TS_START_CORE) ||
            (t_state == TS_WAIT_CORE)  ||
            (t_state == TS_ACCUM)) begin
            mem_valid = core_mem_valid;
            mem_addr  = core_mem_addr;
            mem_wdata = 32'h0;
            mem_wstrb = 4'b0000;
        end else if ((t_state == TS_WB_START) ||
                     (t_state == TS_WB_WAIT)) begin
            mem_valid = wb_valid;
            mem_addr  = wb_addr_word << 2;
            mem_wdata = wb_wdata;
            mem_wstrb = wb_wstrb;
            wb_ready  = mem_ready;
        end
    end

endmodule
