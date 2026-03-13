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


async def run_one_case(
    dut,
    mem,
    M,
    K,
    N,
    *,
    data_mode="random",
    baseA_word=0,
    baseB_word=2048,
    baseC_word=4096,
):
    A = gen_matrix(M, K, data_mode)
    B = gen_matrix_B(K, N, data_mode)
    C_ref = golden_matmul_s8_s32(A, B, M, K, N)

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

    # check C (unpacked s32, one word per element)
    for i in range(M):
        for j in range(N):
            raw = mem.read_word(baseC_word + i * N + j)
            got = u32_to_s32(raw)
            exp = C_ref[i][j]
            if got != exp:
                dut._log.error(f"C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}")
                raise AssertionError("AXI wrapper GEMM mismatch")

    dut._log.info(f"PASS AXI wrapper GEMM: M={M} K={K} N={N} mode={data_mode}")


@cocotb.test()
async def test_matrix_top_wrapper_axi(dut):
    random.seed(2026)
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await Timer(50, "ns")

    mem = AxiMemoryModel(dut, wait_prob=0.20, max_wait=4)
    cocotb.start_soon(mem.run())

    await reset_dut(dut)

    await run_one_case(dut, mem, 1, 1, 1, data_mode="ramp")
    await run_one_case(dut, mem, 8, 8, 8, data_mode="random")
    await run_one_case(dut, mem, 10, 7, 9, data_mode="random")

    dut._log.info("ALL AXI WRAPPER TEST CASES PASSED")

