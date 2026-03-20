import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# ============================================================
# Helpers: signed / unsigned reinterpret
# ============================================================
def u8_to_s8(x):
    x &= 0xFF
    return x if x < 0x80 else x - 0x100


def s8_to_u8(x):
    return x & 0xFF


def u32_to_s32(x):
    x &= 0xFFFFFFFF
    return x if x < (1 << 31) else x - (1 << 32)


def s32_to_u32(x):
    return x & 0xFFFFFFFF


# ============================================================
# PicoRV32-style SRAM Wrapper (bit-true, unsigned storage)
# ============================================================
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
                    oldv = self.mem.get(self.addr, 0)
                    newv = oldv
                    for b in range(4):
                        if (self.wstrb >> b) & 1:
                            newv &= ~(0xFF << (8 * b))
                            newv |= ((self.wdata >> (8 * b)) & 0xFF) << (8 * b)
                    self.mem[self.addr] = newv & 0xFFFFFFFF
                else:
                    self.dut.mem_rdata.value = self.mem.get(self.addr, 0) & 0xFFFFFFFF

                self.state = self.ST_HOLD

            elif self.state == self.ST_HOLD:
                self.dut.mem_ready.value = 1


# ============================================================
# Golden GEMM: S8 × S8 → S32
# ============================================================
def golden_matmul_s8_s32(A, B, M, K, N):
    C = [[0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            s = 0
            for k in range(K):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


# ============================================================
# Packing helpers (SRAM is bit-true)
# ============================================================
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


# ============================================================
# Matrix generators (SIGNED)
# ============================================================
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


# ============================================================
# Control helpers
# ============================================================
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
    await RisingEdge(dut.clk)


async def wait_done(dut, timeout_cycles=500000):
    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        if dut.done.value.is_resolvable and int(dut.done.value) == 1:
            return
    raise RuntimeError("TIMEOUT waiting for done")


# ============================================================
# One test case
# ============================================================
async def run_one_case(
    dut,
    M,
    K,
    N,
    *,
    data_mode="random",
    baseA_word=0,
    baseB_word=2048,
    baseC_word=4096,
    sram_wait_prob=0.0,
    sram_max_wait=3,
):

    dut.glob_m_num.value = M
    dut.glob_k_num.value = K
    dut.glob_n_num.value = N
    dut.base_addr_A.value = baseA_word
    dut.base_addr_B.value = baseB_word
    dut.base_addr_C.value = baseC_word

    A = gen_matrix(M, K, data_mode)
    B = gen_matrix_B(K, N, data_mode)
    C_ref = golden_matmul_s8_s32(A, B, M, K, N)

    sram = PicoSRAM(dut, wait_prob=sram_wait_prob, max_wait=sram_max_wait)
    cocotb.start_soon(sram.run())

    addr = baseA_word
    for r in range(M):
        for w in pack_s8_row(A[r]):
            sram.mem[addr] = w
            addr += 1

    addr = baseB_word
    for r in range(K):
        for w in pack_s8_row(B[r]):
            sram.mem[addr] = w
            addr += 1

    await start_pulse(dut)
    await wait_done(dut)

    for i in range(M):
        for j in range(N):
            raw = sram.mem.get(baseC_word + i * N + j, 0)
            got = u32_to_s32(raw)
            exp = C_ref[i][j]
            if got != exp:
                dut._log.error(f"C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}")
                raise AssertionError("SIGNED GEMM MISMATCH")

    dut._log.info(f"PASS signed GEMM: M={M} K={K} N={N} mode={data_mode}")


# ============================================================
# Regression
# ============================================================
@cocotb.test()
async def test_matrix_top_signed_regression(dut):
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await Timer(50, "ns")
    await reset_dut(dut)

    await run_one_case(dut, 1, 1, 1, data_mode="ramp")
    await run_one_case(dut, 8, 8, 8, data_mode="random")
    await run_one_case(dut, 8, 8, 8, data_mode="max")
    await run_one_case(dut, 8, 8, 8, data_mode="min")
    await run_one_case(dut, 16, 7, 19, data_mode="random", sram_wait_prob=0.3)
    await run_one_case(dut, 16, 7, 19, data_mode="random", sram_wait_prob=0.3, sram_max_wait=5)


    dut._log.info("ALL SIGNED REGRESSION CASES PASSED")
