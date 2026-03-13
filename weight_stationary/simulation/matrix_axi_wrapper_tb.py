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
        self.mem = {}  # word-addressed storage: addr_word -> u32
        self.aw_q = deque()
        self.wait_prob = float(wait_prob)
        self.max_wait = int(max_wait)
        self.aw_stall = 0
        self.w_stall = 0
        self.ar_stall = 0

    def load_word(self, word_addr, value):
        self.mem[word_addr] = value & 0xFFFFFFFF

    def read_word(self, word_addr):
        return self.mem.get(word_addr, 0) & 0xFFFFFFFF

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

            # Keep B channel valid until accepted
            if int(self.dut.m_axi_bvalid.value) == 1 and int(self.dut.m_axi_bready.value) == 1:
                self.dut.m_axi_bvalid.value = 0

            # Keep R channel valid until accepted
            if int(self.dut.m_axi_rvalid.value) == 1 and int(self.dut.m_axi_rready.value) == 1:
                self.dut.m_axi_rvalid.value = 0
                self.dut.m_axi_rlast.value = 0

            # AW ready with optional random stall
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

            # W ready only when an AW has arrived and no B pending
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

                        self.dut.m_axi_bvalid.value = 1
                        self.dut.m_axi_bresp.value = 0  # OKAY
                        self.dut.m_axi_bid.value = 0
                        self.w_stall = self._rand_stall()
            else:
                self.dut.m_axi_wready.value = 0

            # AR/R read path (single pending read response)
            if int(self.dut.m_axi_rvalid.value) == 0:
                if self.ar_stall > 0:
                    self.ar_stall -= 1
                    self.dut.m_axi_arready.value = 0
                else:
                    self.dut.m_axi_arready.value = 1
                    if int(self.dut.m_axi_arvalid.value) == 1:
                        araddr = int(self.dut.m_axi_araddr.value)
                        word_addr = araddr >> 2
                        self.dut.m_axi_rdata.value = self.read_word(word_addr)
                        self.dut.m_axi_rresp.value = 0  # OKAY
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
    # status register @ 0x20: [1]=done_latched, [0]=sys_busy
    for _ in range(timeout_cycles):
        s = await bus_read(dut, 0x20)
        if (s >> 1) & 0x1:
            return
    raise RuntimeError("TIMEOUT waiting done_latched via status register")


def pattern_word(base_word, offset):
    return (0xA5A50000 ^ ((base_word + offset) * 0x1F1F1F1F)) & 0xFFFFFFFF


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

    # preload A (packed s8) to word-addressed memory
    addr = baseA_word
    for r in range(M):
        for w in pack_s8_row(A[r]):
            mem.load_word(addr, w)
            addr += 1

    # preload B (packed s8)
    addr = baseB_word
    for r in range(K):
        for w in pack_s8_row(B[r]):
            mem.load_word(addr, w)
            addr += 1

    # program wrapper registers
    await bus_write(dut, 0x00, baseA_word)
    await bus_write(dut, 0x04, baseB_word)
    await bus_write(dut, 0x08, baseC_word)
    await bus_write(dut, 0x0C, M)
    await bus_write(dut, 0x10, K)
    await bus_write(dut, 0x14, N)
    await bus_write(dut, 0x1C, 0x1)  # start

    await wait_done_via_status(dut)
    await check_status_idle(dut)

    # check C (unpacked s32, one word per element)
    if M > 0 and K > 0 and N > 0:
        for i in range(M):
            for j in range(N):
                raw = mem.read_word(baseC_word + i * N + j)
                got = u32_to_s32(raw)
                exp = C_ref[i][j]
                if got != exp:
                    dut._log.error(f"{case_name}: C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}")
                    raise AssertionError("AXI wrapper GEMM mismatch")

    # check guard region remains unchanged, including zero-dimension cases
    for off in range(M * N, output_words + guard_words):
        addr_word = baseC_word + off
        got = mem.read_word(addr_word)
        exp = expected_prefill[addr_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: guard word overwrite at addr=0x{addr_word:08x} exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("AXI wrapper wrote outside expected output region")

    # zero-sized outputs should leave even the first C word untouched
    if M == 0 or N == 0 or K == 0:
        got = mem.read_word(baseC_word)
        exp = expected_prefill[baseC_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: zero-dimension run should not modify C base exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("AXI wrapper modified C for zero-dimension case")

    dut._log.info(
        f"PASS AXI wrapper GEMM: case={case_name} M={M} K={K} N={N} mode={data_mode} "
        f"baseA={baseA_word} baseB={baseB_word} baseC={baseC_word} wait_prob={mem.wait_prob}"
    )


@cocotb.test()
async def test_matrix_top_wrapper_axi(dut):
    random.seed(2026)
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await Timer(50, "ns")

    mem = AxiMemoryModel(dut, wait_prob=0.20, max_wait=4)
    cocotb.start_soon(mem.run())

    isolated_cases = [
        dict(case_name="smoke_1x1x1", M=1, K=1, N=1, data_mode="ramp", baseA_word=0, baseB_word=2048, baseC_word=4096, wait_prob=0.20, max_wait=4),
        dict(case_name="zero_m", M=0, K=5, N=7, data_mode="random", baseA_word=11, baseB_word=301, baseC_word=611, wait_prob=0.10, max_wait=3),
        dict(case_name="zero_k", M=6, K=0, N=4, data_mode="random", baseA_word=19, baseB_word=347, baseC_word=701, wait_prob=0.10, max_wait=3),
        dict(case_name="zero_n", M=5, K=7, N=0, data_mode="random", baseA_word=23, baseB_word=389, baseC_word=809, wait_prob=0.10, max_wait=3),
        dict(case_name="exact_tile_random", M=8, K=8, N=8, data_mode="random", baseA_word=0, baseB_word=2048, baseC_word=4096, wait_prob=0.20, max_wait=4),
        dict(case_name="max_values", M=5, K=8, N=7, data_mode="max", baseA_word=37, baseB_word=521, baseC_word=1031, wait_prob=0.0, max_wait=1),
        dict(case_name="min_values", M=7, K=8, N=5, data_mode="min", baseA_word=41, baseB_word=613, baseC_word=1231, wait_prob=0.0, max_wait=1),
        dict(case_name="odd_sizes_ramp", M=3, K=11, N=17, data_mode="ramp", baseA_word=53, baseB_word=911, baseC_word=1601, wait_prob=0.25, max_wait=5),
        dict(case_name="mixed_tiling_random", M=10, K=7, N=9, data_mode="random", baseA_word=67, baseB_word=1201, baseC_word=2201, wait_prob=0.20, max_wait=4),
        dict(case_name="large_multi_tile_random", M=16, K=7, N=19, data_mode="random", baseA_word=79, baseB_word=1501, baseC_word=2801, wait_prob=0.20, max_wait=4),
        dict(case_name="wide_k_partial_random", M=9, K=13, N=5, data_mode="random", baseA_word=97, baseB_word=1901, baseC_word=3401, wait_prob=0.20, max_wait=4),
    ]

    for case in isolated_cases:
        await reset_dut(dut)
        await run_one_case(dut, mem, **case)

    repeat_cases = [
        dict(case_name="repeat_same_output_base_first", M=4, K=9, N=4, data_mode="one", baseA_word=101, baseB_word=2401, baseC_word=4096, wait_prob=0.30, max_wait=5),
        dict(case_name="repeat_same_output_base_second", M=4, K=9, N=4, data_mode="random", baseA_word=131, baseB_word=2601, baseC_word=4096, wait_prob=0.30, max_wait=5),
    ]

    await reset_dut(dut)
    for case in repeat_cases:
        await run_one_case(dut, mem, **case)

    dut._log.info("ALL AXI WRAPPER TEST CASES PASSED")

