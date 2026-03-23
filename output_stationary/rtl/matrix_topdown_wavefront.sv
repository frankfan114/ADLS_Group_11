`timescale 1ns/1ps
module matrix_topdown_wavefront #(
    parameter int DATA_W = 8,

    // hardware capability (compile-time)
    parameter int MAX_K  = 8,   // max rows of B (inner dimension)
    parameter int MAX_N  = 8    // max cols of B (top lanes)
)(
    input  logic clk,
    input  logic rst_n,

    // ============================================================
    // Runtime matrix geometry
    // ============================================================
    input  logic [$clog2(MAX_K+1)-1:0] mat_k_num,  // actual K (rows)
    input  logic [$clog2(MAX_N+1)-1:0] mat_n_num,  // actual N (cols)

    // ============================================================
    // Load interface (ROW-major input)
    // ============================================================
    input  logic                      preproc_load_row_valid,
    input  logic [MAX_N*DATA_W-1:0]   preproc_load_row_data,
    input  logic                      preproc_load_clear,

    // ============================================================
    // Control
    // ============================================================
    input  logic preproc_start,   // start wavefront scan

    // ============================================================
    // Wavefront output (to systolic array top lanes)
    // lane j outputs B(t-j, j)
    // ============================================================
    output logic                    wavefront_valid,
    output logic [MAX_N*DATA_W-1:0] wavefront_data,
    output logic                    preproc_done
);

    // ============================================================
    // Internal storage: row-major B (MAX_K x MAX_N)
    // addr = row*MAX_N + col
    // ============================================================
    localparam int MEM_SIZE = MAX_K * MAX_N;
    logic [DATA_W-1:0] mem [0:MEM_SIZE-1];

    // ============================================================
    // Load control
    // ============================================================
    logic [$clog2(MAX_K+1)-1:0] wr_row;
    wire load_done = (wr_row == mat_k_num);

    integer i_init;
    integer col_i;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_row <= '0;
            for (i_init = 0; i_init < MEM_SIZE; i_init = i_init + 1)
                mem[i_init] <= '0;
        end else begin
            if (preproc_load_clear) begin
                wr_row <= '0;
            end else if (preproc_load_row_valid && !load_done) begin
                for (col_i = 0; col_i < MAX_N; col_i = col_i + 1) begin
                    if (col_i < mat_n_num)
                        mem[wr_row*MAX_N + col_i] <= preproc_load_row_data[col_i*DATA_W +: DATA_W];
                    else
                        mem[wr_row*MAX_N + col_i] <= '0;
                end
                wr_row <= wr_row + 1'b1;
            end
        end
    end

    // ============================================================
    // Wavefront FSM: t = 0 .. (K+N-2)
    // ============================================================
    typedef enum logic [1:0] { S_IDLE, S_RUN, S_DONE } state_t;
    state_t state, state_n;

    localparam int T_W = (MAX_K + MAX_N <= 1) ? 1 : $clog2(MAX_K + MAX_N);
    logic [T_W-1:0] t, t_n;
    logic [T_W-1:0] t_max;

    // Guard t_max against underflow when K or N is 0
    always_comb begin
        if ((mat_k_num == 0) || (mat_n_num == 0)) begin
            t_max = '0;
        end else begin
            t_max = (mat_k_num + mat_n_num - 2);
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            t     <= '0;
        end else begin
            state <= state_n;
            t     <= t_n;
        end
    end

    always_comb begin
        state_n = state;
        t_n     = t;

        case (state)
            S_IDLE: begin
                if (preproc_start && load_done) begin
                    // If no work, finish immediately
                    if ((mat_k_num == 0) || (mat_n_num == 0)) begin
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
    // Wavefront output:
    // lane j → element B(t-j, j)
    // Avoid signed arithmetic: use unsigned guard t>=j
    // ============================================================
    always_comb begin
        logic [T_W-1:0] row_u;  // Local variable declared at block scope
        
        // Default all lanes to zero
        wavefront_data = '0;
        row_u = '0;
        
        for (int j = 0; j < MAX_N; j = j + 1) begin
            if (wavefront_valid && (j < int'(mat_n_num))) begin
                if (t >= T_W'(j)) begin
                    row_u = t - T_W'(j);
                    if (row_u < mat_k_num) begin
                        wavefront_data[j*DATA_W +: DATA_W] = mem[int'(row_u)*MAX_N + j];
                    end
                end
            end
        end
    end

endmodule