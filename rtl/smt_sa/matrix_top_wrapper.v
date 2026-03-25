`timescale 1ns / 1ps

module matrix_top_wrapper #(
    parameter DATA_W     = 8,
    parameter ACC_W      = 32,
    parameter MAX_M      = 8,
    parameter MAX_K      = 8,
    parameter MAX_N      = 8,
    parameter SRAM_W     = 32,
    parameter ADDR_WIDTH = 32,
    parameter SMT_THREADS = 4
)(
    input  wire        clk,
    input  wire        resetn,

    // ============================================================
    // Bus interface (SLAVE, CPU config)
    // ============================================================
    input  wire        bus_valid,
    output reg         bus_ready,
    input  wire [31:0] bus_addr,
    input  wire [31:0] bus_wdata,
    input  wire [3:0]  bus_wstrb,
    output reg  [31:0] bus_rdata,

    // ============================================================
    // AXI4 MASTER interface (to DDR subsystem / MIG)
    // ============================================================
    output wire [0:0]  m_axi_awid,
    output wire [31:0] m_axi_awaddr,
    output wire [7:0]  m_axi_awlen,
    output wire [2:0]  m_axi_awsize,
    output wire [1:0]  m_axi_awburst,
    output wire        m_axi_awlock,
    output wire [3:0]  m_axi_awcache,
    output wire [2:0]  m_axi_awprot,
    output wire        m_axi_awvalid,
    input  wire        m_axi_awready,

    output wire [31:0] m_axi_wdata,
    output wire [3:0]  m_axi_wstrb,
    output wire        m_axi_wlast,
    output wire        m_axi_wvalid,
    input  wire        m_axi_wready,

    input  wire [0:0]  m_axi_bid,
    input  wire [1:0]  m_axi_bresp,
    input  wire        m_axi_bvalid,
    output wire        m_axi_bready,

    output wire [0:0]  m_axi_arid,
    output wire [31:0] m_axi_araddr,
    output wire [7:0]  m_axi_arlen,
    output wire [2:0]  m_axi_arsize,
    output wire [1:0]  m_axi_arburst,
    output wire        m_axi_arlock,
    output wire [3:0]  m_axi_arcache,
    output wire [2:0]  m_axi_arprot,
    output wire        m_axi_arvalid,
    input  wire        m_axi_arready,

    input  wire [0:0]  m_axi_rid,
    input  wire [31:0] m_axi_rdata,
    input  wire [1:0]  m_axi_rresp,
    input  wire        m_axi_rlast,
    input  wire        m_axi_rvalid,
    output wire        m_axi_rready,

    output wire        dma_busy
);

    // ============================================================
    // 1. Register Definitions (CPU-visible config)
    // ============================================================
    reg [31:0] reg_addr_a;
    reg [31:0] reg_addr_b;
    reg [31:0] reg_addr_c;

    reg [31:0] reg_m_num;
    reg [31:0] reg_k_num;
    reg [31:0] reg_n_num;
    reg [4:0]  reg_shift;

    reg        start_pulse;
    reg        done_latched;

    // status from core
    wire sys_busy;
    wire sys_done;

    // bus helpers
    wire write_en = bus_valid && (|bus_wstrb);
    wire read_en  = bus_valid && (~|bus_wstrb);
    wire [5:2] addr_idx = bus_addr[5:2]; // word index

    // ============================================================
    // 2. Bus Register Read / Write
    // ============================================================
    always @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            bus_ready    <= 1'b0;
            bus_rdata    <= 32'd0;

            reg_addr_a   <= 32'd0;
            reg_addr_b   <= 32'd0;
            reg_addr_c   <= 32'd0;
            reg_m_num    <= MAX_M;
            reg_k_num    <= MAX_K;
            reg_n_num    <= MAX_N;
            reg_shift    <= 5'd0;

            start_pulse  <= 1'b0;
            done_latched <= 1'b0;
        end else begin
            bus_ready   <= 1'b0;
            start_pulse <= 1'b0;

            // -------------------------
            // Write
            // -------------------------
            if (write_en && !bus_ready) begin
                bus_ready <= 1'b1;
                case (addr_idx)
                    4'h0: reg_addr_a <= bus_wdata;        // 0x00
                    4'h1: reg_addr_b <= bus_wdata;        // 0x04
                    4'h2: reg_addr_c <= bus_wdata;        // 0x08
                    4'h3: reg_m_num  <= bus_wdata;        // 0x0C
                    4'h4: reg_k_num  <= bus_wdata;        // 0x10
                    4'h5: reg_n_num  <= bus_wdata;        // 0x14
                    4'h6: reg_shift  <= bus_wdata[4:0];  // 0x18
                    4'h7: begin                           // 0x1C control
                        if (bus_wdata[0]) begin
                            start_pulse  <= 1'b1;
                            done_latched <= 1'b0;
                        end
                    end
                    default: ;
                endcase
            end

            // -------------------------
            // Read
            // -------------------------
            if (read_en && !bus_ready) begin
                bus_ready <= 1'b1;
                case (addr_idx)
                    4'h0: bus_rdata <= reg_addr_a;
                    4'h1: bus_rdata <= reg_addr_b;
                    4'h2: bus_rdata <= reg_addr_c;
                    4'h3: bus_rdata <= reg_m_num;
                    4'h4: bus_rdata <= reg_k_num;
                    4'h5: bus_rdata <= reg_n_num;
                    4'h6: bus_rdata <= {27'd0, reg_shift};
                    4'h8: bus_rdata <= {30'd0, done_latched, sys_busy}; // status
                    default: bus_rdata <= 32'd0;
                endcase
            end

            if (sys_done)
                done_latched <= 1'b1;
        end
    end

    // ============================================================
    // 3. matrix_tiled instance
    // ============================================================
    wire        sys_mem_valid;
    wire [31:0] sys_mem_addr;
    wire [31:0] sys_mem_wdata;
    wire [3:0]  sys_mem_wstrb;

    wire        sys_mem_ready;
    wire [31:0] sys_mem_rdata;

    matrix_tiled #(
        .DATA_W      (DATA_W),
        .ACC_W       (ACC_W),
        .MAX_M       (MAX_M),
        .MAX_K       (MAX_K),
        .MAX_N       (MAX_N),
        .SRAM_W      (SRAM_W),
        .ADDR_WIDTH  (ADDR_WIDTH),
        .PE_PIPE     (1),
        .SMT_THREADS (SMT_THREADS)
    ) u_core (
        .clk        (clk),
        .rst_n      (resetn),

        .start      (start_pulse),

        .glob_m_num (reg_m_num[15:0]),
        .glob_k_num (reg_k_num[15:0]),
        .glob_n_num (reg_n_num[15:0]),

        .base_addr_A(reg_addr_a),
        .base_addr_B(reg_addr_b),
        .base_addr_C(reg_addr_c),

        .mem_valid  (sys_mem_valid),
        .mem_ready  (sys_mem_ready),
        .mem_addr   (sys_mem_addr),
        .mem_wdata  (sys_mem_wdata),
        .mem_wstrb  (sys_mem_wstrb),
        .mem_rdata  (sys_mem_rdata),

        .busy       (sys_busy),
        .done       (sys_done)
    );

    // ============================================================
    // 4. Bridge: simple mem -> AXI4 master
    // ============================================================
    matrix_axi_master_bridge #(
        .AXI_ADDR_WIDTH (32),
        .AXI_DATA_WIDTH (32),
        .AXI_ID_WIDTH   (1)
    ) u_axi_bridge (
        .clk          (clk),
        .resetn       (resetn),
        .mem_valid    (sys_mem_valid),
        .mem_ready    (sys_mem_ready),
        .mem_addr     (sys_mem_addr),
        .mem_wdata    (sys_mem_wdata),
        .mem_wstrb    (sys_mem_wstrb),
        .mem_rdata    (sys_mem_rdata),

        .m_axi_awid   (m_axi_awid),
        .m_axi_awaddr (m_axi_awaddr),
        .m_axi_awlen  (m_axi_awlen),
        .m_axi_awsize (m_axi_awsize),
        .m_axi_awburst(m_axi_awburst),
        .m_axi_awlock (m_axi_awlock),
        .m_axi_awcache(m_axi_awcache),
        .m_axi_awprot (m_axi_awprot),
        .m_axi_awvalid(m_axi_awvalid),
        .m_axi_awready(m_axi_awready),

        .m_axi_wdata  (m_axi_wdata),
        .m_axi_wstrb  (m_axi_wstrb),
        .m_axi_wlast  (m_axi_wlast),
        .m_axi_wvalid (m_axi_wvalid),
        .m_axi_wready (m_axi_wready),

        .m_axi_bid    (m_axi_bid),
        .m_axi_bresp  (m_axi_bresp),
        .m_axi_bvalid (m_axi_bvalid),
        .m_axi_bready (m_axi_bready),

        .m_axi_arid   (m_axi_arid),
        .m_axi_araddr (m_axi_araddr),
        .m_axi_arlen  (m_axi_arlen),
        .m_axi_arsize (m_axi_arsize),
        .m_axi_arburst(m_axi_arburst),
        .m_axi_arlock (m_axi_arlock),
        .m_axi_arcache(m_axi_arcache),
        .m_axi_arprot (m_axi_arprot),
        .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready),

        .m_axi_rid    (m_axi_rid),
        .m_axi_rdata  (m_axi_rdata),
        .m_axi_rresp  (m_axi_rresp),
        .m_axi_rlast  (m_axi_rlast),
        .m_axi_rvalid (m_axi_rvalid),
        .m_axi_rready (m_axi_rready),

        .busy         (dma_busy)
    );



endmodule
