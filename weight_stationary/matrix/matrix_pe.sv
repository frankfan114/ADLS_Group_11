module matrix_pe #(
    parameter int DATA_W = 8,
    parameter int ACC_W  = 32
)(
    input  logic clk,
    input  logic rst_n,

    input  logic start_a_in,
    input  logic start_b_in,

    input  logic [DATA_W-1:0] input_a,
    input  logic [DATA_W-1:0] input_b,

    input logic clear_acc,

    output logic [DATA_W-1:0] input_a_out,
    output logic [DATA_W-1:0] input_b_out,

    output logic start_a_out,
    output logic start_b_out,

    output logic [ACC_W-1:0] partial_sum
);

    // operand regs
    logic [DATA_W-1:0] a_reg, b_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_reg <= '0;
            b_reg <= '0;
        end else begin
            a_reg <= input_a;
            b_reg <= input_b;
        end
    end

    assign input_a_out = a_reg;
    assign input_b_out = b_reg;

    // start wave
    logic start_a_reg, start_b_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_a_reg <= 1'b0;
            start_b_reg <= 1'b0;
        end else begin
            start_a_reg <= start_a_in;
            start_b_reg <= start_b_in;
        end
    end

    assign start_a_out = start_a_reg;
    assign start_b_out = start_b_reg;

    // MAC (signed multiplication for int8 support)
    logic signed [ACC_W-1:0] acc_reg;
    wire effective_start = start_a_reg | start_b_reg;
    // Sign-extend 8-bit inputs to signed, then multiply
    wire signed [ACC_W-1:0] mult_val = $signed(a_reg) * $signed(b_reg);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc_reg <= '0;
        else if (clear_acc)
            acc_reg <= '0;
        else if (effective_start)
            acc_reg <= mult_val;
        else
            acc_reg <= acc_reg + mult_val;
    end

    assign partial_sum = acc_reg;

endmodule