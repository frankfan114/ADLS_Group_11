`timescale 1ns/1ps
module matrix_tiled #(
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

    input  logic                    start,
    input  logic [15:0]             glob_m_num,
    input  logic [15:0]             glob_k_num,
    input  logic [15:0]             glob_n_num,

    input  logic [ADDR_WIDTH-1:0]   base_addr_A,
    input  logic [ADDR_WIDTH-1:0]   base_addr_B,
    input  logic [ADDR_WIDTH-1:0]   base_addr_C,

    // Read channel (core fetch)
    output logic                    rd_mem_valid,
    input  logic                    rd_mem_ready,
    output logic [31:0]             rd_mem_addr,
    input  logic [31:0]             rd_mem_rdata,

    // Write channel (writeback)
    output logic                    wr_mem_valid,
    input  logic                    wr_mem_ready,
    output logic [31:0]             wr_mem_addr,
    output logic [31:0]             wr_mem_wdata,
    output logic [3:0]              wr_mem_wstrb,

    output logic                    busy,
    output logic                    done
);

    localparam int TILE_M = MAX_M;
    localparam int TILE_K = MAX_K;
    localparam int TILE_N = MAX_N;
    localparam int TOTAL_ELEMS_TILE = MAX_M * MAX_N;

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

    logic [$clog2(MAX_M+1)-1:0] cur_m_num;
    logic [$clog2(MAX_K+1)-1:0] cur_k_num;
    logic [$clog2(MAX_N+1)-1:0] cur_n_num;

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
    end

    typedef enum logic [2:0] {
        CS_IDLE       = 3'd0,
        CS_INIT_TILE  = 3'd1,
        CS_START_CORE = 3'd2,
        CS_WAIT_CORE  = 3'd3,
        CS_ACCUM      = 3'd4,
        CS_COMMIT     = 3'd5
    } c_state_e;

    c_state_e c_state, c_state_n;

    logic [ADDR_WIDTH-1:0] base_addr_A_tile_r;
    logic [ADDR_WIDTH-1:0] base_addr_B_tile_r;
    logic [ADDR_WIDTH-1:0] base_addr_C_tile_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            base_addr_A_tile_r <= '0;
            base_addr_B_tile_r <= '0;
            base_addr_C_tile_r <= '0;
        end else if (c_state == CS_INIT_TILE) begin
            base_addr_A_tile_r <= base_addr_A
                               + (tile_m_idx * TILE_M) * row_stride_A_words
                               + ((tile_k_idx * TILE_K) >> ELEMS_SHIFT);

            base_addr_B_tile_r <= base_addr_B
                               + (tile_k_idx * TILE_K) * row_stride_B_words
                               + ((tile_n_idx * TILE_N) >> ELEMS_SHIFT);

            base_addr_C_tile_r <= base_addr_C
                               + (tile_m_idx * TILE_M) * glob_n_num
                               + (tile_n_idx * TILE_N);
        end
    end

    logic core_start, core_busy, core_done;
    logic core_allow_b_reuse;
    logic core_mem_valid;
    logic core_mem_ready;
    logic [31:0] core_mem_addr;
    logic [31:0] core_mem_wdata;
    logic [3:0]  core_mem_wstrb;
    logic [ACC_W*MAX_M*MAX_N-1:0] core_partial_flat;

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
        .mem_ready    (core_mem_ready),
        .mem_addr     (core_mem_addr),
        .mem_wdata    (core_mem_wdata),
        .mem_wstrb    (core_mem_wstrb),
        .mem_rdata    (rd_mem_rdata),

        .partial_sum_flat(core_partial_flat),

        .core_busy    (core_busy),
        .core_done    (core_done)
    );

    // Keep reuse disabled for pure PP-vs-NOPP comparison.
    assign core_allow_b_reuse = 1'b0;

    logic [ACC_W*MAX_M*MAX_N-1:0] c_accum_ping;
    logic [ACC_W*MAX_M*MAX_N-1:0] c_accum_pong;
    logic                          active_bank;
    integer ii;

    logic [ACC_W*MAX_M*MAX_N-1:0] core_partial_flat_r;
    logic                         k_last_done_r;
    logic                         last_tk_curr;
    logic                         last_tm, last_tn, last_tile_mn;
    logic                         wb_slot_free;
    logic                         commit_fire;
    logic                         run_active;
    logic                         compute_all_done;
    logic                         done_pulse_r;

    always_comb begin
        last_tk_curr  = (num_tile_k != 0) && (tile_k_idx == (num_tile_k - 1));
        last_tm       = (num_tile_m != 0) && (tile_m_idx == (num_tile_m - 1));
        last_tn       = (num_tile_n != 0) && (tile_n_idx == (num_tile_n - 1));
        last_tile_mn  = last_tm && last_tn;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            core_partial_flat_r <= '0;
            k_last_done_r       <= 1'b0;
        end else if ((c_state == CS_WAIT_CORE) && core_done) begin
            core_partial_flat_r <= core_partial_flat;
            k_last_done_r       <= last_tk_curr;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            c_accum_ping <= '0;
            c_accum_pong <= '0;
            active_bank  <= 1'b0;
        end else begin
            if ((c_state == CS_IDLE) && start) begin
                c_accum_ping <= '0;
                c_accum_pong <= '0;
                active_bank  <= 1'b0;
            end else begin
                if ((c_state == CS_INIT_TILE) && (tile_k_idx == 16'd0)) begin
                    if (!active_bank)
                        c_accum_ping <= '0;
                    else
                        c_accum_pong <= '0;
                end

                if (c_state == CS_ACCUM) begin
                    if (!active_bank) begin
                        for (ii = 0; ii < TOTAL_ELEMS_TILE; ii = ii + 1) begin
                            c_accum_ping[ii*ACC_W +: ACC_W] <=
                                c_accum_ping[ii*ACC_W +: ACC_W] + core_partial_flat_r[ii*ACC_W +: ACC_W];
                        end
                    end else begin
                        for (ii = 0; ii < TOTAL_ELEMS_TILE; ii = ii + 1) begin
                            c_accum_pong[ii*ACC_W +: ACC_W] <=
                                c_accum_pong[ii*ACC_W +: ACC_W] + core_partial_flat_r[ii*ACC_W +: ACC_W];
                        end
                    end
                end

                if (commit_fire && !last_tile_mn) begin
                    active_bank <= ~active_bank;
                end
            end
        end
    end

    logic wb_start;
    logic wb_valid, wb_ready;
    logic [ADDR_WIDTH-1:0] wb_addr_word;
    logic [SRAM_W-1:0]     wb_wdata;
    logic [3:0]            wb_wstrb;
    logic wb_busy, wb_done;
    logic wb_job_valid;
    logic wb_bank;
    logic [ADDR_WIDTH-1:0] wb_base_addr_r;
    logic [$clog2(MAX_M+1)-1:0] wb_m_num_r;
    logic [$clog2(MAX_N+1)-1:0] wb_n_num_r;
    logic [ACC_W*MAX_M*MAX_N-1:0] wb_partial_flat;

    assign wb_partial_flat = wb_bank ? c_accum_pong : c_accum_ping;
    assign wb_slot_free    = !wb_job_valid && !wb_busy;
    assign commit_fire     = (c_state == CS_COMMIT) && wb_slot_free;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wb_start       <= 1'b0;
            wb_job_valid   <= 1'b0;
            wb_bank        <= 1'b0;
            wb_base_addr_r <= '0;
            wb_m_num_r     <= '0;
            wb_n_num_r     <= '0;
        end else begin
            wb_start <= 1'b0;

            if (commit_fire) begin
                wb_job_valid   <= 1'b1;
                wb_bank        <= active_bank;
                wb_base_addr_r <= base_addr_C_tile_r;
                wb_m_num_r     <= cur_m_num;
                wb_n_num_r     <= cur_n_num;
                wb_start       <= 1'b1;
            end

            if (wb_done) begin
                wb_job_valid <= 1'b0;
            end
        end
    end

    matrix_writeback_pp #(
        .ACC_W      (ACC_W),
        .MAX_M      (MAX_M),
        .MAX_N      (MAX_N),
        .ADDR_WIDTH (ADDR_WIDTH),
        .SRAM_W     (SRAM_W),
        .SKIP_ZERO_WRITES(1'b0)
    ) u_wb (
        .clk                      (clk),
        .rst_n                    (rst_n),

        .writeback_start          (wb_start),
        .writeback_base_addr      (wb_base_addr_r),
        .writeback_mat_m_num      (wb_m_num_r),
        .writeback_mat_n_num      (wb_n_num_r),

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
        if (!rst_n)
            c_state <= CS_IDLE;
        else
            c_state <= c_state_n;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tile_m_idx <= 16'd0;
            tile_n_idx <= 16'd0;
            tile_k_idx <= 16'd0;
        end else begin
            tile_m_idx <= tile_m_idx_n;
            tile_n_idx <= tile_n_idx_n;
            tile_k_idx <= tile_k_idx_n;
        end
    end

    always_comb begin
        tile_m_idx_n = tile_m_idx;
        tile_n_idx_n = tile_n_idx;
        tile_k_idx_n = tile_k_idx;

        case (c_state)
            CS_IDLE: begin
                if (start) begin
                    tile_m_idx_n = 16'd0;
                    tile_n_idx_n = 16'd0;
                    tile_k_idx_n = 16'd0;
                end
            end

            CS_WAIT_CORE: begin
                if (core_done) begin
                    if (!last_tk_curr)
                        tile_k_idx_n = tile_k_idx + 16'd1;
                end
            end

            CS_COMMIT: begin
                if (commit_fire) begin
                    tile_k_idx_n = 16'd0;
                    if (!last_tile_mn) begin
                        if (last_tn) begin
                            tile_n_idx_n = 16'd0;
                            tile_m_idx_n = tile_m_idx + 16'd1;
                        end else begin
                            tile_n_idx_n = tile_n_idx + 16'd1;
                        end
                    end
                end
            end

            default: begin
            end
        endcase
    end

    always_comb begin
        c_state_n  = c_state;
        core_start = 1'b0;

        case (c_state)
            CS_IDLE: begin
                if (start) begin
                    if ((glob_m_num == 0) || (glob_k_num == 0) || (glob_n_num == 0))
                        c_state_n = CS_IDLE;
                    else
                        c_state_n = CS_INIT_TILE;
                end
            end

            CS_INIT_TILE: begin
                c_state_n = CS_START_CORE;
            end

            CS_START_CORE: begin
                core_start = 1'b1;
                c_state_n  = CS_WAIT_CORE;
            end

            CS_WAIT_CORE: begin
                if (core_done)
                    c_state_n = CS_ACCUM;
            end

            CS_ACCUM: begin
                if (!k_last_done_r)
                    c_state_n = CS_INIT_TILE;
                else
                    c_state_n = CS_COMMIT;
            end

            CS_COMMIT: begin
                if (commit_fire) begin
                    if (last_tile_mn)
                        c_state_n = CS_IDLE;
                    else
                        c_state_n = CS_INIT_TILE;
                end
            end

            default: begin
                c_state_n = CS_IDLE;
            end
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            run_active       <= 1'b0;
            compute_all_done <= 1'b0;
            done_pulse_r     <= 1'b0;
        end else begin
            done_pulse_r <= 1'b0;

            if ((c_state == CS_IDLE) && start) begin
                run_active       <= 1'b1;
                compute_all_done <= ((glob_m_num == 0) || (glob_k_num == 0) || (glob_n_num == 0));
            end

            if (commit_fire && last_tile_mn) begin
                compute_all_done <= 1'b1;
            end

            if (run_active && compute_all_done && !wb_job_valid && !wb_busy) begin
                done_pulse_r     <= 1'b1;
                run_active       <= 1'b0;
                compute_all_done <= 1'b0;
            end
        end
    end

    // Split memory channels: read path for core, write path for writeback.
    always_comb begin
        rd_mem_valid  = core_mem_valid;
        rd_mem_addr   = core_mem_addr;
        core_mem_ready = rd_mem_ready;

        wr_mem_valid  = wb_valid;
        wr_mem_addr   = wb_addr_word << 2;
        wr_mem_wdata  = wb_wdata;
        wr_mem_wstrb  = wb_wstrb;
        wb_ready      = wr_mem_ready;
    end

`ifndef SYNTHESIS
    logic pp_log_en;
    initial begin
        pp_log_en = $test$plusargs("PP_LOG");
        $display("[%0t] [PP_TAG] using pp/matrix/matrix_tiled.sv", $time);
    end

    always_ff @(posedge clk) begin
        if (pp_log_en && start) begin
            $display("[%0t] [PP_TAG] start m=%0d k=%0d n=%0d",
                     $time, glob_m_num, glob_k_num, glob_n_num);
        end
        if (pp_log_en && commit_fire) begin
            $display("[%0t] [PP_TAG] commit tm=%0d tn=%0d tk=%0d bank=%0d",
                     $time, tile_m_idx, tile_n_idx, tile_k_idx, active_bank);
        end
        if (pp_log_en && done_pulse_r) begin
            $display("[%0t] [PP_TAG] done", $time);
        end
    end
`endif

    // Legacy compatibility for existing TB hierarchy probes.
    logic [2:0] t_state;
    always_comb begin
        t_state = 3'd0;
        if (wb_start) begin
            t_state = 3'd5;
        end else if (wb_job_valid || wb_busy || wb_valid) begin
            t_state = 3'd6;
        end else begin
            case (c_state)
                CS_IDLE:       t_state = 3'd0;
                CS_INIT_TILE:  t_state = 3'd1;
                CS_START_CORE: t_state = 3'd2;
                CS_WAIT_CORE:  t_state = 3'd3;
                CS_ACCUM:      t_state = 3'd4;
                CS_COMMIT:     t_state = 3'd5;
                default:       t_state = 3'd0;
            endcase
        end
    end

    assign busy = run_active || (c_state != CS_IDLE) || wb_job_valid || wb_busy;
    assign done = done_pulse_r;

endmodule
