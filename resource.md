OS 8\*8:

## Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 21:32:39 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 15466 | 0 | 0 | 134600 | 11.49 |
| LUT as Logic | 15466 | 0 | 0 | 134600 | 11.49 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 10855 | 0 | 0 | 269200 | 4.03 |
| Register as Flip Flop | 10855 | 0 | 0 | 269200 | 4.03 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 377 | 0 | 0 | 67300 | 0.56 |
| F8 Muxes | 76 | 0 | 0 | 33650 | 0.23 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 7 | Yes | - | Set |
| 10822 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 25 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 7 | 0 | 0 | 740 | 0.95 |
| DSP48E1 only | 7 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDCE | 10822 | Flop & Latch |
| LUT2 | 7437 | LUT |
| LUT4 | 4555 | LUT |
| LUT6 | 3651 | LUT |
| CARRY4 | 1888 | CarryLogic |
| LUT5 | 1632 | LUT |
| LUT3 | 734 | LUT |
| MUXF7 | 377 | MuxFx |
| LUT1 | 87 | LUT |
| MUXF8 | 76 | MuxFx |
| FDRE | 25 | Flop & Latch |
| FDPE | 7 | Flop & Latch |
| DSP48E1 | 7 | Block Arithmetic |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

os 16\*16:

## Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 21:40:48 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 60333 | 0 | 0 | 134600 | 44.82 |
| LUT as Logic | 60333 | 0 | 0 | 134600 | 44.82 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 41739 | 0 | 0 | 269200 | 15.50 |
| Register as Flip Flop | 41739 | 0 | 0 | 269200 | 15.50 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 596 | 0 | 0 | 67300 | 0.89 |
| F8 Muxes | 64 | 0 | 0 | 33650 | 0.19 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 7 | Yes | - | Set |
| 41706 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 25 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 7 | 0 | 0 | 740 | 0.95 |
| DSP48E1 only | 7 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDCE | 41706 | Flop & Latch |
| LUT2 | 29775 | LUT |
| LUT5 | 14447 | LUT |
| LUT6 | 13890 | LUT |
| LUT4 | 8155 | LUT |
| CARRY4 | 7279 | CarryLogic |
| LUT3 | 3305 | LUT |
| MUXF7 | 596 | MuxFx |
| LUT1 | 269 | LUT |
| MUXF8 | 64 | MuxFx |
| FDRE | 25 | Flop & Latch |
| FDPE | 7 | Flop & Latch |
| DSP48E1 | 7 | Block Arithmetic |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

os 4\*4:

## Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 22:01:28 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+------+-------+------------+-----------+-------+
| Slice LUTs\* | 4451 | 0 | 0 | 134600 | 3.31 |
| LUT as Logic | 4451 | 0 | 0 | 134600 | 3.31 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 3050 | 0 | 0 | 269200 | 1.13 |
| Register as Flip Flop | 3050 | 0 | 0 | 269200 | 1.13 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 41 | 0 | 0 | 67300 | 0.06 |
| F8 Muxes | 0 | 0 | 0 | 33650 | 0.00 |
+-------------------------+------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 7 | Yes | - | Set |
| 3017 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 25 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 5 | 0 | 0 | 740 | 0.68 |
| DSP48E1 only | 5 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+------+---------------------+
| Ref Name | Used | Functional Category |
+----------+------+---------------------+
| FDCE | 3017 | Flop & Latch |
| LUT2 | 2271 | LUT |
| LUT4 | 1285 | LUT |
| LUT6 | 1023 | LUT |
| CARRY4 | 542 | CarryLogic |
| LUT5 | 357 | LUT |
| LUT3 | 224 | LUT |
| MUXF7 | 41 | MuxFx |
| LUT1 | 28 | LUT |
| FDRE | 25 | Flop & Latch |
| FDPE | 7 | Flop & Latch |
| DSP48E1 | 5 | Block Arithmetic |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

ws 8\*8:
Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

---

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 23:04:30 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 50817 | 0 | 0 | 134600 | 37.75 |
| LUT as Logic | 50817 | 0 | 0 | 134600 | 37.75 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 73465 | 0 | 0 | 269200 | 27.29 |
| Register as Flip Flop | 73465 | 0 | 0 | 269200 | 27.29 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 16768 | 0 | 0 | 67300 | 24.92 |
| F8 Muxes | 68 | 0 | 0 | 33650 | 0.20 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 6 | Yes | - | Set |
| 7900 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 65558 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 7 | 0 | 0 | 740 | 0.95 |
| DSP48E1 only | 7 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDRE | 65558 | Flop & Latch |
| LUT6 | 40566 | LUT |
| MUXF7 | 16768 | MuxFx |
| FDCE | 7900 | Flop & Latch |
| LUT3 | 6178 | LUT |
| LUT2 | 5687 | LUT |
| LUT4 | 2295 | LUT |
| CARRY4 | 1885 | CarryLogic |
| LUT5 | 712 | LUT |
| MUXF8 | 68 | MuxFx |
| LUT1 | 10 | LUT |
| DSP48E1 | 7 | Block Arithmetic |
| FDPE | 6 | Flop & Latch |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

ws 4\*4:
Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

---

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 23:09:35 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 13545 | 0 | 0 | 134600 | 10.06 |
| LUT as Logic | 13545 | 0 | 0 | 134600 | 10.06 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 18863 | 0 | 0 | 269200 | 7.01 |
| Register as Flip Flop | 18863 | 0 | 0 | 269200 | 7.01 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 4129 | 0 | 0 | 67300 | 6.14 |
| F8 Muxes | 0 | 0 | 0 | 33650 | 0.00 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 6 | Yes | - | Set |
| 2450 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 16406 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 5 | 0 | 0 | 740 | 0.68 |
| DSP48E1 only | 5 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDRE | 16406 | Flop & Latch |
| LUT6 | 10100 | LUT |
| MUXF7 | 4129 | MuxFx |
| FDCE | 2450 | Flop & Latch |
| LUT2 | 1799 | LUT |
| LUT3 | 1343 | LUT |
| LUT4 | 701 | LUT |
| LUT5 | 639 | LUT |
| CARRY4 | 543 | CarryLogic |
| LUT1 | 10 | LUT |
| FDPE | 6 | Flop & Latch |
| DSP48E1 | 5 | Block Arithmetic |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

ws 16\*16:
Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

---

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 23:43:13 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+--------+-------+------------+-----------+--------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+--------+-------+------------+-----------+--------+
| Slice LUTs\* | 185279 | 0 | 0 | 134600 | 137.65 |
| LUT as Logic | 185279 | 0 | 0 | 134600 | 137.65 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 292262 | 0 | 0 | 269200 | 108.57 |
| Register as Flip Flop | 292262 | 0 | 0 | 269200 | 108.57 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 65984 | 0 | 0 | 67300 | 98.04 |
| F8 Muxes | 16543 | 0 | 0 | 33650 | 49.16 |
+-------------------------+--------+-------+------------+-----------+--------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+--------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+--------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 6 | Yes | - | Set |
| 30089 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 262166 | Yes | Reset | - |
+--------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 7 | 0 | 0 | 740 | 0.95 |
| DSP48E1 only | 7 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+--------+---------------------+
| Ref Name | Used | Functional Category |
+----------+--------+---------------------+
| FDRE | 262166 | Flop & Latch |
| LUT6 | 152550 | LUT |
| MUXF7 | 65984 | MuxFx |
| FDCE | 30089 | Flop & Latch |
| LUT2 | 16781 | LUT |
| MUXF8 | 16543 | MuxFx |
| LUT3 | 13595 | LUT |
| LUT5 | 11646 | LUT |
| LUT4 | 10083 | LUT |
| CARRY4 | 7289 | CarryLogic |
| LUT1 | 7 | LUT |
| DSP48E1 | 7 | Block Arithmetic |
| FDPE | 6 | Flop & Latch |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+--------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

os_pp 8*8:
os_pp 4*4:
os_pp 16\*16:

ws_pp 8*8:
ws_pp 4*4:
ws_pp 16\*16:

rsa_ws 8\*8:
Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

---

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 23:54:47 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 47728 | 0 | 0 | 134600 | 35.46 |
| LUT as Logic | 47728 | 0 | 0 | 134600 | 35.46 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 73502 | 0 | 0 | 269200 | 27.30 |
| Register as Flip Flop | 73502 | 0 | 0 | 269200 | 27.30 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 16769 | 0 | 0 | 67300 | 24.92 |
| F8 Muxes | 4224 | 0 | 0 | 33650 | 12.55 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 6 | Yes | - | Set |
| 7934 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 65561 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 7 | 0 | 0 | 740 | 0.95 |
| DSP48E1 only | 7 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDRE | 65561 | Flop & Latch |
| LUT6 | 39041 | LUT |
| MUXF7 | 16769 | MuxFx |
| FDCE | 7934 | Flop & Latch |
| MUXF8 | 4224 | MuxFx |
| LUT2 | 4165 | LUT |
| LUT5 | 3548 | LUT |
| LUT3 | 2625 | LUT |
| LUT4 | 2349 | LUT |
| CARRY4 | 1911 | CarryLogic |
| LUT1 | 10 | LUT |
| DSP48E1 | 7 | Block Arithmetic |
| FDPE | 6 | Flop & Latch |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

rsa_ws 4\*4:
Copyright 1986-2022 Xilinx, Inc. All Rights Reserved. Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.

---

| Tool Version : Vivado v.2023.2 (win64) Build 4029153 Fri Oct 13 20:14:34 MDT 2023
| Date : Mon Mar 23 23:59:38 2026
| Host : ROG-Zephyrus16 running 64-bit major release (build 9200)
| Command : report_utilization -file example_top_utilization_synth.rpt -pb example_top_utilization_synth.pb
| Design : example_top
| Device : xc7a200tsbv484-1
| Speed File : -1
| Design State : Synthesized

---

Utilization Design Information

## Table of Contents

1. Slice Logic
   1.1 Summary of Registers by Type
2. Memory
3. DSP
4. IO and GT Specific
5. Clocking
6. Specific Feature
7. Primitives
8. Black Boxes
9. Instantiated Netlists

10. Slice Logic

---

+-------------------------+-------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------------------+-------+-------+------------+-----------+-------+
| Slice LUTs\* | 12578 | 0 | 0 | 134600 | 9.34 |
| LUT as Logic | 12578 | 0 | 0 | 134600 | 9.34 |
| LUT as Memory | 0 | 0 | 0 | 46200 | 0.00 |
| Slice Registers | 18891 | 0 | 0 | 269200 | 7.02 |
| Register as Flip Flop | 18891 | 0 | 0 | 269200 | 7.02 |
| Register as Latch | 0 | 0 | 0 | 269200 | 0.00 |
| F7 Muxes | 4130 | 0 | 0 | 67300 | 6.14 |
| F8 Muxes | 1024 | 0 | 0 | 33650 | 3.04 |
+-------------------------+-------+-------+------------+-----------+-------+

- Warning! The Final LUT count, after physical optimizations and full implementation, is typically lower. Run opt_design after synthesis, if not already completed, for a more realistic count.
  Warning! LUT value is adjusted to account for LUT combining.

  1.1 Summary of Registers by Type

---

+-------+--------------+-------------+--------------+
| Total | Clock Enable | Synchronous | Asynchronous |
+-------+--------------+-------------+--------------+
| 0 | _ | - | - |
| 0 | _ | - | Set |
| 0 | _ | - | Reset |
| 0 | _ | Set | - |
| 0 | \_ | Reset | - |
| 0 | Yes | - | - |
| 6 | Yes | - | Set |
| 2475 | Yes | - | Reset |
| 1 | Yes | Set | - |
| 16409 | Yes | Reset | - |
+-------+--------------+-------------+--------------+

2. Memory

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| Block RAM Tile | 0 | 0 | 0 | 365 | 0.00 |
| RAMB36/FIFO\* | 0 | 0 | 0 | 365 | 0.00 |
| RAMB18 | 0 | 0 | 0 | 730 | 0.00 |
+----------------+------+-------+------------+-----------+-------+

- Note: Each Block RAM Tile only has one FIFO logic available and therefore can accommodate only one FIFO36E1 or one FIFO18E1. However, if a FIFO18E1 occupies a Block RAM Tile, that tile can still accommodate a RAMB18E1

3. DSP

---

+----------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+----------------+------+-------+------------+-----------+-------+
| DSPs | 5 | 0 | 0 | 740 | 0.68 |
| DSP48E1 only | 5 | | | | |
+----------------+------+-------+------------+-----------+-------+

4. IO and GT Specific

---

+-----------------------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-----------------------------+------+-------+------------+-----------+-------+
| Bonded IOB | 3 | 0 | 0 | 285 | 1.05 |
| Bonded IPADs | 0 | 0 | 0 | 14 | 0.00 |
| Bonded OPADs | 0 | 0 | 0 | 8 | 0.00 |
| PHY_CONTROL | 0 | 0 | 0 | 10 | 0.00 |
| PHASER_REF | 0 | 0 | 0 | 10 | 0.00 |
| OUT_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IN_FIFO | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYCTRL | 0 | 0 | 0 | 10 | 0.00 |
| IBUFDS | 0 | 0 | 0 | 274 | 0.00 |
| GTPE2_CHANNEL | 0 | 0 | 0 | 4 | 0.00 |
| PHASER_OUT/PHASER_OUT_PHY | 0 | 0 | 0 | 40 | 0.00 |
| PHASER_IN/PHASER_IN_PHY | 0 | 0 | 0 | 40 | 0.00 |
| IDELAYE2/IDELAYE2_FINEDELAY | 0 | 0 | 0 | 500 | 0.00 |
| IBUFDS_GTE2 | 0 | 0 | 0 | 2 | 0.00 |
| ILOGIC | 0 | 0 | 0 | 285 | 0.00 |
| OLOGIC | 0 | 0 | 0 | 285 | 0.00 |
+-----------------------------+------+-------+------------+-----------+-------+

5. Clocking

---

+------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+------------+------+-------+------------+-----------+-------+
| BUFGCTRL | 0 | 0 | 0 | 32 | 0.00 |
| BUFIO | 0 | 0 | 0 | 40 | 0.00 |
| MMCME2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| PLLE2_ADV | 0 | 0 | 0 | 10 | 0.00 |
| BUFMRCE | 0 | 0 | 0 | 20 | 0.00 |
| BUFHCE | 0 | 0 | 0 | 120 | 0.00 |
| BUFR | 0 | 0 | 0 | 40 | 0.00 |
+------------+------+-------+------------+-----------+-------+

6. Specific Feature

---

+-------------+------+-------+------------+-----------+-------+
| Site Type | Used | Fixed | Prohibited | Available | Util% |
+-------------+------+-------+------------+-----------+-------+
| BSCANE2 | 0 | 0 | 0 | 4 | 0.00 |
| CAPTUREE2 | 0 | 0 | 0 | 1 | 0.00 |
| DNA_PORT | 0 | 0 | 0 | 1 | 0.00 |
| EFUSE_USR | 0 | 0 | 0 | 1 | 0.00 |
| FRAME_ECCE2 | 0 | 0 | 0 | 1 | 0.00 |
| ICAPE2 | 0 | 0 | 0 | 2 | 0.00 |
| PCIE_2_1 | 0 | 0 | 0 | 1 | 0.00 |
| STARTUPE2 | 0 | 0 | 0 | 1 | 0.00 |
| XADC | 0 | 0 | 0 | 1 | 0.00 |
+-------------+------+-------+------------+-----------+-------+

7. Primitives

---

+----------+-------+---------------------+
| Ref Name | Used | Functional Category |
+----------+-------+---------------------+
| FDRE | 16409 | Flop & Latch |
| LUT6 | 9617 | LUT |
| MUXF7 | 4130 | MuxFx |
| FDCE | 2475 | Flop & Latch |
| LUT2 | 1477 | LUT |
| LUT5 | 1051 | LUT |
| MUXF8 | 1024 | MuxFx |
| LUT3 | 878 | LUT |
| LUT4 | 665 | LUT |
| CARRY4 | 550 | CarryLogic |
| LUT1 | 11 | LUT |
| FDPE | 6 | Flop & Latch |
| DSP48E1 | 5 | Block Arithmetic |
| OBUF | 2 | IO |
| IBUF | 1 | IO |
| FDSE | 1 | Flop & Latch |
+----------+-------+---------------------+

8. Black Boxes

---

+---------------+------+
| Ref Name | Used |
+---------------+------+
| mig_7series_0 | 1 |
+---------------+------+

9. Instantiated Netlists

---

+----------+------+
| Ref Name | Used |
+----------+------+

rsa_ws 16\*16:
