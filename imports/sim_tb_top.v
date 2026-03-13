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

        ddr3_model #(
          .DEBUG(0)
        ) u_comp_ddr3

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
  // Matrix multi-case end-to-end test
  //   flow: preload A/B -> start matrix -> readback C -> compare
  //***************************************************************************
  localparam [C_S_AXI_ADDR_WIDTH-1:0] AXI_BASE_A = 27'd0;       // byte addr
  localparam [C_S_AXI_ADDR_WIDTH-1:0] AXI_BASE_B = 27'd4096;    // byte addr
  localparam [C_S_AXI_ADDR_WIDTH-1:0] AXI_BASE_C = 27'd8192;    // byte addr

  localparam [31:0] MATRIX_WORD_BASE_A = 32'd0;
  localparam [31:0] MATRIX_WORD_BASE_B = 32'd1024;
  localparam [31:0] MATRIX_WORD_BASE_C = 32'd2048;

  localparam integer NUM_CASES = 8;
  localparam integer CASE_DONE_TIMEOUT_POLLS = 200000;
  localparam integer CASE_STATUS_PRINT_EVERY = 20000;
  localparam integer PRINT_CASE_MATRIX_VALUES = 1;
  localparam integer CASE_DONE_TIMEOUT_CYCLES = 2000000;

  localparam [2:0] CORE_S_IDLE    = 3'd0;
  localparam [2:0] CORE_S_LOAD_A  = 3'd1;
  localparam [2:0] CORE_S_LOAD_B  = 3'd2;
  localparam [2:0] CORE_S_CLEAR   = 3'd3;
  localparam [2:0] CORE_S_COMPUTE = 3'd4;

  localparam [2:0] TILE_TS_IDLE       = 3'd0;
  localparam [2:0] TILE_TS_INIT_TILE  = 3'd1;
  localparam [2:0] TILE_TS_START_CORE = 3'd2;
  localparam [2:0] TILE_TS_WAIT_CORE  = 3'd3;
  localparam [2:0] TILE_TS_ACCUM      = 3'd4;
  localparam [2:0] TILE_TS_WB_START   = 3'd5;
  localparam [2:0] TILE_TS_WB_WAIT    = 3'd6;
  localparam [2:0] TILE_TS_DONE       = 3'd7;

  reg [C_S_AXI_DATA_WIDTH-1:0] axi_test_rdata;
  reg                          axi_test_fail;

  time    case_tb_preload_time   [0:NUM_CASES-1];
  time    case_cfg_time          [0:NUM_CASES-1];
  time    case_core_run_time     [0:NUM_CASES-1];
  time    case_tb_readback_time  [0:NUM_CASES-1];
  integer case_core_fetch_cycles [0:NUM_CASES-1];
  integer case_core_compute_cycles [0:NUM_CASES-1];
  integer case_core_writeback_cycles [0:NUM_CASES-1];
  integer case_core_move_cycles  [0:NUM_CASES-1];

  // -------------------------
  // Test-pattern generators
  // -------------------------
  function [7:0] gen_a_elem;
    input integer tc_idx;
    input integer row_idx;
    input integer k_idx;
    integer t;
  begin
    case (tc_idx)
      0: t = (row_idx == k_idx) ? 1 : 0;           // Identity
      1: t = 0;                                     // All zeros
      2: t = row_idx - k_idx;                       // Signed pattern
      3: t = (row_idx * 2) - k_idx - 1;             // Rectangular pattern
      4: t = 13;                                    // 1x1 scalar
      5: t = row_idx - 3;                           // K=1 pattern
      6: t = (row_idx * 2) - k_idx + 1;             // N=1 pattern
      7: t = ((row_idx * 5) + (k_idx * 3) + 11) % 17 - 8; // Mixed signed
      default: t = 0;
    endcase
    gen_a_elem = t[7:0];
  end
  endfunction

  function [7:0] gen_b_elem;
    input integer tc_idx;
    input integer k_idx;
    input integer col_idx;
    integer t;
  begin
    case (tc_idx)
      0: t = k_idx * 8 + col_idx + 1;               // 1..64
      1: t = (k_idx * 11 + col_idx * 7 + 3) % 101;  // Positive pseudo pattern
      2: t = k_idx - (2 * col_idx);                 // Signed pattern
      3: t = (k_idx * 3) + col_idx - 5;             // Rectangular pattern
      4: t = -7;                                    // 1x1 scalar
      5: t = col_idx + 1;                           // K=1 pattern
      6: t = (k_idx % 2) ? -2 : 3;                  // N=1 pattern
      7: t = ((k_idx * 7) + (col_idx * 2) + 3) % 19 - 9; // Mixed signed
      default: t = 0;
    endcase
    gen_b_elem = t[7:0];
  end
  endfunction

  function [31:0] calc_expected_elem;
    input integer tc_idx;
    input integer row_idx;
    input integer col_idx;
    input integer k_dim;
    integer kk;
    integer sum;
    integer a_s;
    integer b_s;
    reg [7:0] a8;
    reg [7:0] b8;
  begin
    sum = 0;
    for (kk = 0; kk < k_dim; kk = kk + 1) begin
      a8  = gen_a_elem(tc_idx, row_idx, kk);
      b8  = gen_b_elem(tc_idx, kk, col_idx);
      a_s = $signed(a8);
      b_s = $signed(b8);
      sum = sum + (a_s * b_s);
    end
    calc_expected_elem = sum[31:0];
  end
  endfunction

  // -------------------------
  // AXI helpers (to MIG AXI slave)
  // -------------------------
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

  // -------------------------
  // Matrix wrapper cfg-bus helpers
  // -------------------------
  task matrix_cfg_idle;
  begin
    force u_ip_top.matrix_bus_valid = 1'b0;
    force u_ip_top.matrix_bus_addr  = 32'd0;
    force u_ip_top.matrix_bus_wdata = 32'd0;
    force u_ip_top.matrix_bus_wstrb = 4'h0;
  end
  endtask

  task matrix_cfg_release;
  begin
    release u_ip_top.matrix_bus_valid;
    release u_ip_top.matrix_bus_addr;
    release u_ip_top.matrix_bus_wdata;
    release u_ip_top.matrix_bus_wstrb;
  end
  endtask

  task matrix_cfg_write;
    input [31:0] reg_addr;
    input [31:0] reg_data;
  begin
    @(posedge u_ip_top.clk);
    while (u_ip_top.matrix_bus_ready) @(posedge u_ip_top.clk);
    force u_ip_top.matrix_bus_addr  = reg_addr;
    force u_ip_top.matrix_bus_wdata = reg_data;
    force u_ip_top.matrix_bus_wstrb = 4'hF;
    force u_ip_top.matrix_bus_valid = 1'b1;
    while (!u_ip_top.matrix_bus_ready) @(posedge u_ip_top.clk);
    @(posedge u_ip_top.clk);
    force u_ip_top.matrix_bus_valid = 1'b0;
  end
  endtask

  task matrix_cfg_read;
    input  [31:0] reg_addr;
    output [31:0] reg_data;
  begin
    @(posedge u_ip_top.clk);
    while (u_ip_top.matrix_bus_ready) @(posedge u_ip_top.clk);
    force u_ip_top.matrix_bus_addr  = reg_addr;
    force u_ip_top.matrix_bus_wdata = 32'd0;
    force u_ip_top.matrix_bus_wstrb = 4'h0;
    force u_ip_top.matrix_bus_valid = 1'b1;
    while (!u_ip_top.matrix_bus_ready) @(posedge u_ip_top.clk);
    reg_data = u_ip_top.matrix_bus_rdata;
    @(posedge u_ip_top.clk);
    force u_ip_top.matrix_bus_valid = 1'b0;
  end
  endtask

  task get_case_dims;
    input  integer tc_idx;
    output integer m_dim;
    output integer k_dim;
    output integer n_dim;
  begin
    case (tc_idx)
      0: begin m_dim = 8; k_dim = 8; n_dim = 8; end
      1: begin m_dim = 8; k_dim = 8; n_dim = 8; end
      2: begin m_dim = 8; k_dim = 8; n_dim = 8; end
      3: begin m_dim = 5; k_dim = 3; n_dim = 7; end
      4: begin m_dim = 1; k_dim = 1; n_dim = 1; end
      5: begin m_dim = 8; k_dim = 1; n_dim = 8; end
      6: begin m_dim = 8; k_dim = 8; n_dim = 1; end
      7: begin m_dim = 3; k_dim = 8; n_dim = 5; end
      default: begin m_dim = 8; k_dim = 8; n_dim = 8; end
    endcase
  end
  endtask

  task preload_case_data;
    input integer tc_idx;
    input integer m_dim;
    input integer k_dim;
    input integer n_dim;
    integer r;
    integer w;
    integer b;
    integer col_idx;
    integer k_words;
    integer n_words;
    reg [31:0] wr_word;
    reg [7:0]  elem;
  begin
    k_words = (k_dim + 3) / 4;
    n_words = (n_dim + 3) / 4;

    axi_master_idle();

    // A preload
    for (r = 0; r < m_dim; r = r + 1) begin
      for (w = 0; w < k_words; w = w + 1) begin
        wr_word = 32'd0;
        for (b = 0; b < 4; b = b + 1) begin
          col_idx = w*4 + b;
          if (col_idx < k_dim) elem = gen_a_elem(tc_idx, r, col_idx);
          else                 elem = 8'd0;
          wr_word = wr_word | ({24'd0, elem} << (8*b));
        end
        axi_write32(AXI_BASE_A + ((r*k_words + w) << 2), wr_word);
      end
    end

    // B preload
    for (r = 0; r < k_dim; r = r + 1) begin
      for (w = 0; w < n_words; w = w + 1) begin
        wr_word = 32'd0;
        for (b = 0; b < 4; b = b + 1) begin
          col_idx = w*4 + b;
          if (col_idx < n_dim) elem = gen_b_elem(tc_idx, r, col_idx);
          else                 elem = 8'd0;
          wr_word = wr_word | ({24'd0, elem} << (8*b));
        end
        axi_write32(AXI_BASE_B + ((r*n_words + w) << 2), wr_word);
      end
    end

    // Clear C region for this case footprint
    for (r = 0; r < m_dim; r = r + 1) begin
      for (col_idx = 0; col_idx < n_dim; col_idx = col_idx + 1) begin
        axi_write32(AXI_BASE_C + (((r*n_dim + col_idx) << 2)), 32'd0);
      end
    end

    axi_master_release();
  end
  endtask

  task run_case;
    input integer tc_idx;
    input integer m_dim;
    input integer k_dim;
    input integer n_dim;
    output time cfg_elapsed;
    output time core_run_elapsed;
    output time readback_elapsed;
    output integer fetch_cycles;
    output integer compute_cycles;
    output integer writeback_cycles;
    integer r;
    integer col_idx;
    integer poll_count;
    integer timeout_cycles;
    integer seen_done_clear;
    integer seen_busy;
    integer mismatch_count;
    reg [31:0] expected_c;
    reg [31:0] status;
    reg [31:0] status_prev;
    reg [31:0] cfg_a;
    reg [31:0] cfg_b;
    reg [31:0] cfg_c;
    reg [31:0] cfg_m;
    reg [31:0] cfg_k;
    reg [31:0] cfg_n;
    reg [2:0]  core_state;
    reg [2:0]  tile_state;
    time cfg_start_time;
    time core_run_start_time;
    time readback_start_time;
  begin
    $display("CASE%0d start M=%0d K=%0d N=%0d", tc_idx, m_dim, k_dim, n_dim);
    cfg_elapsed      = 0;
    core_run_elapsed = 0;
    readback_elapsed = 0;
    fetch_cycles     = 0;
    compute_cycles   = 0;
    writeback_cycles = 0;

    // Program matrix wrapper registers (word addresses and dims).
    cfg_start_time = $time;
    matrix_cfg_write(32'h0000_0000, MATRIX_WORD_BASE_A); // reg_addr_a
    matrix_cfg_write(32'h0000_0004, MATRIX_WORD_BASE_B); // reg_addr_b
    matrix_cfg_write(32'h0000_0008, MATRIX_WORD_BASE_C); // reg_addr_c
    matrix_cfg_write(32'h0000_000C, m_dim[31:0]);        // reg_m_num
    matrix_cfg_write(32'h0000_0010, k_dim[31:0]);        // reg_k_num
    matrix_cfg_write(32'h0000_0014, n_dim[31:0]);        // reg_n_num

    // Read back config regs to ensure write handshakes really landed.
    matrix_cfg_read(32'h0000_0000, cfg_a);
    matrix_cfg_read(32'h0000_0004, cfg_b);
    matrix_cfg_read(32'h0000_0008, cfg_c);
    matrix_cfg_read(32'h0000_000C, cfg_m);
    matrix_cfg_read(32'h0000_0010, cfg_k);
    matrix_cfg_read(32'h0000_0014, cfg_n);
    cfg_elapsed = $time - cfg_start_time;
    $display("CASE%0d cfg readback: A=%08h B=%08h C=%08h M=%0d K=%0d N=%0d",
             tc_idx, cfg_a, cfg_b, cfg_c, cfg_m, cfg_k, cfg_n);

    if ((cfg_a !== MATRIX_WORD_BASE_A) ||
        (cfg_b !== MATRIX_WORD_BASE_B) ||
        (cfg_c !== MATRIX_WORD_BASE_C) ||
        (cfg_m !== m_dim[31:0])       ||
        (cfg_k !== k_dim[31:0])       ||
        (cfg_n !== n_dim[31:0])) begin
      $display("CASE%0d TEST FAILED: CFG readback mismatch", tc_idx);
      axi_test_fail = 1'b1;
      disable run_case;
    end

    // Start run.
    core_run_start_time = $time;
    matrix_cfg_write(32'h0000_001C, 32'h0000_0001);      // start

    // Measure core-side fetch / compute / writeback time by observing
    // the internal tile/core FSMs cycle by cycle.
    status = 32'd0;
    status_prev = 32'hFFFF_FFFF;
    poll_count  = 0;
    timeout_cycles = 0;
    seen_done_clear = 0;
    seen_busy       = 0;
    while ((!u_ip_top.u_matrix_top_wrapper.sys_done) &&
           (timeout_cycles < CASE_DONE_TIMEOUT_CYCLES)) begin
      @(posedge u_ip_top.clk);
      timeout_cycles = timeout_cycles + 1;

      core_state = u_ip_top.u_matrix_top_wrapper.u_core.u_core.state;
      tile_state = u_ip_top.u_matrix_top_wrapper.u_core.t_state;

      if ((core_state == CORE_S_LOAD_A) || (core_state == CORE_S_LOAD_B))
        fetch_cycles = fetch_cycles + 1;
      if (core_state == CORE_S_COMPUTE)
        compute_cycles = compute_cycles + 1;
      if ((tile_state == TILE_TS_WB_START) || (tile_state == TILE_TS_WB_WAIT))
        writeback_cycles = writeback_cycles + 1;

      if (u_ip_top.u_matrix_top_wrapper.sys_busy)
        seen_busy = 1;

      if ((timeout_cycles % CASE_STATUS_PRINT_EVERY) == 0) begin
        $display("CASE%0d waiting core done: tile_state=%0d core_state=%0d busy=%0b cycle=%0d t=%0t",
                 tc_idx, tile_state, core_state, u_ip_top.u_matrix_top_wrapper.sys_busy,
                 timeout_cycles, $time);
      end
    end

    core_run_elapsed = $time - core_run_start_time;

    if (timeout_cycles >= CASE_DONE_TIMEOUT_CYCLES) begin
      $display("CASE%0d TIMEOUT waiting core done: busy=%0b cycle=%0d t=%0t",
               tc_idx, u_ip_top.u_matrix_top_wrapper.sys_busy, timeout_cycles, $time);
      axi_test_fail = 1'b1;
      disable run_case;
    end

    // Read status reg 0x20 after completion: bit[1]=done_latched, bit[0]=busy
    matrix_cfg_read(32'h0000_0020, status);
    poll_count = poll_count + 1;
    if (!status[1]) seen_done_clear = 1;
    if (status[0])  seen_busy       = 1;

    if (status !== status_prev) begin
      $display("CASE%0d status change: status=%08h busy=%0b done=%0b poll=%0d t=%0t",
               tc_idx, status, status[0], status[1], poll_count, $time);
      status_prev = status;
    end

    if (!status[1]) begin
      $display("CASE%0d TEST FAILED: done_latched not observed after core completion, status=%08h",
               tc_idx, status);
      axi_test_fail = 1'b1;
      disable run_case;
    end

    if (!seen_busy) begin
      $display("CASE%0d WARNING: busy was never observed high (very fast or start issue)",
               tc_idx);
    end

    $display("CASE%0d matrix done: core_run=%0t fetch_cycles=%0d compute_cycles=%0d writeback_cycles=%0d move_cycles=%0d",
             tc_idx, core_run_elapsed, fetch_cycles, compute_cycles, writeback_cycles,
             (fetch_cycles + writeback_cycles));

    // Readback C and compare
    mismatch_count = 0;
    if (PRINT_CASE_MATRIX_VALUES != 0)
      $display("CASE%0d C compare dump begin (per-row, format: exp/got)", tc_idx);
    readback_start_time = $time;
    axi_master_idle();
    for (r = 0; r < m_dim; r = r + 1) begin
      for (col_idx = 0; col_idx < n_dim; col_idx = col_idx + 1) begin
        axi_read32(AXI_BASE_C + (((r*n_dim + col_idx) << 2)), axi_test_rdata);
        expected_c = calc_expected_elem(tc_idx, r, col_idx, k_dim);
        if (PRINT_CASE_MATRIX_VALUES != 0) begin
          if (col_idx == 0)
            $write("CASE%0d C row %0d : ", tc_idx, r);
          $write("%0d/%0d", $signed(expected_c), $signed(axi_test_rdata));
          if (col_idx == (n_dim - 1))
            $display("");
          else
            $write(" ");
        end
        if (axi_test_rdata !== expected_c) begin
          if (mismatch_count < 8) begin
            $display("CASE%0d MISMATCH r=%0d c=%0d exp=%h got=%h",
                     tc_idx, r, col_idx, expected_c, axi_test_rdata);
          end
          mismatch_count = mismatch_count + 1;
          axi_test_fail  = 1'b1;
        end
      end
    end
    axi_master_release();
    readback_elapsed = $time - readback_start_time;
    if (PRINT_CASE_MATRIX_VALUES != 0)
      $display("CASE%0d C compare dump end", tc_idx);

    if (mismatch_count == 0)
      $display("CASE%0d PASSED: cfg=%0t tb_readback=%0t", tc_idx, cfg_elapsed, readback_elapsed);
    else
      $display("CASE%0d FAILED mismatch_count=%0d", tc_idx, mismatch_count);
  end
  endtask

  //***************************************************************************
  // Top-level test flow
  //***************************************************************************
  initial
  begin : Logging
     integer tc;
     integer m_dim;
     integer k_dim;
     integer n_dim;
     integer sum_fetch_cycles;
     integer sum_compute_cycles;
     integer sum_writeback_cycles;
     integer sum_move_cycles;
     time    sum_tb_preload_time;
     time    sum_cfg_time;
     time    sum_core_run_time;
     time    sum_tb_readback_time;
     time    preload_start_time;
     time    preload_elapsed;

     axi_test_fail  = 1'b0;
     axi_test_rdata = {C_S_AXI_DATA_WIDTH{1'b0}};
     sum_fetch_cycles   = 0;
     sum_compute_cycles = 0;
     sum_writeback_cycles = 0;
     sum_move_cycles    = 0;
     sum_tb_preload_time = 0;
     sum_cfg_time        = 0;
     sum_core_run_time   = 0;
     sum_tb_readback_time = 0;

     fork
        begin : run_matrix_multicase
           wait (init_calib_complete);
           $display("Calibration Done");

           // Freeze example_top's built-in cfg FSM in IDLE;
           // TB will drive matrix bus for each case.
           force u_ip_top.matrix_cfg_state = 4'd0;
           matrix_cfg_idle();

           for (tc = 0; tc < NUM_CASES; tc = tc + 1) begin
             get_case_dims(tc, m_dim, k_dim, n_dim);
             preload_start_time = $time;
             preload_case_data(tc, m_dim, k_dim, n_dim);
             preload_elapsed = $time - preload_start_time;
             case_tb_preload_time[tc] = preload_elapsed;
             $display("CASE%0d preload done: A@%h B@%h C@%h", tc, AXI_BASE_A, AXI_BASE_B, AXI_BASE_C);
             run_case(tc, m_dim, k_dim, n_dim,
                      case_cfg_time[tc], case_core_run_time[tc], case_tb_readback_time[tc],
                      case_core_fetch_cycles[tc], case_core_compute_cycles[tc],
                      case_core_writeback_cycles[tc]);
             case_core_move_cycles[tc] = case_core_fetch_cycles[tc] + case_core_writeback_cycles[tc];

             sum_tb_preload_time = sum_tb_preload_time + case_tb_preload_time[tc];
             sum_cfg_time        = sum_cfg_time + case_cfg_time[tc];
             sum_core_run_time   = sum_core_run_time + case_core_run_time[tc];
             sum_tb_readback_time = sum_tb_readback_time + case_tb_readback_time[tc];
             sum_fetch_cycles    = sum_fetch_cycles + case_core_fetch_cycles[tc];
             sum_compute_cycles  = sum_compute_cycles + case_core_compute_cycles[tc];
             sum_writeback_cycles = sum_writeback_cycles + case_core_writeback_cycles[tc];
             sum_move_cycles     = sum_move_cycles + case_core_move_cycles[tc];

             $display("CASE%0d timing summary: tb_preload=%0t cfg=%0t core_run=%0t tb_readback=%0t fetch_cycles=%0d compute_cycles=%0d writeback_cycles=%0d move/compute=%0f",
                      tc,
                      case_tb_preload_time[tc],
                      case_cfg_time[tc],
                      case_core_run_time[tc],
                      case_tb_readback_time[tc],
                      case_core_fetch_cycles[tc],
                      case_core_compute_cycles[tc],
                      case_core_writeback_cycles[tc],
                      (case_core_compute_cycles[tc] != 0) ?
                      ((1.0 * case_core_move_cycles[tc]) / case_core_compute_cycles[tc]) : 0.0);
           end

           $display("MATRIX TIMING TOTAL: tb_preload=%0t cfg=%0t core_run=%0t tb_readback=%0t",
                    sum_tb_preload_time, sum_cfg_time, sum_core_run_time, sum_tb_readback_time);
           $display("MATRIX TIMING TOTAL CYCLES: fetch=%0d compute=%0d writeback=%0d move=%0d move/compute=%0f",
                    sum_fetch_cycles, sum_compute_cycles, sum_writeback_cycles, sum_move_cycles,
                    (sum_compute_cycles != 0) ? ((1.0 * sum_move_cycles) / sum_compute_cycles) : 0.0);

           if (!axi_test_fail)
             $display("TEST PASSED: MATRIX MULTI-CASE (%0d cases)", NUM_CASES);
           else
             $display("TEST FAILED: MATRIX MULTI-CASE");

           matrix_cfg_release();
           release u_ip_top.matrix_cfg_state;

           disable test_timeout;
           $finish;
        end

        begin : test_timeout
           if (SIM_BYPASS_INIT_CAL == "SIM_INIT_CAL_FULL")
             #2500000000.0;
           else
             #1000000000.0;

           if (!init_calib_complete)
             $display("TEST FAILED: INITIALIZATION DID NOT COMPLETE");
           else
             $display("TEST FAILED: MATRIX MULTI-CASE TIMEOUT");

           disable run_matrix_multicase;
           $finish;
        end
     join
  end
endmodule
