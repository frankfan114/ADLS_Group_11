`timescale 1ns / 1ps

module matrix_axi_master_bridge #(
    parameter integer AXI_ADDR_WIDTH = 32,
    parameter integer AXI_DATA_WIDTH = 32,
    parameter integer AXI_ID_WIDTH   = 1
)(
    input  wire                         clk,
    input  wire                         resetn,

    // ------------------------------------------------------------------------
    // Simple request/response memory side (non-AXI)
    // - One request at a time (no outstanding queue).
    // - Request fires when mem_valid=1 in IDLE.
    // - Read when mem_wstrb==0, write when any mem_wstrb bit is 1.
    // - Completion is a 1-cycle mem_ready pulse; mem_rdata is valid for reads.
    // ------------------------------------------------------------------------
    input  wire                         mem_valid,   // request valid
    output reg                          mem_ready,   // completion pulse
    input  wire [AXI_ADDR_WIDTH-1:0]    mem_addr,    // byte address
    input  wire [AXI_DATA_WIDTH-1:0]    mem_wdata,   // write payload
    input  wire [AXI_DATA_WIDTH/8-1:0]  mem_wstrb,   // byte enables; 0 => read
    output reg  [AXI_DATA_WIDTH-1:0]    mem_rdata,   // read payload

    // ------------------------------------------------------------------------
    // AXI4 master write address channel (AW)
    // This bridge issues only single-beat writes (AWLEN=0).
    // ------------------------------------------------------------------------
    output reg  [AXI_ID_WIDTH-1:0]      m_axi_awid,
    output reg  [AXI_ADDR_WIDTH-1:0]    m_axi_awaddr,
    output reg  [7:0]                   m_axi_awlen,
    output reg  [2:0]                   m_axi_awsize,
    output reg  [1:0]                   m_axi_awburst,
    output reg                          m_axi_awlock,
    output reg  [3:0]                   m_axi_awcache,
    output reg  [2:0]                   m_axi_awprot,
    output reg                          m_axi_awvalid,
    input  wire                         m_axi_awready,

    // AXI4 master write data channel (W)
    output reg  [AXI_DATA_WIDTH-1:0]    m_axi_wdata,
    output reg  [AXI_DATA_WIDTH/8-1:0]  m_axi_wstrb,
    output reg                          m_axi_wlast,
    output reg                          m_axi_wvalid,
    input  wire                         m_axi_wready,

    // AXI4 master write response channel (B)
    input  wire [AXI_ID_WIDTH-1:0]      m_axi_bid,
    input  wire [1:0]                   m_axi_bresp,
    input  wire                         m_axi_bvalid,
    output reg                          m_axi_bready,

    // ------------------------------------------------------------------------
    // AXI4 master read address channel (AR)
    // This bridge issues only single-beat reads (ARLEN=0).
    // ------------------------------------------------------------------------
    output reg  [AXI_ID_WIDTH-1:0]      m_axi_arid,
    output reg  [AXI_ADDR_WIDTH-1:0]    m_axi_araddr,
    output reg  [7:0]                   m_axi_arlen,
    output reg  [2:0]                   m_axi_arsize,
    output reg  [1:0]                   m_axi_arburst,
    output reg                          m_axi_arlock,
    output reg  [3:0]                   m_axi_arcache,
    output reg  [2:0]                   m_axi_arprot,
    output reg                          m_axi_arvalid,
    input  wire                         m_axi_arready,

    // AXI4 master read data channel (R)
    input  wire [AXI_ID_WIDTH-1:0]      m_axi_rid,
    input  wire [AXI_DATA_WIDTH-1:0]    m_axi_rdata,
    input  wire [1:0]                   m_axi_rresp,
    input  wire                         m_axi_rlast,
    input  wire                         m_axi_rvalid,
    output reg                          m_axi_rready,

    output wire                         busy         // bridge not in IDLE
);

    localparam [2:0]
        S_IDLE    = 3'd0,
        S_WR_AW   = 3'd1,
        S_WR_W    = 3'd2,
        S_WR_B    = 3'd3,
        S_RD_AR   = 3'd4,
        S_RD_R    = 3'd5,
        S_RESPOND = 3'd6;

    reg [2:0] state, state_n;

    reg [AXI_ADDR_WIDTH-1:0]   req_addr;
    reg [AXI_DATA_WIDTH-1:0]   req_wdata;
    reg [AXI_DATA_WIDTH/8-1:0] req_wstrb;
    wire mem_is_write = |mem_wstrb;

    always @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            state <= S_IDLE;
        end else begin
            state <= state_n;
        end
    end

    always @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            req_addr     <= {AXI_ADDR_WIDTH{1'b0}};
            req_wdata    <= {AXI_DATA_WIDTH{1'b0}};
            req_wstrb    <= {(AXI_DATA_WIDTH/8){1'b0}};
            mem_rdata    <= {AXI_DATA_WIDTH{1'b0}};
        end else begin
            if (state == S_IDLE && mem_valid) begin
                req_addr     <= mem_addr;
                req_wdata    <= mem_wdata;
                req_wstrb    <= mem_wstrb;
            end

            if (state == S_RD_R && m_axi_rvalid && m_axi_rready) begin
                mem_rdata <= m_axi_rdata;
            end
        end
    end

    always @(*) begin
        state_n = state;
        case (state)
            S_IDLE: begin
                if (mem_valid) begin
                    if (mem_is_write) state_n = S_WR_AW;
                    else              state_n = S_RD_AR;
                end
            end

            S_WR_AW: begin
                if (m_axi_awvalid && m_axi_awready) state_n = S_WR_W;
            end

            S_WR_W: begin
                if (m_axi_wvalid && m_axi_wready) state_n = S_WR_B;
            end

            S_WR_B: begin
                if (m_axi_bvalid && m_axi_bready) state_n = S_RESPOND;
            end

            S_RD_AR: begin
                if (m_axi_arvalid && m_axi_arready) state_n = S_RD_R;
            end

            S_RD_R: begin
                if (m_axi_rvalid && m_axi_rready && m_axi_rlast) state_n = S_RESPOND;
            end

            S_RESPOND: begin
                state_n = S_IDLE;
            end

            default: state_n = S_IDLE;
        endcase
    end

    always @(*) begin
        mem_ready = (state == S_RESPOND);

        // Defaults
        m_axi_awid    = {AXI_ID_WIDTH{1'b0}};
        m_axi_awaddr  = req_addr;
        m_axi_awlen   = 8'd0;     // single beat
        m_axi_awsize  = 3'd2;     // 4 bytes
        m_axi_awburst = 2'b01;    // INCR
        m_axi_awlock  = 1'b0;
        m_axi_awcache = 4'b0011;
        m_axi_awprot  = 3'b000;
        m_axi_awvalid = (state == S_WR_AW);

        m_axi_wdata   = req_wdata;
        m_axi_wstrb   = req_wstrb;
        m_axi_wlast   = 1'b1;
        m_axi_wvalid  = (state == S_WR_W);

        m_axi_bready  = (state == S_WR_B);

        m_axi_arid    = {AXI_ID_WIDTH{1'b0}};
        m_axi_araddr  = req_addr;
        m_axi_arlen   = 8'd0;     // single beat
        m_axi_arsize  = 3'd2;     // 4 bytes
        m_axi_arburst = 2'b01;    // INCR
        m_axi_arlock  = 1'b0;
        m_axi_arcache = 4'b0011;
        m_axi_arprot  = 3'b000;
        m_axi_arvalid = (state == S_RD_AR);

        m_axi_rready  = (state == S_RD_R);
    end

    assign busy = (state != S_IDLE);

endmodule
