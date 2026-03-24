module matrix_pe #(
    parameter int DATA_W = 8,
    parameter int ACC_W  = 32
)(
    input  logic clk,
    input  logic rst_n,

    input  logic                  load_weight,
    input  logic [DATA_W-1:0]     weight_in,
    input  logic [DATA_W-1:0]     input_a,

    output logic [DATA_W-1:0]     weight_q,
    output logic signed [ACC_W-1:0] product
);

    logic signed [DATA_W-1:0] weight_reg;
    logic signed [DATA_W-1:0] act_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            weight_reg <= '0;
            act_reg    <= '0;
        end else begin
            if (load_weight)
                weight_reg <= weight_in;
            act_reg <= input_a;
        end
    end

    assign weight_q = weight_reg;
    assign product  = $signed(act_reg) * $signed(weight_reg);

endmodule
