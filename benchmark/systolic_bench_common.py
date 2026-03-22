import random
from collections import deque

import cocotb
from cocotb.triggers import Event, RisingEdge
from cocotb.utils import get_sim_time


CLOCK_PERIOD_NS = 10
DEFAULT_BASE_A_WORD = 0
DEFAULT_BASE_B_WORD = 4096
DEFAULT_BASE_C_WORD = 8192


def u32_to_s32(x):
    x &= 0xFFFFFFFF
    return x if x < (1 << 31) else x - (1 << 32)


def s8_to_u8(x):
    return x & 0xFF


def golden_matmul_s8_s32(A, B, M, K, N):
    C = [[0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            acc = 0
            for k in range(K):
                acc += A[i][k] * B[k][j]
            C[i][j] = acc
    return C


def pack_s8_row(row):
    words = []
    w = 0
    cnt = 0
    for v in row:
        w |= s8_to_u8(v) << (8 * cnt)
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


def packed_words_per_row(cols, elems_per_word=4):
    return (cols + elems_per_word - 1) // elems_per_word


def pattern_word(base_word, offset):
    return (0xA5A50000 ^ ((base_word + offset) * 0x1F1F1F1F)) & 0xFFFFFFFF


def preload_c_region(mem, base_word, words):
    expected = {}
    for off in range(words):
        val = pattern_word(base_word, off)
        mem.load_word(base_word + off, val)
        expected[base_word + off] = val
    return expected


def int_value(signal):
    value = signal.value
    if hasattr(value, "is_resolvable") and not value.is_resolvable:
        return 0
    return int(value)


def resolve_signal_value(dut, *paths):
    for path in paths:
        target = dut
        ok = True
        for attr in path.split("."):
            if not hasattr(target, attr):
                ok = False
                break
            target = getattr(target, attr)
        if ok:
            return int_value(target)
    return None


class DeterministicAxiMemoryModel:
    """Simple AXI4 slave model for 32-bit single-beat traffic with counters."""

    def __init__(
        self,
        dut,
        *,
        wait_prob=0.0,
        max_wait=3,
    ):
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
        self.read_beats = 0
        self.write_beats = 0

    def configure(
        self,
        *,
        wait_prob=0.0,
        max_wait=3,
    ):
        self.wait_prob = float(wait_prob)
        self.max_wait = int(max_wait)

    def clear_memory(self):
        self.mem.clear()

    def clear_stats(self):
        self.read_hist.clear()
        self.write_hist.clear()
        self.read_beats = 0
        self.write_beats = 0

    def load_word(self, word_addr, value):
        self.mem[word_addr] = value & 0xFFFFFFFF

    def read_word(self, word_addr):
        return self.mem.get(word_addr, 0) & 0xFFFFFFFF

    def _bump(self, hist, word_addr):
        hist[word_addr] = hist.get(word_addr, 0) + 1

    def count_reads(self, base_word, words):
        return sum(self.read_hist.get(base_word + off, 0) for off in range(words))

    def count_writes(self, base_word, words):
        return sum(self.write_hist.get(base_word + off, 0) for off in range(words))

    def _reset_runtime(self):
        self.aw_q.clear()
        self.aw_stall = 0
        self.w_stall = 0
        self.ar_stall = 0

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

    def _rand_stall(self):
        if self.wait_prob > 0.0 and random.random() < self.wait_prob:
            return random.randint(1, max(1, self.max_wait))
        return 0

    async def run(self):
        self._reset_runtime()

        while True:
            await RisingEdge(self.dut.clk)

            if int_value(self.dut.resetn) == 0:
                self._reset_runtime()
                continue

            if int_value(self.dut.m_axi_bvalid) == 1 and int_value(self.dut.m_axi_bready) == 1:
                self.dut.m_axi_bvalid.value = 0

            if int_value(self.dut.m_axi_rvalid) == 1 and int_value(self.dut.m_axi_rready) == 1:
                self.dut.m_axi_rvalid.value = 0
                self.dut.m_axi_rlast.value = 0

            if self.aw_stall > 0:
                self.aw_stall -= 1
                self.dut.m_axi_awready.value = 0
            else:
                can_take_aw = len(self.aw_q) < 8
                self.dut.m_axi_awready.value = 1 if can_take_aw else 0
                if can_take_aw and int_value(self.dut.m_axi_awvalid) == 1:
                    awaddr = int_value(self.dut.m_axi_awaddr)
                    self.aw_q.append(awaddr)
                    self.aw_stall = self._rand_stall()

            if int_value(self.dut.m_axi_bvalid) == 0 and len(self.aw_q) > 0:
                if self.w_stall > 0:
                    self.w_stall -= 1
                    self.dut.m_axi_wready.value = 0
                else:
                    self.dut.m_axi_wready.value = 1
                    if int_value(self.dut.m_axi_wvalid) == 1:
                        awaddr = self.aw_q.popleft()
                        word_addr = awaddr >> 2
                        oldv = self.read_word(word_addr)
                        wdata = int_value(self.dut.m_axi_wdata)
                        wstrb = int_value(self.dut.m_axi_wstrb)

                        newv = oldv
                        for byte_idx in range(4):
                            if (wstrb >> byte_idx) & 1:
                                newv &= ~(0xFF << (8 * byte_idx))
                                newv |= ((wdata >> (8 * byte_idx)) & 0xFF) << (8 * byte_idx)

                        self.load_word(word_addr, newv)
                        self._bump(self.write_hist, word_addr)
                        self.write_beats += 1
                        self.dut.m_axi_bvalid.value = 1
                        self.dut.m_axi_bresp.value = 0
                        self.dut.m_axi_bid.value = 0
                        self.w_stall = self._rand_stall()
            else:
                self.dut.m_axi_wready.value = 0

            if int_value(self.dut.m_axi_rvalid) == 0:
                if self.ar_stall > 0:
                    self.ar_stall -= 1
                    self.dut.m_axi_arready.value = 0
                else:
                    self.dut.m_axi_arready.value = 1
                    if int_value(self.dut.m_axi_arvalid) == 1:
                        araddr = int_value(self.dut.m_axi_araddr)
                        word_addr = araddr >> 2
                        self._bump(self.read_hist, word_addr)
                        self.read_beats += 1
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
        if int_value(dut.bus_ready) == 1:
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
        if int_value(dut.bus_ready) == 1:
            data = int_value(dut.bus_rdata) & 0xFFFFFFFF
            dut.bus_valid.value = 0
            return data
    raise RuntimeError(f"bus_read timeout addr=0x{addr:08x}")


async def wait_done_via_status(dut, timeout_cycles=800000):
    for _ in range(timeout_cycles):
        status = await bus_read(dut, 0x20)
        if (status >> 1) & 0x1:
            return
    raise RuntimeError("TIMEOUT waiting for done_latched via status register")


async def check_status_idle(dut):
    status = await bus_read(dut, 0x20)
    if status & 0x1:
        raise AssertionError(f"sys_busy should be 0 after completion, got status=0x{status:08x}")
    if ((status >> 1) & 0x1) != 1:
        raise AssertionError(f"done_latched should be 1 after completion, got status=0x{status:08x}")


async def program_optional_array_config(dut, case):
    if "auto_config_en" in case:
        await bus_write(dut, 0x24, 0x1 if bool(case.get("auto_config_en")) else 0x0)
    if "manual_row_mask" in case:
        await bus_write(dut, 0x28, int(case.get("manual_row_mask", 0)) & 0xFFFFFFFF)
    if "manual_col_mask" in case:
        await bus_write(dut, 0x2C, int(case.get("manual_col_mask", 0)) & 0xFFFFFFFF)


async def read_optional_array_config(dut, *, default_rows=8, default_cols=8):
    cfg_status = await bus_read(dut, 0x30)
    cfg_masks = await bus_read(dut, 0x34)

    selected_cfg_id = (cfg_status >> 24) & 0xFF
    selected_active_cols = (cfg_status >> 16) & 0xFF
    selected_active_rows = (cfg_status >> 8) & 0xFF

    if selected_active_rows == 0:
        selected_active_rows = int(default_rows)
    if selected_active_cols == 0:
        selected_active_cols = int(default_cols)

    row_mask_width = int(default_rows)
    col_mask_width = int(default_cols)
    row_mask = cfg_masks & ((1 << row_mask_width) - 1)
    col_mask = (cfg_masks >> row_mask_width) & ((1 << col_mask_width) - 1)

    if row_mask == 0:
        row_mask = (1 << row_mask_width) - 1
    if col_mask == 0:
        col_mask = (1 << col_mask_width) - 1

    return {
        "selected_cfg_id": selected_cfg_id,
        "selected_active_rows": selected_active_rows,
        "selected_active_cols": selected_active_cols,
        "selected_row_mask": row_mask,
        "selected_col_mask": col_mask,
    }


async def measure_until_event(dut, done_event, timeout_cycles=1000000):
    sampled_cycles = 0
    dma_busy_cycles = 0
    aw_wait_cycles = 0
    w_wait_cycles = 0
    b_wait_cycles = 0
    ar_wait_cycles = 0
    r_wait_cycles = 0
    memory_stall_cycles = 0

    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        sampled_cycles += 1
        dma_busy = int_value(dut.dma_busy)
        awvalid = int_value(dut.m_axi_awvalid)
        awready = int_value(dut.m_axi_awready)
        wvalid = int_value(dut.m_axi_wvalid)
        wready = int_value(dut.m_axi_wready)
        bvalid = int_value(dut.m_axi_bvalid)
        bready = int_value(dut.m_axi_bready)
        arvalid = int_value(dut.m_axi_arvalid)
        arready = int_value(dut.m_axi_arready)
        rvalid = int_value(dut.m_axi_rvalid)
        rready = int_value(dut.m_axi_rready)

        dma_busy_cycles += dma_busy

        aw_wait = awvalid and not awready
        w_wait = wvalid and not wready
        b_wait = bready and not bvalid
        ar_wait = arvalid and not arready
        r_wait = rready and not rvalid

        aw_wait_cycles += int(aw_wait)
        w_wait_cycles += int(w_wait)
        b_wait_cycles += int(b_wait)
        ar_wait_cycles += int(ar_wait)
        r_wait_cycles += int(r_wait)
        memory_stall_cycles += int(aw_wait or w_wait or b_wait or ar_wait or r_wait)

        if done_event.is_set():
            return {
                "sampled_cycles": sampled_cycles,
                "dma_busy_cycles": dma_busy_cycles,
                "aw_wait_cycles": aw_wait_cycles,
                "w_wait_cycles": w_wait_cycles,
                "b_wait_cycles": b_wait_cycles,
                "ar_wait_cycles": ar_wait_cycles,
                "r_wait_cycles": r_wait_cycles,
                "memory_stall_cycles": memory_stall_cycles,
            }

    raise RuntimeError("TIMEOUT waiting for done event in benchmark monitor")


async def run_benchmark_case(dut, mem, case, *, tile_m=8, tile_n=8):
    case_name = case["case_name"]
    M = int(case["M"])
    K = int(case["K"])
    N = int(case["N"])
    data_mode = case.get("data_mode", "random")
    seed = int(case.get("seed", 2026))
    baseA_word = int(case.get("baseA_word", DEFAULT_BASE_A_WORD))
    baseB_word = int(case.get("baseB_word", DEFAULT_BASE_B_WORD))
    baseC_word = int(case.get("baseC_word", DEFAULT_BASE_C_WORD))
    mem_cfg = case.get("memory", {})

    mem.configure(
        wait_prob=float(mem_cfg.get("wait_prob", 0.0)),
        max_wait=int(mem_cfg.get("max_wait", 1)),
    )
    mem.clear_memory()
    mem.clear_stats()

    random.seed(seed)
    A = gen_matrix(M, K, data_mode)
    B = gen_matrix_B(K, N, data_mode)
    C_ref = golden_matmul_s8_s32(A, B, M, K, N)

    output_words = max(1, M * N)
    guard_words = 4
    expected_prefill = preload_c_region(mem, baseC_word, output_words + guard_words)

    addr = baseA_word
    for row in A:
        for word in pack_s8_row(row):
            mem.load_word(addr, word)
            addr += 1

    addr = baseB_word
    for row in B:
        for word in pack_s8_row(row):
            mem.load_word(addr, word)
            addr += 1

    await bus_write(dut, 0x00, baseA_word)
    await bus_write(dut, 0x04, baseB_word)
    await bus_write(dut, 0x08, baseC_word)
    await bus_write(dut, 0x0C, M)
    await bus_write(dut, 0x10, K)
    await bus_write(dut, 0x14, N)
    await program_optional_array_config(dut, case)

    done_event = Event()
    monitor = cocotb.start_soon(measure_until_event(dut, done_event))
    start_ns = get_sim_time("ns")
    await bus_write(dut, 0x1C, 0x1)
    await wait_done_via_status(dut)
    end_ns = get_sim_time("ns")
    done_event.set()
    busy_window = await monitor
    await check_status_idle(dut)
    cfg_info = await read_optional_array_config(dut, default_rows=tile_m, default_cols=tile_n)

    if M > 0 and K > 0 and N > 0:
        for i in range(M):
            for j in range(N):
                raw = mem.read_word(baseC_word + i * N + j)
                got = u32_to_s32(raw)
                exp = C_ref[i][j]
                if got != exp:
                    dut._log.error(
                        f"{case_name}: C[{i},{j}] exp={exp} got={got} raw=0x{raw:08x}"
                    )
                    raise AssertionError("Benchmark GEMM mismatch")

    for off in range(M * N, output_words + guard_words):
        addr_word = baseC_word + off
        got = mem.read_word(addr_word)
        exp = expected_prefill[addr_word]
        if got != exp:
            raise AssertionError(
                f"{case_name}: guard word overwrite at addr=0x{addr_word:08x}"
            )

    a_words_total = M * packed_words_per_row(K)
    b_words_total = K * packed_words_per_row(N)
    c_words_total = M * N

    a_reads = mem.count_reads(baseA_word, a_words_total)
    b_reads = mem.count_reads(baseB_word, b_words_total)
    c_reads = mem.count_reads(baseC_word, c_words_total)
    c_writes = mem.count_writes(baseC_word, c_words_total)

    physical_pe_count = tile_m * tile_n
    configured_pe_count = cfg_info["selected_active_rows"] * cfg_info["selected_active_cols"]
    useful_macs = M * K * N
    latency_cycles = int(round((end_ns - start_ns) / CLOCK_PERIOD_NS))
    busy_cycles = latency_cycles
    throughput_mac_per_cycle = (useful_macs / latency_cycles) if latency_cycles else 0.0
    utilization = (useful_macs / (physical_pe_count * busy_cycles)) if busy_cycles else 0.0
    mapping_efficiency = (useful_macs / (configured_pe_count * busy_cycles)) if (busy_cycles and configured_pe_count) else 0.0
    memory_stall_ratio = (
        busy_window["memory_stall_cycles"] / latency_cycles if latency_cycles else 0.0
    )
    dma_busy_ratio = (busy_window["dma_busy_cycles"] / latency_cycles) if latency_cycles else 0.0

    eff_tile_m = cfg_info["selected_active_rows"]
    eff_tile_n = cfg_info["selected_active_cols"]
    m_tiles = (M + eff_tile_m - 1) // eff_tile_m if M > 0 else 0
    n_tiles = (N + eff_tile_n - 1) // eff_tile_n if N > 0 else 0
    k_tiles = (K + tile_m - 1) // tile_m if K > 0 else 0
    unique_a_words = max(1, a_words_total) if a_words_total > 0 else 0
    unique_b_words = max(1, b_words_total) if b_words_total > 0 else 0
    read_bytes = mem.read_beats * 4
    write_bytes = mem.write_beats * 4
    bytes_per_mac = ((read_bytes + write_bytes) / useful_macs) if useful_macs else 0.0
    read_bytes_per_mac = (read_bytes / useful_macs) if useful_macs else 0.0
    write_bytes_per_mac = (write_bytes / useful_macs) if useful_macs else 0.0
    cycles_per_mac = (latency_cycles / useful_macs) if useful_macs else 0.0
    output_slot_utilization = (
        (M * N) / (m_tiles * eff_tile_m * n_tiles * eff_tile_n)
        if (m_tiles and n_tiles and eff_tile_m and eff_tile_n)
        else 0.0
    )

    result = {
        "case_name": case_name,
        "workload": case.get("workload", case_name),
        "profile": case.get("profile", "custom"),
        "suite": case.get("suite", "default"),
        "case_group": case.get("case_group", case.get("workload", case_name)),
        "shape_tag": case.get("shape_tag"),
        "config_mode": case.get("config_mode", "default"),
        "M": M,
        "K": K,
        "N": N,
        "data_mode": data_mode,
        "memory": {
            "wait_prob": float(mem_cfg.get("wait_prob", 0.0)),
            "max_wait": int(mem_cfg.get("max_wait", 1)),
        },
        "auto_config_en": case.get("auto_config_en"),
        "manual_row_mask": case.get("manual_row_mask"),
        "manual_col_mask": case.get("manual_col_mask"),
        "selected_cfg_id": cfg_info["selected_cfg_id"],
        "selected_active_rows": cfg_info["selected_active_rows"],
        "selected_active_cols": cfg_info["selected_active_cols"],
        "selected_row_mask": cfg_info["selected_row_mask"],
        "selected_col_mask": cfg_info["selected_col_mask"],
        "physical_pe_count": physical_pe_count,
        "configured_pe_count": configured_pe_count,
        "useful_macs": useful_macs,
        "latency_cycles": latency_cycles,
        "cycles_per_mac": cycles_per_mac,
        "sys_busy_cycles": busy_cycles,
        "throughput_mac_per_cycle": throughput_mac_per_cycle,
        "array_utilization": utilization,
        "mapping_efficiency": mapping_efficiency,
        "output_slot_utilization": output_slot_utilization,
        "dma_busy_cycles": busy_window["dma_busy_cycles"],
        "dma_busy_ratio": dma_busy_ratio,
        "memory_stall_cycles": busy_window["memory_stall_cycles"],
        "memory_stall_ratio": memory_stall_ratio,
        "aw_wait_cycles": busy_window["aw_wait_cycles"],
        "w_wait_cycles": busy_window["w_wait_cycles"],
        "b_wait_cycles": busy_window["b_wait_cycles"],
        "ar_wait_cycles": busy_window["ar_wait_cycles"],
        "r_wait_cycles": busy_window["r_wait_cycles"],
        "a_reads": a_reads,
        "b_reads": b_reads,
        "c_reads": c_reads,
        "c_writes": c_writes,
        "read_beats": mem.read_beats,
        "write_beats": mem.write_beats,
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
        "bytes_per_mac": bytes_per_mac,
        "read_bytes_per_mac": read_bytes_per_mac,
        "write_bytes_per_mac": write_bytes_per_mac,
        "a_read_amplification": (a_reads / unique_a_words) if unique_a_words else 0.0,
        "b_read_amplification": (b_reads / unique_b_words) if unique_b_words else 0.0,
        "b_reuse_factor": ((m_tiles * b_words_total) / b_reads) if b_reads else 0.0,
        "m_tiles": m_tiles,
        "n_tiles": n_tiles,
        "k_tiles": k_tiles,
        "naive_b_reads_no_reuse": (m_tiles * b_words_total) if b_words_total else 0,
    }

    dut._log.info(
        f"BENCH {case_name}: latency={latency_cycles} busy={busy_cycles} "
        f"tput={throughput_mac_per_cycle:.4f} "
        f"util={utilization:.4f} A_reads={a_reads} B_reads={b_reads} C_writes={c_writes}"
    )
    return result
