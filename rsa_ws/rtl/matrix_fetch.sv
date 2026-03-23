`timescale 1ns/1ps
module matrix_fetch #(
    parameter int DATA_WIDTH   = 8,
    parameter int SRAM_WIDTH   = 32,
    parameter int MAX_COL_NUM  = 8,
    parameter int MAX_ROW_NUM  = 8,
    parameter int ADDR_WIDTH   = 32
)(
    input  logic clk,
    input  logic rst_n,

    // ------------------------------------------------------------
    // Control
    // ------------------------------------------------------------
    input  logic start,
    input  logic [$clog2(MAX_COL_NUM+1)-1:0] col_num,
    input  logic [$clog2(MAX_ROW_NUM+1)-1:0] row_num,
    input  logic [ADDR_WIDTH-1:0]            base_addr,
    input  logic [$clog2(SRAM_WIDTH / DATA_WIDTH)-1:0] fetch_col_offset,

    // ------------------------------------------------------------
    // SRAM-like read interface
    // ------------------------------------------------------------
    output logic                  rd_valid,
    output logic [ADDR_WIDTH-1:0] rd_addr,
    input  logic                  rd_ready,
    input  logic [SRAM_WIDTH-1:0] rd_data,

    // ------------------------------------------------------------
    // Row-level interface
    // ------------------------------------------------------------
    output logic                          fetch_row_valid,
    output logic [MAX_COL_NUM*DATA_WIDTH-1:0] fetch_row_data,
    output logic                          fetch_done,
    output logic                          fetch_busy,
    input  logic                          fetch_row_ready,
    input  logic [ADDR_WIDTH-1:0]         fetch_row_stride
);

    // ============================================================
    // Derived parameters
    // ============================================================
    localparam int ELEMS_PER_SRAM    = SRAM_WIDTH / DATA_WIDTH;
    localparam int ELEMS_SHIFT       = $clog2(ELEMS_PER_SRAM);
    localparam int MAX_WORDS_PER_ROW = ((MAX_COL_NUM + ELEMS_PER_SRAM - 1) / ELEMS_PER_SRAM) + 1;
    localparam int BUFFER_BITS       = MAX_COL_NUM * DATA_WIDTH;

    logic [$clog2(MAX_WORDS_PER_ROW+1)-1:0] words_per_row;
    logic [$clog2(MAX_COL_NUM + ELEMS_PER_SRAM + 1)-1:0] total_fetch_elems;
    always_comb begin
        total_fetch_elems = col_num + fetch_col_offset;
        words_per_row = (total_fetch_elems + (ELEMS_PER_SRAM-1)) >> ELEMS_SHIFT;
    end

    // ============================================================
    // FSM
    // ============================================================
    typedef enum logic [2:0] {
        S_IDLE,
        S_REQ,
        S_WAIT,
        S_GAP,
        S_ROW_OUT,
        S_DONE
    } state_t;

    state_t state, state_n;

    // ============================================================
    // Datapath
    // ============================================================
    logic [ADDR_WIDTH-1:0]                  ptr;
    logic [$clog2(MAX_ROW_NUM+1)-1:0]       row_idx;
    logic [$clog2(MAX_WORDS_PER_ROW+1)-1:0] word_idx;
    logic [BUFFER_BITS-1:0]                 buffer;

    wire last_row = (row_num != 0) && (row_idx == row_num-1);
    wire row_full = (word_idx == words_per_row);

    // ============================================================
    // FSM sequential
    // ============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_IDLE;
        else
            state <= state_n;
    end

    // ============================================================
    // FSM combinational
    // ============================================================
    always_comb begin
        state_n = state;
        case (state)
            S_IDLE:
                if (start) state_n = S_REQ;

            S_REQ:
                if (row_idx >= row_num) state_n = S_DONE;
                else if (row_full)      state_n = S_ROW_OUT;
                else                    state_n = S_WAIT;

            S_WAIT:
                if (rd_ready)           state_n = S_GAP;

            S_GAP:
                state_n = S_REQ;

            S_ROW_OUT:
                if (fetch_row_ready) begin
                    if (last_row) state_n = S_DONE;
                    else          state_n = S_REQ;
                end

            S_DONE:
                if (start) state_n = S_REQ;

            default:
                state_n = S_IDLE;
        endcase
    end

    // ============================================================
    // rd channel (strict)
    // ============================================================
    assign rd_valid = (state == S_WAIT);
    assign rd_addr  = ptr;

    // ============================================================
    // Data packing
    // ============================================================
    integer b;
    integer global_elem;
    integer logical_elem;
    logic [$clog2(MAX_COL_NUM + ELEMS_PER_SRAM + 1)-1:0] elem_base;

    always_comb begin
        elem_base = (word_idx << ELEMS_SHIFT);
    end

    // ============================================================
    // Datapath update
    // ============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ptr      <= '0;
            row_idx  <= '0;
            word_idx <= '0;
            buffer   <= '0;
        end else begin
            case (state)

                S_IDLE: begin
                    if (start) begin
                        ptr      <= base_addr;
                        row_idx  <= '0;
                        word_idx <= '0;
                        buffer   <= '0;
                    end
                end

                S_WAIT: begin
                    if (rd_ready) begin
                        for (b = 0; b < ELEMS_PER_SRAM; b++) begin
                            global_elem = elem_base + b;
                            logical_elem = global_elem - fetch_col_offset;
                            if ((global_elem >= fetch_col_offset) &&
                                (logical_elem >= 0) &&
                                (logical_elem < col_num)) begin
                                buffer[(logical_elem*DATA_WIDTH) +: DATA_WIDTH]
                                    <= rd_data[(b*DATA_WIDTH) +: DATA_WIDTH];
                            end
                        end
                        word_idx <= word_idx + 1'b1;
                        ptr      <= ptr + 1'b1;
                    end
                end

                S_ROW_OUT: begin
                    if (fetch_row_ready) begin
                        if (!last_row) begin
                            row_idx  <= row_idx + 1'b1;
                            word_idx <= '0;
                            buffer   <= '0;
                            ptr      <= ptr + (fetch_row_stride - words_per_row);
                        end
                    end
                end

                S_DONE: begin
                    if (start) begin
                        ptr      <= base_addr;
                        row_idx  <= '0;
                        word_idx <= '0;
                        buffer   <= '0;
                    end
                end

                default: ;
            endcase
        end
    end

    // ============================================================
    // Outputs
    // ============================================================
    assign fetch_row_valid = (state == S_ROW_OUT);
    assign fetch_row_data  = buffer;
    assign fetch_done      = (state == S_DONE);
    assign fetch_busy      = (state != S_IDLE) && (state != S_DONE);

endmodule
