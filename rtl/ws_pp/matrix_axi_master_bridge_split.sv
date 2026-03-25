`timescale 1ns / 1ps

module matrix_axi_master_bridge_split #(
    parameter int AXI_ADDR_WIDTH = 32,
    parameter int AXI_DATA_WIDTH = 32,
    parameter int AXI_ID_WIDTH   = 1
)(
    input  logic                         clk,
    input  logic                         resetn,

    // Read request channel
    input  logic                         rd_valid,
    output logic                         rd_ready,   // completion pulse
    input  logic [AXI_ADDR_WIDTH-1:0]    rd_addr,    // byte address
    output logic [AXI_DATA_WIDTH-1:0]    rd_rdata,

    // Write request channel
    input  logic                         wr_valid,
    output logic                         wr_ready,   // completion pulse
    input  logic [AXI_ADDR_WIDTH-1:0]    wr_addr,    // byte address
    input  logic [AXI_DATA_WIDTH-1:0]    wr_wdata,
    input  logic [AXI_DATA_WIDTH/8-1:0]  wr_wstrb,

    // AXI4 master write address channel (AW)
    output logic [AXI_ID_WIDTH-1:0]      m_axi_awid,
    output logic [AXI_ADDR_WIDTH-1:0]    m_axi_awaddr,
    output logic [7:0]                   m_axi_awlen,
    output logic [2:0]                   m_axi_awsize,
    output logic [1:0]                   m_axi_awburst,
    output logic                         m_axi_awlock,
    output logic [3:0]                   m_axi_awcache,
    output logic [2:0]                   m_axi_awprot,
    output logic                         m_axi_awvalid,
    input  logic                         m_axi_awready,

    // AXI4 master write data channel (W)
    output logic [AXI_DATA_WIDTH-1:0]    m_axi_wdata,
    output logic [AXI_DATA_WIDTH/8-1:0]  m_axi_wstrb,
    output logic                         m_axi_wlast,
    output logic                         m_axi_wvalid,
    input  logic                         m_axi_wready,

    // AXI4 master write response channel (B)
    input  logic [AXI_ID_WIDTH-1:0]      m_axi_bid,
    input  logic [1:0]                   m_axi_bresp,
    input  logic                         m_axi_bvalid,
    output logic                         m_axi_bready,

    // AXI4 master read address channel (AR)
    output logic [AXI_ID_WIDTH-1:0]      m_axi_arid,
    output logic [AXI_ADDR_WIDTH-1:0]    m_axi_araddr,
    output logic [7:0]                   m_axi_arlen,
    output logic [2:0]                   m_axi_arsize,
    output logic [1:0]                   m_axi_arburst,
    output logic                         m_axi_arlock,
    output logic [3:0]                   m_axi_arcache,
    output logic [2:0]                   m_axi_arprot,
    output logic                         m_axi_arvalid,
    input  logic                         m_axi_arready,

    // AXI4 master read data channel (R)
    input  logic [AXI_ID_WIDTH-1:0]      m_axi_rid,
    input  logic [AXI_DATA_WIDTH-1:0]    m_axi_rdata,
    input  logic [1:0]                   m_axi_rresp,
    input  logic                         m_axi_rlast,
    input  logic                         m_axi_rvalid,
    output logic                         m_axi_rready,

    output logic                         busy
);

    typedef enum logic [1:0] {
        R_IDLE = 2'd0,
        R_AR   = 2'd1,
        R_R    = 2'd2,
        R_RESP = 2'd3
    } r_state_e;

    typedef enum logic [2:0] {
        W_IDLE = 3'd0,
        W_AW   = 3'd1,
        W_W    = 3'd2,
        W_B    = 3'd3,
        W_RESP = 3'd4
    } w_state_e;

    r_state_e r_state, r_state_n;
    w_state_e w_state, w_state_n;

    logic [AXI_ADDR_WIDTH-1:0]   rd_addr_q;
    logic [AXI_ADDR_WIDTH-1:0]   wr_addr_q;
    logic [AXI_DATA_WIDTH-1:0]   wr_wdata_q;
    logic [AXI_DATA_WIDTH/8-1:0] wr_wstrb_q;

    // -------------------------
    // Read path
    // -------------------------
    always_ff @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            r_state   <= R_IDLE;
            rd_addr_q <= '0;
            rd_rdata  <= '0;
        end else begin
            r_state <= r_state_n;

            if ((r_state == R_IDLE) && rd_valid)
                rd_addr_q <= rd_addr;

            if ((r_state == R_R) && m_axi_rvalid && m_axi_rready)
                rd_rdata <= m_axi_rdata;
        end
    end

    always_comb begin
        r_state_n = r_state;
        case (r_state)
            R_IDLE: if (rd_valid) r_state_n = R_AR;
            R_AR:   if (m_axi_arvalid && m_axi_arready) r_state_n = R_R;
            R_R:    if (m_axi_rvalid && m_axi_rready && m_axi_rlast) r_state_n = R_RESP;
            R_RESP: r_state_n = R_IDLE;
            default: r_state_n = R_IDLE;
        endcase
    end

    // -------------------------
    // Write path
    // -------------------------
    always_ff @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            w_state    <= W_IDLE;
            wr_addr_q  <= '0;
            wr_wdata_q <= '0;
            wr_wstrb_q <= '0;
        end else begin
            w_state <= w_state_n;

            if ((w_state == W_IDLE) && wr_valid) begin
                wr_addr_q  <= wr_addr;
                wr_wdata_q <= wr_wdata;
                wr_wstrb_q <= wr_wstrb;
            end
        end
    end

    always_comb begin
        w_state_n = w_state;
        case (w_state)
            W_IDLE: if (wr_valid) w_state_n = W_AW;
            W_AW:   if (m_axi_awvalid && m_axi_awready) w_state_n = W_W;
            W_W:    if (m_axi_wvalid && m_axi_wready) w_state_n = W_B;
            W_B:    if (m_axi_bvalid && m_axi_bready) w_state_n = W_RESP;
            W_RESP: w_state_n = W_IDLE;
            default: w_state_n = W_IDLE;
        endcase
    end

    // Completion pulses back to request side
    assign rd_ready = (r_state == R_RESP);
    assign wr_ready = (w_state == W_RESP);

    // AXI read channel outputs
    assign m_axi_arid    = '0;
    assign m_axi_araddr  = rd_addr_q;
    assign m_axi_arlen   = 8'd0;     // single beat
    assign m_axi_arsize  = 3'd2;     // 4 bytes
    assign m_axi_arburst = 2'b01;    // INCR
    assign m_axi_arlock  = 1'b0;
    assign m_axi_arcache = 4'b0011;
    assign m_axi_arprot  = 3'b000;
    assign m_axi_arvalid = (r_state == R_AR);
    assign m_axi_rready  = (r_state == R_R);

    // AXI write channel outputs
    assign m_axi_awid    = '0;
    assign m_axi_awaddr  = wr_addr_q;
    assign m_axi_awlen   = 8'd0;     // single beat
    assign m_axi_awsize  = 3'd2;     // 4 bytes
    assign m_axi_awburst = 2'b01;    // INCR
    assign m_axi_awlock  = 1'b0;
    assign m_axi_awcache = 4'b0011;
    assign m_axi_awprot  = 3'b000;
    assign m_axi_awvalid = (w_state == W_AW);

    assign m_axi_wdata   = wr_wdata_q;
    assign m_axi_wstrb   = wr_wstrb_q;
    assign m_axi_wlast   = 1'b1;
    assign m_axi_wvalid  = (w_state == W_W);
    assign m_axi_bready  = (w_state == W_B);

    assign busy = (r_state != R_IDLE) || (w_state != W_IDLE);

endmodule
