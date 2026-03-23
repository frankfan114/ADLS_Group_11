`timescale 1ns/1ps
module matrix_writeback #(
    parameter int ACC_W      = 32,
    parameter int MAX_M      = 8,
    parameter int MAX_N      = 8,
    parameter int ADDR_WIDTH = 32,
    parameter int SRAM_W     = 32
)(
    input  logic clk,
    input  logic rst_n,

    input  logic                        writeback_start,
    input  logic [ADDR_WIDTH-1:0]       writeback_base_addr,      // WORD address
    input  logic [$clog2(MAX_M+1)-1:0]  writeback_mat_m_num,
    input  logic [$clog2(MAX_N+1)-1:0]  writeback_mat_n_num,

    input  logic [ACC_W*MAX_M*MAX_N-1:0] writeback_partial_sum_flat,

    output logic                     wb_valid,
    input  logic                     wb_ready,
    output logic [ADDR_WIDTH-1:0]    wb_addr,    // WORD address
    output logic [SRAM_W-1:0]        wb_wdata,
    output logic [3:0]               wb_wstrb,

    input  logic [ADDR_WIDTH-1:0]    writeback_row_stride_words,

    output logic                     writeback_busy,
    output logic                     writeback_done
);

    // ============================================================
    // FSM states
    // ============================================================
    typedef enum logic [2:0] {
        WB_IDLE = 3'd0,
        WB_SEND = 3'd1,
        WB_WAIT = 3'd2,
        WB_GAP  = 3'd3,
        WB_DONE = 3'd4
    } wb_state_e;

    wb_state_e state, state_n;

    // ============================================================
    // Counters
    // ============================================================
    logic [$clog2(MAX_M+1)-1:0] row_cnt;
    logic [$clog2(MAX_N+1)-1:0] col_cnt;
    logic [31:0]                word_idx;
    logic [31:0]                total_words;

    always_comb begin
        total_words = writeback_mat_m_num * writeback_mat_n_num;
    end

    wire wb_fire;
    wire last_word;

    assign wb_fire   = (state == WB_WAIT) && wb_ready;
    assign last_word = (total_words != 0) && (word_idx == total_words - 1);

    // ============================================================
    // Base address register
    // ============================================================
    logic [ADDR_WIDTH-1:0] base_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            base_reg <= '0;
        else if (state == WB_IDLE && writeback_start)
            base_reg <= writeback_base_addr;
    end

    // ============================================================
    // Address generation (WORD)
    // ============================================================
    assign wb_addr =
        base_reg +
        row_cnt * writeback_row_stride_words +
        col_cnt;

    // ============================================================
    // Data select from flat buffer
    // ============================================================
    logic [31:0] phys;
    always_comb begin
        phys     = row_cnt * MAX_N + col_cnt;
        wb_wdata = writeback_partial_sum_flat[phys*ACC_W +: SRAM_W];
        wb_wstrb = 4'hF;
    end

    // ============================================================
    // FSM next-state logic (IF / ELSE ONLY)
    // ============================================================
    always_comb begin
        state_n = state;

        case (state)
            WB_IDLE: begin
                if (writeback_start) begin
                    if (total_words == 0)
                        state_n = WB_DONE;
                    else
                        state_n = WB_SEND;
                end
            end

            WB_SEND: begin
                state_n = WB_WAIT;
            end

            WB_WAIT: begin
                if (wb_ready) begin
                    if (last_word)
                        state_n = WB_DONE;
                    else
                        state_n = WB_GAP;
                end
            end

            WB_GAP: begin
                state_n = WB_SEND;
            end

            WB_DONE: begin
                state_n = WB_IDLE;
            end

            default: begin
                state_n = WB_IDLE;
            end
        endcase
    end

    // ============================================================
    // Sequential: state & counters
    // ============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= WB_IDLE;
            row_cnt  <= '0;
            col_cnt  <= '0;
            word_idx <= '0;
        end else begin
            state <= state_n;

            if (state == WB_IDLE && writeback_start) begin
                row_cnt  <= '0;
                col_cnt  <= '0;
                word_idx <= '0;
            end else if (wb_fire) begin
                word_idx <= word_idx + 1'b1;

                if (!last_word) begin
                    if (col_cnt == writeback_mat_n_num - 1) begin
                        col_cnt <= '0;
                        row_cnt <= row_cnt + 1'b1;
                    end else begin
                        col_cnt <= col_cnt + 1'b1;
                    end
                end
            end
        end
    end

    // ============================================================
    // Outputs
    // ============================================================
    assign wb_valid       = (state == WB_SEND) || (state == WB_WAIT);
    assign writeback_busy = (state != WB_IDLE) && (state != WB_DONE);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            writeback_done <= 1'b0;
        else
            writeback_done <= (state == WB_DONE);
    end

endmodule