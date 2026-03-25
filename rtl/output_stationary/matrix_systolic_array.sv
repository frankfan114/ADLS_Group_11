`timescale 1ns/1ps
module matrix_systolic_array #(
    parameter int DATA_W = 8,
    parameter int ACC_W  = 32,
    parameter int MAX_M  = 8,
    parameter int MAX_N  = 8
)(
    input  logic clk,
    input  logic rst_n,

    input  logic [$clog2(MAX_M+1)-1:0] mat_m_num,
    input  logic [$clog2(MAX_N+1)-1:0] mat_n_num,

    input  logic start_top_wavefront,
    input  logic start_left_wavefront,

    input  logic top_wavefront_valid,
    input  logic left_wavefront_valid,

    input  logic [MAX_N*DATA_W-1:0] top_wavefront_vec,
    input  logic [MAX_M*DATA_W-1:0] left_wavefront_vec,

    input  logic clear_acc,

    output logic [ACC_W*MAX_M*MAX_N-1:0] partial_sum_flat
);

    // ------------------------------------------------------------
    // Unpack inputs
    // ------------------------------------------------------------
    logic [ACC_W-1:0]  partial_sum [MAX_M*MAX_N];
    logic [DATA_W-1:0] top_arr  [MAX_N];
    logic [DATA_W-1:0] left_arr [MAX_M];

    genvar gv;
    generate
        for (gv = 0; gv < MAX_N; gv++) begin : UNPACK_TOP
            assign top_arr[gv] = top_wavefront_vec[gv*DATA_W +: DATA_W];
        end
        for (gv = 0; gv < MAX_M; gv++) begin : UNPACK_LEFT
            assign left_arr[gv] = left_wavefront_vec[gv*DATA_W +: DATA_W];
        end
    endgenerate

    // ------------------------------------------------------------
    // Internal pipelines
    // ------------------------------------------------------------
    logic [DATA_W-1:0] val_top_pipe  [MAX_M+1][MAX_N];
    logic [DATA_W-1:0] val_left_pipe [MAX_M][MAX_N+1];

    logic start_top_pipe  [MAX_M+1][MAX_N];
    logic start_left_pipe [MAX_M][MAX_N+1];

    // feed top and left boundaries (still combinational, small)
    generate
        for (gv = 0; gv < MAX_N; gv++) begin : FEED_TOP
            assign val_top_pipe[0][gv] =
                (top_wavefront_valid && (gv < mat_n_num)) ? top_arr[gv] : '0;
            assign start_top_pipe[0][gv] = (gv == 0) ? start_top_wavefront : 1'b0;
        end

        for (gv = 0; gv < MAX_M; gv++) begin : FEED_LEFT
            assign val_left_pipe[gv][0] =
                (left_wavefront_valid && (gv < mat_m_num)) ? left_arr[gv] : '0;
            assign start_left_pipe[gv][0] = (gv == 0) ? start_left_wavefront : 1'b0;
        end
    endgenerate

    // ------------------------------------------------------------
    // PE array
    // ------------------------------------------------------------
    genvar i, j;
    generate
        for (i = 0; i < MAX_M; i++) begin : ROW
            for (j = 0; j < MAX_N; j++) begin : COL
                localparam int IDX = i*MAX_N + j;

                matrix_pe #(
                    .DATA_W(DATA_W),
                    .ACC_W (ACC_W)
                ) u_pe (
                    .clk(clk),
                    .rst_n(rst_n),

                    .start_a_in(start_top_pipe[i][j]),
                    .start_b_in(start_left_pipe[i][j]),

                    .input_a(val_top_pipe[i][j]),
                    .input_b(val_left_pipe[i][j]),
                    .clear_acc(clear_acc),

                    .input_a_out(val_top_pipe[i+1][j]),
                    .input_b_out(val_left_pipe[i][j+1]),

                    .start_a_out(start_top_pipe[i+1][j]),
                    .start_b_out(start_left_pipe[i][j+1]),

                    .partial_sum(partial_sum[IDX])
                );
            end
        end
    endgenerate

    // ------------------------------------------------------------
    // Flatten with runtime mask (REGISTERED to improve timing)
    // ------------------------------------------------------------
    logic [ACC_W*MAX_M*MAX_N-1:0] partial_sum_flat_r;

    integer ii, jj;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            partial_sum_flat_r <= '0;
        end else begin
            // Optional: you can gate this update only when running to reduce toggling.
            // Here we keep it always-updated for simplicity.
            for (ii = 0; ii < MAX_M; ii++) begin
                for (jj = 0; jj < MAX_N; jj++) begin
                    int idx;
                    idx = ii*MAX_N + jj;
                    if ((ii < mat_m_num) && (jj < mat_n_num))
                        partial_sum_flat_r[idx*ACC_W +: ACC_W] <= partial_sum[idx];
                    else
                        partial_sum_flat_r[idx*ACC_W +: ACC_W] <= '0;
                end
            end
        end
    end

    assign partial_sum_flat = partial_sum_flat_r;

endmodule