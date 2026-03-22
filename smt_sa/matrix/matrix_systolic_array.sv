`timescale 1ns/1ps
module matrix_systolic_array #(
    parameter int DATA_W      = 8,
    parameter int ACC_W       = 32,
    parameter int MAX_M       = 8,
    parameter int MAX_K       = 8,
    parameter int MAX_N       = 8,
    parameter int SMT_THREADS = 4
)(
    input  logic clk,
    input  logic rst_n,

    input  logic start,
    input  logic [$clog2(MAX_M+1)-1:0] mat_m_num,
    input  logic [$clog2(MAX_K+1)-1:0] mat_k_num,
    input  logic [$clog2(MAX_N+1)-1:0] mat_n_num,

    input  logic [MAX_M*MAX_K*DATA_W-1:0] act_matrix_flat,
    input  logic [MAX_K*MAX_N*DATA_W-1:0] weight_matrix_flat,

    output logic [ACC_W*MAX_M*MAX_N-1:0] partial_sum_flat,
    output logic busy,
    output logic done
);

    typedef enum logic [1:0] {
        S_IDLE = 2'd0,
        S_RUN  = 2'd1,
        S_DONE = 2'd2
    } state_e;

    state_e state, state_n;

    logic signed [ACC_W-1:0] partial_sum [0:MAX_M*MAX_N-1];
    logic signed [ACC_W-1:0] pe_product  [0:MAX_M*MAX_N-1];
    logic                    pe_product_valid [0:MAX_M*MAX_N-1];
    logic                    pe_busy         [0:MAX_M*MAX_N-1];
    logic                    pe_done         [0:MAX_M*MAX_N-1];

    function automatic logic [MAX_K*DATA_W-1:0] get_a_row_vec(
        input logic [MAX_M*MAX_K*DATA_W-1:0] flat,
        input int                            row_idx
    );
        begin
            get_a_row_vec = flat[row_idx*MAX_K*DATA_W +: MAX_K*DATA_W];
        end
    endfunction

    function automatic logic [MAX_K*DATA_W-1:0] get_b_col_vec(
        input logic [MAX_K*MAX_N*DATA_W-1:0] flat,
        input int                            col_idx
    );
        int kk;
        int phys;
        begin
            get_b_col_vec = '0;
            for (kk = 0; kk < MAX_K; kk++) begin
                phys = kk * MAX_N + col_idx;
                get_b_col_vec[kk*DATA_W +: DATA_W] = flat[phys*DATA_W +: DATA_W];
            end
        end
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_IDLE;
        else
            state <= state_n;
    end

    integer ii;
    integer jj;
    integer idx;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (ii = 0; ii < MAX_M*MAX_N; ii++) begin
                partial_sum[ii] <= '0;
            end
        end else begin
            if ((state == S_IDLE) && start) begin
                for (ii = 0; ii < MAX_M*MAX_N; ii++) begin
                    partial_sum[ii] <= '0;
                end
            end else if (state == S_RUN) begin
                for (ii = 0; ii < MAX_M; ii++) begin
                    for (jj = 0; jj < MAX_N; jj++) begin
                        idx = ii * MAX_N + jj;
                        if ((ii < int'(mat_m_num)) &&
                            (jj < int'(mat_n_num)) &&
                            pe_product_valid[idx]) begin
                            partial_sum[idx] <= partial_sum[idx] + pe_product[idx];
                        end
                    end
                end
            end
        end
    end

    logic all_pe_done;
    always_comb begin
        all_pe_done = 1'b1;
        for (ii = 0; ii < MAX_M; ii++) begin
            for (jj = 0; jj < MAX_N; jj++) begin
                idx = ii * MAX_N + jj;
                if ((ii < int'(mat_m_num)) &&
                    (jj < int'(mat_n_num)) &&
                    !pe_done[idx]) begin
                    all_pe_done = 1'b0;
                end
            end
        end
    end

    always_comb begin
        state_n = state;

        case (state)
            S_IDLE: begin
                if (start) begin
                    if ((mat_m_num == '0) || (mat_k_num == '0) || (mat_n_num == '0))
                        state_n = S_DONE;
                    else
                        state_n = S_RUN;
                end
            end

            S_RUN: begin
                if (all_pe_done)
                    state_n = S_DONE;
            end

            S_DONE: begin
                state_n = S_IDLE;
            end

            default: begin
                state_n = S_IDLE;
            end
        endcase
    end

    genvar i, j;
    generate
        for (i = 0; i < MAX_M; i++) begin : GEN_ROW
            for (j = 0; j < MAX_N; j++) begin : GEN_COL
                localparam int IDX = i * MAX_N + j;

                matrix_pe #(
                    .DATA_W     (DATA_W),
                    .ACC_W      (ACC_W),
                    .MAX_K      (MAX_K),
                    .SMT_THREADS(SMT_THREADS)
                ) u_pe (
                    .clk         (clk),
                    .rst_n       (rst_n),
                    .start       ((state == S_IDLE) && start),
                    .mat_k_num   (((i < mat_m_num) && (j < mat_n_num)) ? mat_k_num : '0),
                    .act_vec     (get_a_row_vec(act_matrix_flat, i)),
                    .weight_vec  (get_b_col_vec(weight_matrix_flat, j)),
                    .product     (pe_product[IDX]),
                    .product_valid(pe_product_valid[IDX]),
                    .busy        (pe_busy[IDX]),
                    .done        (pe_done[IDX])
                );
            end
        end
    endgenerate

    always_comb begin
        partial_sum_flat = '0;
        for (ii = 0; ii < MAX_M; ii++) begin
            for (jj = 0; jj < MAX_N; jj++) begin
                idx = ii * MAX_N + jj;
                if ((ii < int'(mat_m_num)) && (jj < int'(mat_n_num)))
                    partial_sum_flat[idx*ACC_W +: ACC_W] = partial_sum[idx];
            end
        end
    end

    assign busy = (state == S_RUN);
    assign done = (state == S_DONE);

endmodule
