import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def u8_to_s8(x):
    x &= 0xFF
    return x if x < 0x80 else x - 0x100


def s8_to_u8(x):
    return x & 0xFF


def u32_to_s32(x):
    x &= 0xFFFFFFFF
    return x if x < (1 << 31) else x - (1 << 32)


class PicoSRAM:
    ST_IDLE = 0
    ST_ACCESS = 1
    ST_HOLD = 2

    def __init__(self, dut, size_words=16384, wait_prob=0.0, max_wait=3):
        self.dut = dut
        self.mem = {i: 0 for i in range(size_words)}
        self.size_words = size_words

        self.state = self.ST_IDLE
        self.addr = 0
        self.wstrb = 0
        self.wdata = 0

        self.wait_prob = float(wait_prob)
        self.max_wait = int(max_wait)
        self.wait_cnt = 0

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

    async def run(self):
        self.dut.mem_ready.value = 0
        if hasattr(self.dut, "mem_rdata"):
            self.dut.mem_rdata.value = 0

        while True:
            await RisingEdge(self.dut.clk)
            self.dut.mem_ready.value = 0

            if not self.dut.mem_valid.value.is_resolvable:
                continue

            if int(self.dut.mem_valid.value) == 0:
                if self.state == self.ST_HOLD:
                    self.state = self.ST_IDLE
                continue

            if self.wait_cnt > 0:
                self.wait_cnt -= 1
                continue
            if self.wait_prob > 0.0 and random.random() < self.wait_prob:
                self.wait_cnt = random.randint(1, max(1, self.max_wait))
                continue

            addr_word = int(self.dut.mem_addr.value) >> 2
            wstrb = int(self.dut.mem_wstrb.value) if self.dut.mem_wstrb.value.is_resolvable else 0
            wdata = int(self.dut.mem_wdata.value) if (wstrb and self.dut.mem_wdata.value.is_resolvable) else 0

            if self.state == self.ST_IDLE:
                self.addr = addr_word
                self.wstrb = wstrb
                self.wdata = wdata
                self.state = self.ST_ACCESS

            elif self.state == self.ST_ACCESS:
                self.dut.mem_ready.value = 1

                if self.wstrb != 0:
                    oldv = self.read_word(self.addr)
                    newv = oldv
                    for b in range(4):
                        if (self.wstrb >> b) & 1:
                            newv &= ~(0xFF << (8 * b))
                            newv |= ((self.wdata >> (8 * b)) & 0xFF) << (8 * b)
                    self.load_word(self.addr, newv)
                    self._bump(self.write_hist, self.addr)
                else:
                    self._bump(self.read_hist, self.addr)
                    self.dut.mem_rdata.value = self.read_word(self.addr)

                self.state = self.ST_HOLD

            elif self.state == self.ST_HOLD:
                self.dut.mem_ready.value = 1


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


def pattern_word(base_word, offset):
    return (0xA5A50000 ^ ((base_word + offset) * 0x1F1F1F1F)) & 0xFFFFFFFF


def preload_c_region(sram, base_word, words):
    expected = {}
    for off in range(words):
        val = pattern_word(base_word, off)
        sram.load_word(base_word + off, val)
        expected[base_word + off] = val
    return expected


async def reset_dut(dut, cycles=5):
    dut.rst_n.value = 0
    dut.start.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def start_pulse(dut, width_cycles=1):
    dut.start.value = 1
    for _ in range(width_cycles):
        await RisingEdge(dut.clk)
    dut.start.value = 0


async def wait_done(dut, timeout_cycles=500000):
    if dut.done.value.is_resolvable and int(dut.done.value) == 1:
        return
    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        if dut.done.value.is_resolvable and int(dut.done.value) == 1:
            return
    raise RuntimeError("TIMEOUT waiting for done")


async def check_idle_signals(dut, *, context):
    busy = int(dut.busy.value) if dut.busy.value.is_resolvable else None
    done = int(dut.done.value) if dut.done.value.is_resolvable else None
    if busy != 0 or done != 0:
        raise AssertionError(f"{context}: expected busy=0 done=0, got busy={busy} done={done}")


async def run_one_case(
    dut,
    sram,
    M,
    K,
    N,
    *,
    case_name=None,
    data_mode="random",
    baseA_word=0,
    baseB_word=2048,
    baseC_word=4096,
    sram_wait_prob=None,
    sram_max_wait=None,
):
    if sram_wait_prob is not None:
        sram.wait_prob = float(sram_wait_prob)
    if sram_max_wait is not None:
        sram.max_wait = int(sram_max_wait)

    case_name = case_name or f"M{M}_K{K}_N{N}_{data_mode}"
    sram.clear_stats()

    dut.glob_m_num.value = M
    dut.glob_k_num.value = K
    dut.glob_n_num.value = N
    dut.base_addr_A.value = baseA_word
    dut.base_addr_B.value = baseB_word
    dut.base_addr_C.value = baseC_word

    A = gen_matrix(M, K, data_mode)
    B = gen_matrix_B(K, N, data_mode)
    C_ref = golden_matmul_s8_s32(A, B, M, K, N)
    output_words = max(1, M * N)
    guard_words = 4
    expected_prefill = preload_c_region(sram, baseC_word, output_words + guard_words)

    addr = baseA_word
    for r in range(M):
        for w in pack_s8_row(A[r]):
            sram.load_word(addr, w)
            addr += 1

    addr = baseB_word
    for r in range(K):
        for w in pack_s8_row(B[r]):
            sram.load_word(addr, w)
            addr += 1

    await start_pulse(dut)
    await wait_done(dut)
    await RisingEdge(dut.clk)
    await check_idle_signals(dut, context=f"{case_name} after completion")

    if M > 0 and K > 0 and N > 0:
        for i in range(M):
            for j in range(N):
                raw = sram.read_word(baseC_word + i * N + j)
                got = u32_to_s32(raw)
                exp = C_ref[i][j]
                if got != exp:
                    dut._log.error(f"{case_name}: C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}")
                    raise AssertionError("SIGNED GEMM MISMATCH")

    for off in range(M * N, output_words + guard_words):
        addr_word = baseC_word + off
        got = sram.read_word(addr_word)
        exp = expected_prefill[addr_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: guard word overwrite at addr=0x{addr_word:08x} exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("core wrote outside expected output region")

    actual_c_reads = sram.count_reads(baseC_word, M * N)
    actual_c_writes = sram.count_writes(baseC_word, M * N)
    expected_c_writes = 0 if (M == 0 or N == 0 or K == 0) else (M * N)

    if actual_c_reads != 0:
        raise AssertionError(f"{case_name}: expected 0 C reads, got {actual_c_reads}")
    if actual_c_writes != expected_c_writes:
        raise AssertionError(f"{case_name}: expected {expected_c_writes} C writes, got {actual_c_writes}")

    if M == 0 or N == 0 or K == 0:
        got = sram.read_word(baseC_word)
        exp = expected_prefill[baseC_word]
        if got != exp:
            dut._log.error(
                f"{case_name}: zero-dimension run should not modify C base exp=0x{exp:08x} got=0x{got:08x}"
            )
            raise AssertionError("core modified C for zero-dimension case")

    dut._log.info(
        f"PASS signed GEMM: case={case_name} M={M} K={K} N={N} mode={data_mode} "
        f"wait_prob={sram.wait_prob}"
    )


@cocotb.test()
async def test_matrix_top_signed_regression(dut):
    random.seed(2026)
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await Timer(50, "ns")

    sram = PicoSRAM(dut)
    cocotb.start_soon(sram.run())

    isolated_cases = [
        dict(case_name="smoke_1x1x1", M=1, K=1, N=1, data_mode="ramp", baseA_word=0, baseB_word=2048, baseC_word=4096, sram_wait_prob=0.20, sram_max_wait=4),
        dict(case_name="zero_m", M=0, K=5, N=7, data_mode="random", baseA_word=11, baseB_word=301, baseC_word=611, sram_wait_prob=0.10, sram_max_wait=3),
        dict(case_name="zero_k", M=6, K=0, N=4, data_mode="random", baseA_word=19, baseB_word=347, baseC_word=701, sram_wait_prob=0.10, sram_max_wait=3),
        dict(case_name="zero_n", M=5, K=7, N=0, data_mode="random", baseA_word=23, baseB_word=389, baseC_word=809, sram_wait_prob=0.10, sram_max_wait=3),
        dict(case_name="exact_tile_random", M=8, K=8, N=8, data_mode="random", baseA_word=0, baseB_word=2048, baseC_word=4096, sram_wait_prob=0.20, sram_max_wait=4),
        dict(case_name="max_values", M=5, K=8, N=7, data_mode="max", baseA_word=37, baseB_word=521, baseC_word=1031, sram_wait_prob=0.0, sram_max_wait=1),
        dict(case_name="min_values", M=7, K=8, N=5, data_mode="min", baseA_word=41, baseB_word=613, baseC_word=1231, sram_wait_prob=0.0, sram_max_wait=1),
        dict(case_name="odd_sizes_ramp", M=3, K=11, N=17, data_mode="ramp", baseA_word=53, baseB_word=911, baseC_word=1601, sram_wait_prob=0.25, sram_max_wait=5),
        dict(case_name="mixed_tiling_random", M=10, K=7, N=9, data_mode="random", baseA_word=67, baseB_word=1201, baseC_word=2201, sram_wait_prob=0.20, sram_max_wait=4),
        dict(case_name="large_multi_tile_random", M=16, K=7, N=19, data_mode="random", baseA_word=79, baseB_word=1501, baseC_word=2801, sram_wait_prob=0.20, sram_max_wait=4),
        dict(case_name="wide_k_partial_random", M=9, K=13, N=5, data_mode="random", baseA_word=97, baseB_word=1901, baseC_word=3401, sram_wait_prob=0.20, sram_max_wait=4),
    ]

    for case in isolated_cases:
        await reset_dut(dut)
        await check_idle_signals(dut, context=f"{case['case_name']} after reset")
        await run_one_case(dut, sram, **case)

    repeat_cases = [
        dict(case_name="repeat_same_output_base_first", M=4, K=9, N=4, data_mode="one", baseA_word=101, baseB_word=2401, baseC_word=4096, sram_wait_prob=0.30, sram_max_wait=5),
        dict(case_name="repeat_same_output_base_second", M=4, K=9, N=4, data_mode="random", baseA_word=131, baseB_word=2601, baseC_word=4096, sram_wait_prob=0.30, sram_max_wait=5),
    ]

    await reset_dut(dut)
    await check_idle_signals(dut, context="repeat sequence after reset")
    for case in repeat_cases:
        await run_one_case(dut, sram, **case)

    dut._log.info("ALL SIGNED REGRESSION CASES PASSED")
