`timescale 1ns/1ps
module matrix_leftright_wavefront  #(
    parameter int DATA_W  = 8,

    // hardware capability (compile-time)
    parameter int MAX_M   = 8,   // max rows of A
    parameter int MAX_K   = 8    // max cols of A
)(
    input  logic clk,
    input  logic rst_n,

    // ============================================================
    // Runtime matrix geometry
    // ============================================================
    input  logic [$clog2(MAX_M+1)-1:0] mat_row_num,  // actual M
    input  logic [$clog2(MAX_K+1)-1:0] mat_col_num,  // actual K

    // ============================================================
    // Load interface (row-major input, from input_fifo)
    // ============================================================
    input  logic                    preproc_load_row_valid,
    input  logic [MAX_K*DATA_W-1:0] preproc_load_row_data,
    input  logic                    preproc_load_clear,

    // ============================================================
    // Control
    // ============================================================
    input  logic preproc_start,   // start wavefront scan

    // ============================================================
    // Wavefront output (to systolic array)
    // ============================================================
    output logic                    wavefront_valid,
    output logic [MAX_M*DATA_W-1:0] wavefront_data,
    output logic                    preproc_done
);

    // ============================================================
    // Internal storage: row-major A (MAX_M x MAX_K)
    // ============================================================
    localparam int MEM_SIZE = MAX_M * MAX_K;
    logic [DATA_W-1:0] mem [0:MEM_SIZE-1];

    // ============================================================
    // Load control
    // ============================================================
    logic [$clog2(MAX_M+1)-1:0] wr_row;
    wire load_done = (wr_row == mat_row_num);

    integer i, c;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_row <= '0;
            for (i = 0; i < MEM_SIZE; i = i + 1)
                mem[i] <= '0;
        end else begin
            if (preproc_load_clear) begin
                wr_row <= '0;
            end else if (preproc_load_row_valid && !load_done) begin
                // write one full row (row-major)
                for (c = 0; c < MAX_K; c = c + 1) begin
                    if (c < mat_col_num)
                        mem[wr_row*MAX_K + c] <= preproc_load_row_data[c*DATA_W +: DATA_W];
                    else
                        mem[wr_row*MAX_K + c] <= '0;
                end
                wr_row <= wr_row + 1'b1;
            end
        end
    end

    // ============================================================
    // Wavefront FSM
    // ============================================================
    typedef enum logic [1:0] { S_IDLE, S_RUN, S_DONE } state_t;
    state_t state, state_n;

    localparam int T_W = (MAX_M + MAX_K <= 1) ? 1 : $clog2(MAX_M + MAX_K);
    logic [T_W-1:0] t, t_n;
    logic [T_W-1:0] t_max;

    // Guard t_max against underflow when mat_row_num/mat_col_num are 0
    always_comb begin
        if ((mat_row_num == 0) || (mat_col_num == 0)) begin
            t_max = '0;
        end else begin
            // (M + K - 2), safe because M,K >= 1 here
            t_max = (mat_row_num + mat_col_num - 2);
        end
    end

    // state register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            t     <= '0;
        end else begin
            state <= state_n;
            t     <= t_n;
        end
    end

    // next-state logic
    always_comb begin
        state_n = state;
        t_n     = t;

        case (state)
            S_IDLE: begin
                // If no work (M==0 or K==0), don't enter RUN; treat as immediate done.
                if (preproc_start && load_done) begin
                    if ((mat_row_num == 0) || (mat_col_num == 0)) begin
                        state_n = S_DONE;
                        t_n     = '0;
                    end else begin
                    state_n = S_RUN;
                    t_n     = '0;
                    end
                end
            end

            S_RUN: begin
                if (t == t_max) begin
                    state_n = S_DONE;
                end else begin
                    t_n = t + 1'b1;
                end
            end

            S_DONE: begin
                state_n = S_IDLE;
            end

            default: begin
                state_n = S_IDLE;
            end
        endcase
    end

    assign wavefront_valid = (state == S_RUN);
    assign preproc_done    = (state == S_DONE);

    // ============================================================
    // Wavefront generation
    // lane r outputs A(r, t-r) if in range
    // (avoid signed int arithmetic; use unsigned guards)
    // ============================================================
    always_comb begin
        logic [T_W-1:0] col_u;  // Local variable declared at block scope
        
        // Default all lanes to zero
        wavefront_data = '0;
        col_u = '0;
        
        for (int r = 0; r < MAX_M; r = r + 1) begin
            if (wavefront_valid && (r < int'(mat_row_num))) begin
                // Only valid when t >= r (avoid negative column)
                if (t >= T_W'(r)) begin
                    col_u = t - T_W'(r);
                    if (col_u < mat_col_num) begin
                        wavefront_data[r*DATA_W +: DATA_W] = mem[r*MAX_K + int'(col_u)];
                    end
                end
            end
        end
    end

endmodule