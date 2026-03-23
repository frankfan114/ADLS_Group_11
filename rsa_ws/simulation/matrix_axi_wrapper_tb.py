import random
from collections import deque

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def u32_to_s32(x):
    x &= 0xFFFFFFFF
    return x if x < (1 << 31) else x - (1 << 32)


def s8_to_u8(x):
    return x & 0xFF


def golden_matmul_s8_s32(A, B, M, K, N):
    C = [[0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            s = 0
            for k in range(K):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


def pack_s8_row(row):
    words = []
    w = 0
    cnt = 0
    for v in row:
        w |= (s8_to_u8(v) << (8 * cnt))
        cnt += 1
        if cnt == 4:
            words.append(w & 0xFFFFFFFF)
            w = 0
            cnt = 0
    if cnt != 0:
        words.append(w & 0xFFFFFFFF)
    return words


def gen_matrix(M, K, mode):
    if mode == "zero":
        return [[0 for _ in range(K)] for _ in range(M)]
    if mode == "one":
        return [[1 for _ in range(K)] for _ in range(M)]
    if mode == "max":
        return [[127 for _ in range(K)] for _ in range(M)]
    if mode == "min":
        return [[-128 for _ in range(K)] for _ in range(M)]
    if mode == "ramp":
        return [[((i * 17 + k * 31) % 256) - 128 for k in range(K)] for i in range(M)]
    return [[random.randint(-128, 127) for _ in range(K)] for _ in range(M)]


def gen_matrix_B(K, N, mode):
    if mode == "zero":
        return [[0 for _ in range(N)] for _ in range(K)]
    if mode == "one":
        return [[1 for _ in range(N)] for _ in range(K)]
    if mode == "max":
        return [[127 for _ in range(N)] for _ in range(K)]
    if mode == "min":
        return [[-128 for _ in range(N)] for _ in range(K)]
    if mode == "ramp":
        return [[((k * 13 + j * 29) % 256) - 128 for j in range(N)] for k in range(K)]
    return [[random.randint(-128, 127) for _ in range(N)] for _ in range(K)]


class AxiMemoryModel:
    """Simple AXI4 slave model for 32-bit single-beat traffic."""

    def __init__(self, dut, wait_prob=0.0, max_wait=3):
        self.dut = dut
        self.mem = {}
        self.aw_q = deque()
        self.wait_prob = float(wait_prob)
        self.max_wait = int(max_wait)
        self.aw_stall = 0
        self.w_stall = 0
        self.ar_stall = 0
        self.read_hist = {}
        self.write_hist = {}

    def load_word(self, word_addr, value):
        self.mem[word_addr] = value & 0xFFFFFFFF

    def read_word(self, word_addr):
        return self.mem.get(word_addr, 0) & 0xFFFFFFFF

    def clear_stats(self):
        self.read_hist.clear()
        self.write_hist.clear()

    def _bump(self, hist, word_addr):
        hist[word_addr] = hist.get(word_addr, 0) + 1

    def count_reads(self, base_word, words):
        return sum(self.read_hist.get(base_word + off, 0) for off in range(words))

    def count_writes(self, base_word, words):
        return sum(self.write_hist.get(base_word + off, 0) for off in range(words))

    def _rand_stall(self):
        if self.wait_prob > 0.0 and random.random() < self.wait_prob:
            return random.randint(1, max(1, self.max_wait))
        return 0

    async def run(self):
        self.dut.m_axi_awready.value = 0
        self.dut.m_axi_wready.value = 0
        self.dut.m_axi_bvalid.value = 0
        self.dut.m_axi_bid.value = 0
        self.dut.m_axi_bresp.value = 0
        self.dut.m_axi_arready.value = 0
        self.dut.m_axi_rvalid.value = 0
        self.dut.m_axi_rid.value = 0
        self.dut.m_axi_rresp.value = 0
        self.dut.m_axi_rlast.value = 0
        self.dut.m_axi_rdata.value = 0

        while True:
            await RisingEdge(self.dut.clk)

            if int(self.dut.resetn.value) == 0:
                self.aw_q.clear()
                self.dut.m_axi_awready.value = 0
                self.dut.m_axi_wready.value = 0
                self.dut.m_axi_bvalid.value = 0
                self.dut.m_axi_arready.value = 0
                self.dut.m_axi_rvalid.value = 0
                self.dut.m_axi_rlast.value = 0
                continue

            if int(self.dut.m_axi_bvalid.value) == 1 and int(self.dut.m_axi_bready.value) == 1:
                self.dut.m_axi_bvalid.value = 0

            if int(self.dut.m_axi_rvalid.value) == 1 and int(self.dut.m_axi_rready.value) == 1:
                self.dut.m_axi_rvalid.value = 0
                self.dut.m_axi_rlast.value = 0

            if self.aw_stall > 0:
                self.aw_stall -= 1
                self.dut.m_axi_awready.value = 0
            else:
                can_take_aw = len(self.aw_q) < 8
                self.dut.m_axi_awready.value = 1 if can_take_aw else 0
                if can_take_aw and int(self.dut.m_axi_awvalid.value) == 1:
                    awaddr = int(self.dut.m_axi_awaddr.value)
                    self.aw_q.append(awaddr)
                    self.aw_stall = self._rand_stall()

            if int(self.dut.m_axi_bvalid.value) == 0 and len(self.aw_q) > 0:
                if self.w_stall > 0:
                    self.w_stall -= 1
                    self.dut.m_axi_wready.value = 0
                else:
                    self.dut.m_axi_wready.value = 1
                    if int(self.dut.m_axi_wvalid.value) == 1:
                        awaddr = self.aw_q.popleft()
                        word_addr = awaddr >> 2
                        oldv = self.read_word(word_addr)
                        wdata = int(self.dut.m_axi_wdata.value)
                        wstrb = int(self.dut.m_axi_wstrb.value)

                        newv = oldv
                        for b in range(4):
                            if (wstrb >> b) & 1:
                                newv &= ~(0xFF << (8 * b))
                                newv |= ((wdata >> (8 * b)) & 0xFF) << (8 * b)
                        self.load_word(word_addr, newv)
                        self._bump(self.write_hist, word_addr)

                        self.dut.m_axi_bvalid.value = 1
                        self.dut.m_axi_bresp.value = 0
                        self.dut.m_axi_bid.value = 0
                        self.w_stall = self._rand_stall()
            else:
                self.dut.m_axi_wready.value = 0

            if int(self.dut.m_axi_rvalid.value) == 0:
                if self.ar_stall > 0:
                    self.ar_stall -= 1
                    self.dut.m_axi_arready.value = 0
                else:
                    self.dut.m_axi_arready.value = 1
                    if int(self.dut.m_axi_arvalid.value) == 1:
                        araddr = int(self.dut.m_axi_araddr.value)
                        word_addr = araddr >> 2
                        self._bump(self.read_hist, word_addr)
                        self.dut.m_axi_rdata.value = self.read_word(word_addr)
                        self.dut.m_axi_rresp.value = 0
                        self.dut.m_axi_rid.value = 0
                        self.dut.m_axi_rlast.value = 1
                        self.dut.m_axi_rvalid.value = 1
                        self.ar_stall = self._rand_stall()
            else:
                self.dut.m_axi_arready.value = 0


async def reset_dut(dut, cycles=8):
    dut.resetn.value = 0
    dut.bus_valid.value = 0
    dut.bus_addr.value = 0
    dut.bus_wdata.value = 0
    dut.bus_wstrb.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    dut.resetn.value = 1
    await RisingEdge(dut.clk)


async def bus_write(dut, addr, data, wstrb=0xF, timeout=2000):
    dut.bus_addr.value = addr
    dut.bus_wdata.value = data & 0xFFFFFFFF
    dut.bus_wstrb.value = wstrb & 0xF
    dut.bus_valid.value = 1

    for _ in range(timeout):
        await RisingEdge(dut.clk)
        if int(dut.bus_ready.value) == 1:
            dut.bus_valid.value = 0
            dut.bus_wstrb.value = 0
            return
    raise RuntimeError(f"bus_write timeout addr=0x{addr:08x}")


async def bus_read(dut, addr, timeout=2000):
    dut.bus_addr.value = addr
    dut.bus_wdata.value = 0
    dut.bus_wstrb.value = 0
    dut.bus_valid.value = 1

    for _ in range(timeout):
        await RisingEdge(dut.clk)
        if int(dut.bus_ready.value) == 1:
            data = int(dut.bus_rdata.value) & 0xFFFFFFFF
            dut.bus_valid.value = 0
            return data
    raise RuntimeError(f"bus_read timeout addr=0x{addr:08x}")


async def wait_done_via_status(dut, timeout_cycles=800000):
    for _ in range(timeout_cycles):
        s = await bus_read(dut, 0x20)
        if (s >> 1) & 0x1:
            return
    raise RuntimeError("TIMEOUT waiting done_latched via status register")


def pattern_word(base_word, offset):
    return (0xA5A50000 ^ ((base_word + offset) * 0x1F1F1F1F)) & 0xFFFFFFFF


def packed_words_per_row(cols, elems_per_word=4):
    return (cols + elems_per_word - 1) // elems_per_word


def preload_c_region(mem, base_word, words):
    expected = {}
    for off in range(words):
        val = pattern_word(base_word, off)
        mem.load_word(base_word + off, val)
        expected[base_word + off] = val
    return expected


async def check_status_idle(dut):
    status = await bus_read(dut, 0x20)
    if status & 0x1:
        raise AssertionError(f"sys_busy should be 0 after completion, got status=0x{status:08x}")
    if ((status >> 1) & 0x1) != 1:
        raise AssertionError(f"done_latched should be 1 after completion, got status=0x{status:08x}")


def decode_cfg_status(status_word):
    return {
        "cfg_id": (status_word >> 24) & 0xFF,
        "active_cols": (status_word >> 16) & 0xFF,
        "active_rows": (status_word >> 8) & 0xFF,
    }


def decode_cfg_masks(mask_word):
    return {
        "row_mask": mask_word & 0xFF,
        "col_mask": (mask_word >> 8) & 0xFF,
    }


async def program_array_config(dut, *, auto_cfg_en=True, row_mask=0xFF, col_mask=0xFF):
    await bus_write(dut, 0x24, 0x1 if auto_cfg_en else 0x0)
    await bus_write(dut, 0x28, row_mask)
    await bus_write(dut, 0x2C, col_mask)


async def read_array_config(dut):
    cfg_status = decode_cfg_status(await bus_read(dut, 0x30))
    cfg_masks = decode_cfg_masks(await bus_read(dut, 0x34))
    return {**cfg_status, **cfg_masks}


async def run_one_case(
    dut,
    mem,
    M,
    K,
    N,
    *,
    case_name=None,
    data_mode="random",
    baseA_word=0,
    baseB_word=2048,
    baseC_word=4096,
    wait_prob=None,
    max_wait=None,
    auto_cfg_en=True,
    row_mask=0xFF,
    col_mask=0xFF,
    expected_cfg_id=None,
    expected_active_rows=None,
    expected_active_cols=None,
    expected_row_mask=None,
    expected_col_mask=None,
):
    if wait_prob is not None:
        mem.wait_prob = float(wait_prob)
    if max_wait is not None:
        mem.max_wait = int(max_wait)

    case_name = case_name or f"M{M}_K{K}_N{N}_{data_mode}"
    A = gen_matrix(M, K, data_mode)
    B = gen_matrix_B(K, N, data_mode)
    C_ref = golden_matmul_s8_s32(A, B, M, K, N)
    output_words = max(1, M * N)
    guard_words = 4
    expected_prefill = preload_c_region(mem, baseC_word, output_words + guard_words)

    addr = baseA_word
    for r in range(M):
        for w in pack_s8_row(A[r]):
            mem.load_word(addr, w)
            addr += 1

    addr = baseB_word
    for r in range(K):
        for w in pack_s8_row(B[r]):
            mem.load_word(addr, w)
            addr += 1

    await bus_write(dut, 0x00, baseA_word)
    await bus_write(dut, 0x04, baseB_word)
    await bus_write(dut, 0x08, baseC_word)
    await bus_write(dut, 0x0C, M)
    await bus_write(dut, 0x10, K)
    await bus_write(dut, 0x14, N)
    await program_array_config(
        dut,
        auto_cfg_en=auto_cfg_en,
        row_mask=row_mask,
        col_mask=col_mask,
    )
    await bus_write(dut, 0x1C, 0x1)

    await wait_done_via_status(dut)
    await check_status_idle(dut)

    cfg = await read_array_config(dut)
    if expected_cfg_id is not None and cfg["cfg_id"] != expected_cfg_id:
        raise AssertionError(f"{case_name}: expected cfg_id={expected_cfg_id}, got {cfg['cfg_id']}")
    if expected_active_rows is not None and cfg["active_rows"] != expected_active_rows:
        raise AssertionError(
            f"{case_name}: expected active_rows={expected_active_rows}, got {cfg['active_rows']}"
        )
    if expected_active_cols is not None and cfg["active_cols"] != expected_active_cols:
        raise AssertionError(
            f"{case_name}: expected active_cols={expected_active_cols}, got {cfg['active_cols']}"
        )
    if expected_row_mask is not None and cfg["row_mask"] != expected_row_mask:
        raise AssertionError(
            f"{case_name}: expected row_mask=0x{expected_row_mask:02x}, got 0x{cfg['row_mask']:02x}"
        )
    if expected_col_mask is not None and cfg["col_mask"] != expected_col_mask:
        raise AssertionError(
            f"{case_name}: expected col_mask=0x{expected_col_mask:02x}, got 0x{cfg['col_mask']:02x}"
        )

    if M > 0 and K > 0 and N > 0:
        for i in range(M):
            for j in range(N):
                raw = mem.read_word(baseC_word + i * N + j)
                got = u32_to_s32(raw)
                exp = C_ref[i][j]
                if got != exp:
                    dut._log.error(f"{case_name}: C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}")
                    raise AssertionError("AXI wrapper GEMM mismatch")

    for off in range(M * N, output_words + guard_words):
        addr_word = baseC_word + off
        got = mem.read_word(addr_word)
        exp = expected_prefill[addr_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: guard word overwrite at addr=0x{addr_word:08x} exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("AXI wrapper wrote outside expected output region")

    if M == 0 or N == 0 or K == 0:
        got = mem.read_word(baseC_word)
        exp = expected_prefill[baseC_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: zero-dimension run should not modify C base exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("AXI wrapper modified C for zero-dimension case")

    dut._log.info(
        f"PASS SARA/ADAPTNET GEMM: case={case_name} M={M} K={K} N={N} "
        f"cfg_id={cfg['cfg_id']} active_rows={cfg['active_rows']} active_cols={cfg['active_cols']}"
    )


async def run_reuse_check(dut, mem, *, case):
    await reset_dut(dut)
    mem.clear_stats()
    await run_one_case(dut, mem, **case)

    b_words_total = case["K"] * packed_words_per_row(case["N"])
    c_words_total = case["M"] * case["N"]

    actual_b_reads = mem.count_reads(case["baseB_word"], b_words_total)
    actual_c_writes = mem.count_writes(case["baseC_word"], c_words_total)

    if actual_b_reads != b_words_total:
        raise AssertionError(
            f"{case['case_name']}: expected {b_words_total} B reads with reuse, got {actual_b_reads}"
        )
    if actual_c_writes != c_words_total:
        raise AssertionError(
            f"{case['case_name']}: expected {c_words_total} C writes, got {actual_c_writes}"
        )

    dut._log.info(
        f"PASS SARA reuse check: case={case['case_name']} B_reads={actual_b_reads} C_writes={actual_c_writes}"
    )


@cocotb.test()
async def test_matrix_top_wrapper_axi(dut):
    random.seed(2026)
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await Timer(50, "ns")

    mem = AxiMemoryModel(dut, wait_prob=0.20, max_wait=4)
    cocotb.start_soon(mem.run())

    basic_cases = [
        dict(case_name="smoke_dense_auto", M=8, K=8, N=8, data_mode="random", baseA_word=0, baseB_word=2048, baseC_word=4096),
        dict(case_name="odd_sizes_auto", M=5, K=11, N=7, data_mode="ramp", baseA_word=101, baseB_word=2401, baseC_word=4096),
        dict(case_name="zero_m_auto", M=0, K=5, N=7, data_mode="random", baseA_word=211, baseB_word=2601, baseC_word=4801),
        dict(case_name="zero_k_auto", M=6, K=0, N=4, data_mode="random", baseA_word=311, baseB_word=2801, baseC_word=5201),
        dict(case_name="zero_n_auto", M=5, K=7, N=0, data_mode="random", baseA_word=419, baseB_word=3001, baseC_word=5601),
        dict(case_name="max_values_auto", M=5, K=8, N=7, data_mode="max", baseA_word=503, baseB_word=3401, baseC_word=6201, wait_prob=0.0, max_wait=1),
        dict(case_name="min_values_auto", M=7, K=8, N=5, data_mode="min", baseA_word=619, baseB_word=3801, baseC_word=7001, wait_prob=0.0, max_wait=1),
    ]

    for case in basic_cases:
        await reset_dut(dut)
        await run_one_case(dut, mem, **case)

    manual_cases = [
        dict(
            case_name="manual_sparse_bypass",
            M=7,
            K=8,
            N=8,
            data_mode="random",
            baseA_word=6000,
            baseB_word=8000,
            baseC_word=10000,
            auto_cfg_en=False,
            row_mask=0x55,
            col_mask=0x33,
            expected_cfg_id=0x80,
            expected_active_rows=4,
            expected_active_cols=4,
            expected_row_mask=0x55,
            expected_col_mask=0x33,
        ),
        dict(
            case_name="manual_zero_mask_fallback",
            M=8,
            K=8,
            N=8,
            data_mode="one",
            baseA_word=12000,
            baseB_word=14000,
            baseC_word=16000,
            auto_cfg_en=False,
            row_mask=0x00,
            col_mask=0x00,
            expected_cfg_id=0x80,
            expected_active_rows=8,
            expected_active_cols=8,
            expected_row_mask=0xFF,
            expected_col_mask=0xFF,
        ),
    ]

    for case in manual_cases:
        await reset_dut(dut)
        await run_one_case(dut, mem, **case)

    auto_cases = [
        dict(
            case_name="auto_balanced_4x4",
            M=3,
            K=8,
            N=3,
            data_mode="random",
            baseA_word=18000,
            baseB_word=20000,
            baseC_word=22000,
            expected_cfg_id=3,
            expected_active_rows=4,
            expected_active_cols=4,
            expected_row_mask=0x0F,
            expected_col_mask=0x0F,
        ),
        dict(
            case_name="auto_tall_4x8",
            M=3,
            K=8,
            N=16,
            data_mode="random",
            baseA_word=24000,
            baseB_word=26000,
            baseC_word=28000,
            expected_cfg_id=1,
            expected_active_rows=4,
            expected_active_cols=8,
            expected_row_mask=0x0F,
            expected_col_mask=0xFF,
        ),
        dict(
            case_name="auto_wide_8x4",
            M=16,
            K=8,
            N=3,
            data_mode="random",
            baseA_word=30000,
            baseB_word=32000,
            baseC_word=34000,
            expected_cfg_id=2,
            expected_active_rows=8,
            expected_active_cols=4,
            expected_row_mask=0xFF,
            expected_col_mask=0x0F,
        ),
        dict(
            case_name="auto_small_2x2",
            M=2,
            K=8,
            N=2,
            data_mode="random",
            baseA_word=36000,
            baseB_word=38000,
            baseC_word=40000,
            expected_cfg_id=6,
            expected_active_rows=2,
            expected_active_cols=2,
            expected_row_mask=0x03,
            expected_col_mask=0x03,
        ),
    ]

    for case in auto_cases:
        await reset_dut(dut)
        await run_one_case(dut, mem, **case)

    repeat_cases = [
        dict(
            case_name="repeat_manual_same_output_base",
            M=4,
            K=8,
            N=8,
            data_mode="one",
            baseA_word=42000,
            baseB_word=44000,
            baseC_word=46000,
            auto_cfg_en=False,
            row_mask=0x0F,
            col_mask=0xFF,
            expected_cfg_id=0x80,
            expected_active_rows=4,
            expected_active_cols=8,
            expected_row_mask=0x0F,
            expected_col_mask=0xFF,
        ),
        dict(
            case_name="repeat_auto_same_output_base",
            M=4,
            K=8,
            N=4,
            data_mode="random",
            baseA_word=48000,
            baseB_word=50000,
            baseC_word=46000,
            expected_cfg_id=3,
            expected_active_rows=4,
            expected_active_cols=4,
            expected_row_mask=0x0F,
            expected_col_mask=0x0F,
        ),
    ]

    await reset_dut(dut)
    for case in repeat_cases:
        await run_one_case(dut, mem, **case)

    reuse_case = dict(
        case_name="manual_4x8_b_reuse",
        M=16,
        K=8,
        N=8,
        data_mode="random",
        baseA_word=52000,
        baseB_word=54000,
        baseC_word=56000,
        auto_cfg_en=False,
        row_mask=0x0F,
        col_mask=0xFF,
        expected_cfg_id=0x80,
        expected_active_rows=4,
        expected_active_cols=8,
        expected_row_mask=0x0F,
        expected_col_mask=0xFF,
    )
    await run_reuse_check(dut, mem, case=reuse_case)

    dut._log.info("ALL SARA/ADAPTNET AXI WRAPPER TEST CASES PASSED")
