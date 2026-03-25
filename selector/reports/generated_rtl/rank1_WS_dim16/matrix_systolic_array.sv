`timescale 1ns/1ps
module matrix_systolic_array #(
    parameter int DATA_W = 8,
    parameter int ACC_W  = 32,
    parameter int MAX_M  = 8,
    parameter int MAX_K  = 8,
    parameter int MAX_N  = 8
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
        S_IDLE    = 2'd0,
        S_LOAD_W  = 2'd1,
        S_COMPUTE = 2'd2,
        S_DONE    = 2'd3
    } state_e;

    state_e state, state_n;

    logic [$clog2(MAX_K+1)-1:0] k_idx, k_idx_n;
    logic [ACC_W-1:0] partial_sum [MAX_M*MAX_N];

    logic                         load_weight;
    logic [DATA_W-1:0]            pe_weight_q [MAX_M*MAX_N];
    logic signed [ACC_W-1:0]      pe_product  [MAX_M*MAX_N];

    function automatic logic [DATA_W-1:0] get_a_elem(
        input logic [MAX_M*MAX_K*DATA_W-1:0] flat,
        input int row_idx,
        input int k_col_idx
    );
        int phys;
        begin
            phys = row_idx * MAX_K + k_col_idx;
            get_a_elem = flat[phys*DATA_W +: DATA_W];
        end
    endfunction

    function automatic logic [DATA_W-1:0] get_b_elem(
        input logic [MAX_K*MAX_N*DATA_W-1:0] flat,
        input int k_row_idx,
        input int col_idx
    );
        int phys;
        begin
            phys = k_row_idx * MAX_N + col_idx;
            get_b_elem = flat[phys*DATA_W +: DATA_W];
        end
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_IDLE;
        else
            state <= state_n;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            k_idx <= '0;
        else
            k_idx <= k_idx_n;
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
            if (state == S_IDLE && start) begin
                for (ii = 0; ii < MAX_M*MAX_N; ii++) begin
                    partial_sum[ii] <= '0;
                end
            end else if (state == S_COMPUTE) begin
                for (ii = 0; ii < MAX_M; ii++) begin
                    for (jj = 0; jj < MAX_N; jj++) begin
                        idx = ii * MAX_N + jj;
                        if ((ii < mat_m_num) && (jj < mat_n_num) && (k_idx < mat_k_num))
                            partial_sum[idx] <= partial_sum[idx] + pe_product[idx];
                    end
                end
            end
        end
    end

    always_comb begin
        state_n = state;
        k_idx_n = k_idx;

        case (state)
            S_IDLE: begin
                if (start) begin
                    k_idx_n = '0;
                    if ((mat_m_num == 0) || (mat_k_num == 0) || (mat_n_num == 0))
                        state_n = S_DONE;
                    else
                        state_n = S_LOAD_W;
                end
            end

            S_LOAD_W: begin
                state_n = S_COMPUTE;
            end

            S_COMPUTE: begin
                if (k_idx == (mat_k_num - 1))
                    state_n = S_DONE;
                else begin
                    k_idx_n = k_idx + 1'b1;
                    state_n = S_LOAD_W;
                end
            end

            S_DONE: begin
                state_n = S_IDLE;
            end

            default: begin
                state_n = S_IDLE;
                k_idx_n = '0;
            end
        endcase
    end

    assign load_weight = (state == S_LOAD_W);

    genvar i, j;
    generate
        for (i = 0; i < MAX_M; i++) begin : GEN_ROW
            for (j = 0; j < MAX_N; j++) begin : GEN_COL
                localparam int IDX = i*MAX_N + j;

                matrix_pe #(
                    .DATA_W(DATA_W),
                    .ACC_W (ACC_W)
                ) u_pe (
                    .clk        (clk),
                    .rst_n      (rst_n),
                    .load_weight(load_weight && (j < mat_n_num) && (k_idx < mat_k_num)),
                    .weight_in  (get_b_elem(weight_matrix_flat, k_idx, j)),
                    .input_a    ((i < mat_m_num && k_idx < mat_k_num) ? get_a_elem(act_matrix_flat, i, k_idx) : '0),
                    .weight_q   (pe_weight_q[IDX]),
                    .product    (pe_product[IDX])
                );
            end
        end
    endgenerate

    always_comb begin
        partial_sum_flat = '0;
        for (ii = 0; ii < MAX_M; ii++) begin
            for (jj = 0; jj < MAX_N; jj++) begin
                idx = ii * MAX_N + jj;
                if ((ii < mat_m_num) && (jj < mat_n_num))
                    partial_sum_flat[idx*ACC_W +: ACC_W] = partial_sum[idx];
            end
        end
    end

    assign busy = (state != S_IDLE) && (state != S_DONE);
    assign done = (state == S_DONE);

endmodule
