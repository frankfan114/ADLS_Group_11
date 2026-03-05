//*****************************************************************************

// (c) Copyright 2009 - 2010 Xilinx, Inc. All rights reserved.

//

// This file contains confidential and proprietary information

// of Xilinx, Inc. and is protected under U.S. and

// international copyright and other intellectual property

// laws.

//

// DISCLAIMER

// This disclaimer is not a license and does not grant any

// rights to the materials distributed herewith. Except as

// otherwise provided in a valid license issued to you by

// Xilinx, and to the maximum extent permitted by applicable

// law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND

// WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES

// AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING

// BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-

// INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and

// (2) Xilinx shall not be liable (whether in contract or tort,

// including negligence, or under any other theory of

// liability) for any loss or damage of any kind or nature

// related to, arising under or in connection with these

// materials, including for any direct, or any indirect,

// special, incidental, or consequential loss or damage

// (including loss of data, profits, goodwill, or any type of

// loss or damage suffered as a result of any action brought

// by a third party) even if such damage or loss was

// reasonably foreseeable or Xilinx had been advised of the

// possibility of the same.

//

// CRITICAL APPLICATIONS

// Xilinx products are not designed or intended to be fail-

// safe, or for use in any application requiring fail-safe

// performance, such as life-support or safety devices or

// systems, Class III medical devices, nuclear facilities,

// applications related to the deployment of airbags, or any

// other applications that could lead to death, personal

// injury, or severe property or environmental damage

// (individually and collectively, "Critical

// Applications"). Customer assumes the sole risk and

// liability of any use of Xilinx products in Critical

// Applications, subject only to applicable laws and

// regulations governing limitations on product liability.

//

// THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS

// PART OF THIS FILE AT ALL TIMES.

//

//*****************************************************************************

//   ____  ____

//  /   /\/   /

// /___/  \  /    Vendor             : Xilinx

// \   \   \/     Version            : 4.2

//  \   \         Application        : MIG

//  /   /         Filename           : sim_tb_top.v

// /___/   /\     Date Last Modified : $Date: 2011/06/07 13:45:16 $

// \   \  /  \    Date Created       : Tue Sept 21 2010

//  \___\/\___\

//

// Device           : 7 Series

// Design Name      : DDR3 SDRAM

// Purpose          :

//                   Top-level testbench for testing DDR3.

//                   Instantiates:

//                     1. IP_TOP (top-level representing FPGA, contains core,

//                        clocking, built-in testbench/memory checker and other

//                        support structures)

//                     2. DDR3 Memory

//                     3. Miscellaneous clock generation and reset logic

//                     4. For ECC ON case inserts error on LSB bit

//                        of data from DRAM to FPGA.

// Reference        :

// Revision History :

//*****************************************************************************



`timescale 1ps/100fs



module sim_tb_top;





   //***************************************************************************

   // Traffic Gen related parameters

   //***************************************************************************

   parameter SIMULATION            = "TRUE";

   parameter BEGIN_ADDRESS         = 32'h00000000;

   parameter END_ADDRESS           = 32'h00000fff;

   parameter PRBS_EADDR_MASK_POS   = 32'hff000000;



   //***************************************************************************

   // The following parameters refer to width of various ports

   //***************************************************************************

   parameter COL_WIDTH             = 10;

                                     // # of memory Column Address bits.

   parameter CS_WIDTH              = 1;

                                     // # of unique CS outputs to memory.

   parameter DM_WIDTH              = 1;

                                     // # of DM (data mask)

   parameter DQ_WIDTH              = 8;

                                     // # of DQ (data)

   parameter DQS_WIDTH             = 1;

   parameter DQS_CNT_WIDTH         = 1;

                                     // = ceil(log2(DQS_WIDTH))

   parameter DRAM_WIDTH            = 8;

                                     // # of DQ per DQS

   parameter ECC                   = "OFF";

   parameter RANKS                 = 1;

                                     // # of Ranks.

   parameter ODT_WIDTH             = 1;

                                     // # of ODT outputs to memory.

   parameter ROW_WIDTH             = 14;

                                     // # of memory Row Address bits.

   parameter ADDR_WIDTH            = 28;

                                     // # = RANK_WIDTH + BANK_WIDTH

                                     //     + ROW_WIDTH + COL_WIDTH;

                                     // Chip Select is always tied to low for

                                     // single rank devices

   //***************************************************************************

   // The following parameters are mode register settings

   //***************************************************************************

   parameter BURST_MODE            = "8";

                                     // DDR3 SDRAM:

                                     // Burst Length (Mode Register 0).

                                     // # = "8", "4", "OTF".

                                     // DDR2 SDRAM:

                                     // Burst Length (Mode Register).

                                     // # = "8", "4".

   parameter CA_MIRROR             = "OFF";

                                     // C/A mirror opt for DDR3 dual rank

   

   //***************************************************************************

   // The following parameters are multiplier and divisor factors for PLLE2.

   // Based on the selected design frequency these parameters vary.

   //***************************************************************************

   parameter CLKIN_PERIOD          = 3225;

                                     // Input Clock Period





   //***************************************************************************

   // Simulation parameters

   //***************************************************************************

   parameter SIM_BYPASS_INIT_CAL   = "FAST";

                                     // # = "SIM_INIT_CAL_FULL" -  Complete

                                     //              memory init &

                                     //              calibration sequence

                                     // # = "SKIP" - Not supported

                                     // # = "FAST" - Complete memory init & use

                                     //              abbreviated calib sequence



   //***************************************************************************

   // IODELAY and PHY related parameters

   //***************************************************************************

   parameter TCQ                   = 100;

   //***************************************************************************

   // IODELAY and PHY related parameters

   //***************************************************************************

   parameter RST_ACT_LOW           = 1;

                                     // =1 for active low reset,

                                     // =0 for active high.



   //***************************************************************************

   // Referece clock frequency parameters

   //***************************************************************************

   parameter REFCLK_FREQ           = 200.0;

                                     // IODELAYCTRL reference clock frequency

   //***************************************************************************

   // System clock frequency parameters

   //***************************************************************************

   parameter tCK                   = 3225;

                                     // memory tCK paramter.

                     // # = Clock Period in pS.

   parameter nCK_PER_CLK           = 2;

                                     // # of memory CKs per fabric CLK



   

   //***************************************************************************

   // AXI4 Shim parameters

   //***************************************************************************

   parameter C_S_AXI_ID_WIDTH              = 1;

                                             // Width of all master and slave ID signals.

                                             // # = >= 1.

   parameter C_S_AXI_ADDR_WIDTH            = 27;

                                             // Width of S_AXI_AWADDR, S_AXI_ARADDR, M_AXI_AWADDR and

                                             // M_AXI_ARADDR for all SI/MI slots.

                                             // # = 32.

   parameter C_S_AXI_DATA_WIDTH            = 32;

                                             // Width of WDATA and RDATA on SI slot.

                                             // Must be <= APP_DATA_WIDTH.

                                             // # = 32, 64, 128, 256.

   parameter C_S_AXI_SUPPORTS_NARROW_BURST = 0;

                                             // Indicates whether to instatiate upsizer

                                             // Range: 0, 1





   //***************************************************************************

   // Debug and Internal parameters

   //***************************************************************************

   parameter DEBUG_PORT            = "OFF";

                                     // # = "ON" Enable debug signals/controls.

                                     //   = "OFF" Disable debug signals/controls.

   //***************************************************************************

   // Debug and Internal parameters

   //***************************************************************************

   parameter DRAM_TYPE             = "DDR3";



    



  //**************************************************************************//

  // Local parameters Declarations

  //**************************************************************************//



  localparam real TPROP_DQS          = 0.00;

                                       // Delay for DQS signal during Write Operation

  localparam real TPROP_DQS_RD       = 0.00;

                       // Delay for DQS signal during Read Operation

  localparam real TPROP_PCB_CTRL     = 0.00;

                       // Delay for Address and Ctrl signals

  localparam real TPROP_PCB_DATA     = 0.00;

                       // Delay for data signal during Write operation

  localparam real TPROP_PCB_DATA_RD  = 0.00;

                       // Delay for data signal during Read operation



  localparam MEMORY_WIDTH            = 8;

  localparam NUM_COMP                = DQ_WIDTH/MEMORY_WIDTH;

  localparam ECC_TEST 		   	= "OFF" ;

  localparam ERR_INSERT = (ECC_TEST == "ON") ? "OFF" : ECC ;

  



  localparam real REFCLK_PERIOD = (1000000.0/(2*REFCLK_FREQ));

  localparam RESET_PERIOD = 200000; //in pSec  

  localparam real SYSCLK_PERIOD = tCK;

    

    



  //**************************************************************************//

  // Wire Declarations

  //**************************************************************************//

  reg                                sys_rst_n;

  wire                               sys_rst;





  reg                     sys_clk_i;

  wire                               sys_clk_p;

  wire                               sys_clk_n;

    



  reg clk_ref_i;

  wire                               clk_ref_p;

  wire                               clk_ref_n;

    



  

  wire                               ddr3_reset_n;

  wire [DQ_WIDTH-1:0]                ddr3_dq_fpga;

  wire [DQS_WIDTH-1:0]               ddr3_dqs_p_fpga;

  wire [DQS_WIDTH-1:0]               ddr3_dqs_n_fpga;

  wire [ROW_WIDTH-1:0]               ddr3_addr_fpga;

  wire [3-1:0]              ddr3_ba_fpga;

  wire                               ddr3_ras_n_fpga;

  wire                               ddr3_cas_n_fpga;

  wire                               ddr3_we_n_fpga;

  wire [1-1:0]               ddr3_cke_fpga;

  wire [1-1:0]                ddr3_ck_p_fpga;

  wire [1-1:0]                ddr3_ck_n_fpga;

    

  

  wire                               init_calib_complete;

  wire                               tg_compare_error;

  wire [(CS_WIDTH*1)-1:0] ddr3_cs_n_fpga;

    

  wire [DM_WIDTH-1:0]                ddr3_dm_fpga;

    

  wire [ODT_WIDTH-1:0]               ddr3_odt_fpga;

    

  

  reg [(CS_WIDTH*1)-1:0] ddr3_cs_n_sdram_tmp;

    

  reg [DM_WIDTH-1:0]                 ddr3_dm_sdram_tmp;

    

  reg [ODT_WIDTH-1:0]                ddr3_odt_sdram_tmp;

    



  

  wire [DQ_WIDTH-1:0]                ddr3_dq_sdram;

  reg [ROW_WIDTH-1:0]                ddr3_addr_sdram [0:1];

  reg [3-1:0]               ddr3_ba_sdram [0:1];

  reg                                ddr3_ras_n_sdram;

  reg                                ddr3_cas_n_sdram;

  reg                                ddr3_we_n_sdram;

  wire [(CS_WIDTH*1)-1:0] ddr3_cs_n_sdram;

  wire [ODT_WIDTH-1:0]               ddr3_odt_sdram;

  reg [1-1:0]                ddr3_cke_sdram;

  wire [DM_WIDTH-1:0]                ddr3_dm_sdram;

  wire [DQS_WIDTH-1:0]               ddr3_dqs_p_sdram;

  wire [DQS_WIDTH-1:0]               ddr3_dqs_n_sdram;

  reg [1-1:0]                 ddr3_ck_p_sdram;

  reg [1-1:0]                 ddr3_ck_n_sdram;

  

    



//**************************************************************************//



  //**************************************************************************//

  // Reset Generation

  //**************************************************************************//

  initial begin

    sys_rst_n = 1'b0;

    #RESET_PERIOD

      sys_rst_n = 1'b1;

   end



   assign sys_rst = RST_ACT_LOW ? sys_rst_n : ~sys_rst_n;



  //**************************************************************************//

  // Clock Generation

  //**************************************************************************//



  initial

    sys_clk_i = 1'b0;

  always

    sys_clk_i = #(CLKIN_PERIOD/2.0) ~sys_clk_i;



  assign sys_clk_p = sys_clk_i;

  assign sys_clk_n = ~sys_clk_i;



  initial

    clk_ref_i = 1'b0;

  always

    clk_ref_i = #REFCLK_PERIOD ~clk_ref_i;



  assign clk_ref_p = clk_ref_i;

  assign clk_ref_n = ~clk_ref_i;







  always @( * ) begin

    ddr3_ck_p_sdram      <=  #(TPROP_PCB_CTRL) ddr3_ck_p_fpga;

    ddr3_ck_n_sdram      <=  #(TPROP_PCB_CTRL) ddr3_ck_n_fpga;

    ddr3_addr_sdram[0]   <=  #(TPROP_PCB_CTRL) ddr3_addr_fpga;

    ddr3_addr_sdram[1]   <=  #(TPROP_PCB_CTRL) (CA_MIRROR == "ON") ?

                                                 {ddr3_addr_fpga[ROW_WIDTH-1:9],

                                                  ddr3_addr_fpga[7], ddr3_addr_fpga[8],

                                                  ddr3_addr_fpga[5], ddr3_addr_fpga[6],

                                                  ddr3_addr_fpga[3], ddr3_addr_fpga[4],

                                                  ddr3_addr_fpga[2:0]} :

                                                 ddr3_addr_fpga;

    ddr3_ba_sdram[0]     <=  #(TPROP_PCB_CTRL) ddr3_ba_fpga;

    ddr3_ba_sdram[1]     <=  #(TPROP_PCB_CTRL) (CA_MIRROR == "ON") ?

                                                 {ddr3_ba_fpga[3-1:2],

                                                  ddr3_ba_fpga[0],

                                                  ddr3_ba_fpga[1]} :

                                                 ddr3_ba_fpga;

    ddr3_ras_n_sdram     <=  #(TPROP_PCB_CTRL) ddr3_ras_n_fpga;

    ddr3_cas_n_sdram     <=  #(TPROP_PCB_CTRL) ddr3_cas_n_fpga;

    ddr3_we_n_sdram      <=  #(TPROP_PCB_CTRL) ddr3_we_n_fpga;

    ddr3_cke_sdram       <=  #(TPROP_PCB_CTRL) ddr3_cke_fpga;

  end

    



  always @( * )

    ddr3_cs_n_sdram_tmp   <=  #(TPROP_PCB_CTRL) ddr3_cs_n_fpga;

  assign ddr3_cs_n_sdram =  ddr3_cs_n_sdram_tmp;

    



  always @( * )

    ddr3_dm_sdram_tmp <=  #(TPROP_PCB_DATA) ddr3_dm_fpga;//DM signal generation

  assign ddr3_dm_sdram = ddr3_dm_sdram_tmp;

    



  always @( * )

    ddr3_odt_sdram_tmp  <=  #(TPROP_PCB_CTRL) ddr3_odt_fpga;

  assign ddr3_odt_sdram =  ddr3_odt_sdram_tmp;

    



// Controlling the bi-directional BUS



  genvar dqwd;

  generate

    for (dqwd = 1;dqwd < DQ_WIDTH;dqwd = dqwd+1) begin : dq_delay

      WireDelay #

       (

        .Delay_g    (TPROP_PCB_DATA),

        .Delay_rd   (TPROP_PCB_DATA_RD),

        .ERR_INSERT ("OFF")

       )

      u_delay_dq

       (

        .A             (ddr3_dq_fpga[dqwd]),

        .B             (ddr3_dq_sdram[dqwd]),

        .reset         (sys_rst_n),

        .phy_init_done (init_calib_complete)

       );

    end

          WireDelay #

       (

        .Delay_g    (TPROP_PCB_DATA),

        .Delay_rd   (TPROP_PCB_DATA_RD),

        .ERR_INSERT ("OFF")

       )

      u_delay_dq_0

       (

        .A             (ddr3_dq_fpga[0]),

        .B             (ddr3_dq_sdram[0]),

        .reset         (sys_rst_n),

        .phy_init_done (init_calib_complete)

       );

  endgenerate



  genvar dqswd;

  generate

    for (dqswd = 0;dqswd < DQS_WIDTH;dqswd = dqswd+1) begin : dqs_delay

      WireDelay #

       (

        .Delay_g    (TPROP_DQS),

        .Delay_rd   (TPROP_DQS_RD),

        .ERR_INSERT ("OFF")

       )

      u_delay_dqs_p

       (

        .A             (ddr3_dqs_p_fpga[dqswd]),

        .B             (ddr3_dqs_p_sdram[dqswd]),

        .reset         (sys_rst_n),

        .phy_init_done (init_calib_complete)

       );



      WireDelay #

       (

        .Delay_g    (TPROP_DQS),

        .Delay_rd   (TPROP_DQS_RD),

        .ERR_INSERT ("OFF")

       )

      u_delay_dqs_n

       (

        .A             (ddr3_dqs_n_fpga[dqswd]),

        .B             (ddr3_dqs_n_sdram[dqswd]),

        .reset         (sys_rst_n),

        .phy_init_done (init_calib_complete)

       );

    end

  endgenerate

    



    



  //===========================================================================

  //                         FPGA Memory Controller

  //===========================================================================



  example_top #

    (



     .SIMULATION                (SIMULATION),

     .BEGIN_ADDRESS             (BEGIN_ADDRESS),

     .END_ADDRESS               (END_ADDRESS),

     .PRBS_EADDR_MASK_POS       (PRBS_EADDR_MASK_POS),



     .COL_WIDTH                 (COL_WIDTH),

     .CS_WIDTH                  (CS_WIDTH),

     .DM_WIDTH                  (DM_WIDTH),

    

     .DQ_WIDTH                  (DQ_WIDTH),

     .DQS_CNT_WIDTH             (DQS_CNT_WIDTH),

     .DRAM_WIDTH                (DRAM_WIDTH),

     .ECC_TEST                  (ECC_TEST),

     .RANKS                     (RANKS),

     .ROW_WIDTH                 (ROW_WIDTH),

     .ADDR_WIDTH                (ADDR_WIDTH),

     .BURST_MODE                (BURST_MODE),

     .TCQ                       (TCQ),



     

    .DRAM_TYPE                 (DRAM_TYPE),

    

     

    .nCK_PER_CLK               (nCK_PER_CLK),

    

     

     .C_S_AXI_ID_WIDTH          (C_S_AXI_ID_WIDTH),

     .C_S_AXI_ADDR_WIDTH        (C_S_AXI_ADDR_WIDTH),

     .C_S_AXI_DATA_WIDTH        (C_S_AXI_DATA_WIDTH),

     .C_S_AXI_SUPPORTS_NARROW_BURST (C_S_AXI_SUPPORTS_NARROW_BURST),

    

     .DEBUG_PORT                (DEBUG_PORT),

    

     .RST_ACT_LOW               (RST_ACT_LOW)

    )

   u_ip_top

     (



     .ddr3_dq              (ddr3_dq_fpga),

     .ddr3_dqs_n           (ddr3_dqs_n_fpga),

     .ddr3_dqs_p           (ddr3_dqs_p_fpga),



     .ddr3_addr            (ddr3_addr_fpga),

     .ddr3_ba              (ddr3_ba_fpga),

     .ddr3_ras_n           (ddr3_ras_n_fpga),

     .ddr3_cas_n           (ddr3_cas_n_fpga),

     .ddr3_we_n            (ddr3_we_n_fpga),

     .ddr3_reset_n         (ddr3_reset_n),

     .ddr3_ck_p            (ddr3_ck_p_fpga),

     .ddr3_ck_n            (ddr3_ck_n_fpga),

     .ddr3_cke             (ddr3_cke_fpga),

     .ddr3_cs_n            (ddr3_cs_n_fpga),

    

     .ddr3_dm              (ddr3_dm_fpga),

    

     .ddr3_odt             (ddr3_odt_fpga),

    

     

     .sys_clk_p            (sys_clk_p),

     .sys_clk_n            (sys_clk_n),

    

     .clk_ref_p            (clk_ref_p),

     .clk_ref_n            (clk_ref_n),

    

     .device_temp_i        (12'b0),

    

      .init_calib_complete (init_calib_complete),

      .tg_compare_error    (tg_compare_error),

      .sys_rst             (sys_rst)

     );



  //**************************************************************************//

  // Memory Models instantiations

  //**************************************************************************//



  genvar r,i;

  generate

    for (r = 0; r < CS_WIDTH; r = r + 1) begin: mem_rnk

      for (i = 0; i < NUM_COMP; i = i + 1) begin: gen_mem

        ddr3_model u_comp_ddr3

          (

           .rst_n   (ddr3_reset_n),

           .ck      (ddr3_ck_p_sdram),

           .ck_n    (ddr3_ck_n_sdram),

           .cke     (ddr3_cke_sdram[r]),

           .cs_n    (ddr3_cs_n_sdram[r]),

           .ras_n   (ddr3_ras_n_sdram),

           .cas_n   (ddr3_cas_n_sdram),

           .we_n    (ddr3_we_n_sdram),

           .dm_tdqs (ddr3_dm_sdram[i]),

           .ba      (ddr3_ba_sdram[r]),

           .addr    (ddr3_addr_sdram[r]),

           .dq      (ddr3_dq_sdram[MEMORY_WIDTH*(i+1)-1:MEMORY_WIDTH*(i)]),

           .dqs     (ddr3_dqs_p_sdram[i]),

           .dqs_n   (ddr3_dqs_n_sdram[i]),

           .tdqs_n  (),

           .odt     (ddr3_odt_sdram[r])

           );

      end

    end

  endgenerate

    

    









  //***************************************************************************

  // AXI read/write smoke test (TB-driven)

  //***************************************************************************

  localparam [C_S_AXI_ADDR_WIDTH-1:0] AXI_TEST_ADDR  = 27'h0001000;

  localparam [C_S_AXI_DATA_WIDTH-1:0] AXI_TEST_WDATA = 32'hA5A55A5A;



  reg [C_S_AXI_DATA_WIDTH-1:0] axi_test_rdata;

  reg                          axi_test_fail;



  task axi_master_idle;

  begin

    force u_ip_top.s_axi_awid    = {C_S_AXI_ID_WIDTH{1'b0}};

    force u_ip_top.s_axi_awaddr  = {C_S_AXI_ADDR_WIDTH{1'b0}};

    force u_ip_top.s_axi_awlen   = 8'd0;

    force u_ip_top.s_axi_awsize  = 3'd2;

    force u_ip_top.s_axi_awburst = 2'b01;

    force u_ip_top.s_axi_awlock  = 1'b0;

    force u_ip_top.s_axi_awcache = 4'b0011;

    force u_ip_top.s_axi_awprot  = 3'b000;

    force u_ip_top.s_axi_awvalid = 1'b0;



    force u_ip_top.s_axi_wdata   = {C_S_AXI_DATA_WIDTH{1'b0}};

    force u_ip_top.s_axi_wstrb   = {(C_S_AXI_DATA_WIDTH/8){1'b0}};

    force u_ip_top.s_axi_wlast   = 1'b1;

    force u_ip_top.s_axi_wvalid  = 1'b0;

    force u_ip_top.s_axi_bready  = 1'b0;



    force u_ip_top.s_axi_arid    = {C_S_AXI_ID_WIDTH{1'b0}};

    force u_ip_top.s_axi_araddr  = {C_S_AXI_ADDR_WIDTH{1'b0}};

    force u_ip_top.s_axi_arlen   = 8'd0;

    force u_ip_top.s_axi_arsize  = 3'd2;

    force u_ip_top.s_axi_arburst = 2'b01;

    force u_ip_top.s_axi_arlock  = 1'b0;

    force u_ip_top.s_axi_arcache = 4'b0011;

    force u_ip_top.s_axi_arprot  = 3'b000;

    force u_ip_top.s_axi_arvalid = 1'b0;

    force u_ip_top.s_axi_rready  = 1'b0;

  end

  endtask



  task axi_master_release;

  begin

    release u_ip_top.s_axi_awid;

    release u_ip_top.s_axi_awaddr;

    release u_ip_top.s_axi_awlen;

    release u_ip_top.s_axi_awsize;

    release u_ip_top.s_axi_awburst;

    release u_ip_top.s_axi_awlock;

    release u_ip_top.s_axi_awcache;

    release u_ip_top.s_axi_awprot;

    release u_ip_top.s_axi_awvalid;



    release u_ip_top.s_axi_wdata;

    release u_ip_top.s_axi_wstrb;

    release u_ip_top.s_axi_wlast;

    release u_ip_top.s_axi_wvalid;

    release u_ip_top.s_axi_bready;



    release u_ip_top.s_axi_arid;

    release u_ip_top.s_axi_araddr;

    release u_ip_top.s_axi_arlen;

    release u_ip_top.s_axi_arsize;

    release u_ip_top.s_axi_arburst;

    release u_ip_top.s_axi_arlock;

    release u_ip_top.s_axi_arcache;

    release u_ip_top.s_axi_arprot;

    release u_ip_top.s_axi_arvalid;

    release u_ip_top.s_axi_rready;

  end

  endtask



  task axi_write32;

    input [C_S_AXI_ADDR_WIDTH-1:0] addr;

    input [C_S_AXI_DATA_WIDTH-1:0] data;

  begin

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_awid    = {C_S_AXI_ID_WIDTH{1'b0}};

    force u_ip_top.s_axi_awaddr  = addr;

    force u_ip_top.s_axi_awlen   = 8'd0;

    force u_ip_top.s_axi_awsize  = 3'd2;

    force u_ip_top.s_axi_awburst = 2'b01;

    force u_ip_top.s_axi_awlock  = 1'b0;

    force u_ip_top.s_axi_awcache = 4'b0011;

    force u_ip_top.s_axi_awprot  = 3'b000;

    force u_ip_top.s_axi_awvalid = 1'b1;

    while (!u_ip_top.s_axi_awready) @(posedge u_ip_top.clk);

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_awvalid = 1'b0;



    force u_ip_top.s_axi_wdata   = data;

    force u_ip_top.s_axi_wstrb   = {(C_S_AXI_DATA_WIDTH/8){1'b1}};

    force u_ip_top.s_axi_wlast   = 1'b1;

    force u_ip_top.s_axi_wvalid  = 1'b1;

    while (!u_ip_top.s_axi_wready) @(posedge u_ip_top.clk);

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_wvalid  = 1'b0;



    force u_ip_top.s_axi_bready = 1'b1;

    while (!u_ip_top.s_axi_bvalid) @(posedge u_ip_top.clk);

    if (u_ip_top.s_axi_bresp !== 2'b00) begin

      $display("TEST FAILED: AXI WRITE BRESP=%0h", u_ip_top.s_axi_bresp);

      axi_test_fail = 1'b1;

    end

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_bready = 1'b0;

  end

  endtask



  task axi_read32;

    input  [C_S_AXI_ADDR_WIDTH-1:0] addr;

    output [C_S_AXI_DATA_WIDTH-1:0] data;

  begin

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_arid    = {C_S_AXI_ID_WIDTH{1'b0}};

    force u_ip_top.s_axi_araddr  = addr;

    force u_ip_top.s_axi_arlen   = 8'd0;

    force u_ip_top.s_axi_arsize  = 3'd2;

    force u_ip_top.s_axi_arburst = 2'b01;

    force u_ip_top.s_axi_arlock  = 1'b0;

    force u_ip_top.s_axi_arcache = 4'b0011;

    force u_ip_top.s_axi_arprot  = 3'b000;

    force u_ip_top.s_axi_arvalid = 1'b1;

    while (!u_ip_top.s_axi_arready) @(posedge u_ip_top.clk);

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_arvalid = 1'b0;



    force u_ip_top.s_axi_rready = 1'b1;

    while (!u_ip_top.s_axi_rvalid) @(posedge u_ip_top.clk);

    data = u_ip_top.s_axi_rdata;

    if ((u_ip_top.s_axi_rresp !== 2'b00) || (u_ip_top.s_axi_rlast !== 1'b1)) begin

      $display("TEST FAILED: AXI READ RRESP=%0h RLAST=%0b",

               u_ip_top.s_axi_rresp, u_ip_top.s_axi_rlast);

      axi_test_fail = 1'b1;

    end

    @(posedge u_ip_top.clk);

    force u_ip_top.s_axi_rready = 1'b0;

  end

  endtask



  //***************************************************************************

  // Reporting the test case status

  //***************************************************************************

  initial

  begin : Logging

     axi_test_fail  = 1'b0;

     axi_test_rdata = {C_S_AXI_DATA_WIDTH{1'b0}};



     fork

        begin : run_axi_smoke

           wait (init_calib_complete);

           $display("Calibration Done");



           // Hold matrix control bus inactive so TB owns AXI master signals.

           force u_ip_top.matrix_bus_valid = 1'b0;

           force u_ip_top.matrix_bus_wstrb = 4'h0;



           axi_master_idle();

           axi_write32(AXI_TEST_ADDR, AXI_TEST_WDATA);

           axi_read32 (AXI_TEST_ADDR, axi_test_rdata);



           if (!axi_test_fail && (axi_test_rdata === AXI_TEST_WDATA)) begin

              $display("TEST PASSED: AXI RW addr=%h write=%h read=%h",

                       AXI_TEST_ADDR, AXI_TEST_WDATA, axi_test_rdata);

           end else begin

              $display("TEST FAILED: AXI RW addr=%h write=%h read=%h",

                       AXI_TEST_ADDR, AXI_TEST_WDATA, axi_test_rdata);

           end



           axi_master_release();

           release u_ip_top.matrix_bus_valid;

           release u_ip_top.matrix_bus_wstrb;



           disable test_timeout;

           $finish;

        end



        begin : test_timeout

           if (SIM_BYPASS_INIT_CAL == "SIM_INIT_CAL_FULL")

             #2500000000.0;

           else

             #1000000000.0;



           if (!init_calib_complete) begin

              $display("TEST FAILED: INITIALIZATION DID NOT COMPLETE");

           end

           else begin

              $display("TEST FAILED: AXI RW TEST TIMEOUT");

           end



           disable run_axi_smoke;

           $finish;

        end

     join

  end

endmodule




