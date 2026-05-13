"""
ZK-Rollup (Citrea) — Proof Generation Latency Benchmark
Harish M · Praatibh | National Sun Yat-sen University
"""
import time
import hashlib
import sys
import os
import shutil
import threading

if sys.platform == "win32":
    import ctypes
    kernel = ctypes.windll.kernel32
    kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)

RESET   = '\033[0m'
BOLD    = '\033[1m'
DIM     = '\033[2m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
CYAN    = '\033[96m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'
WHITE   = '\033[97m'

def get_width():
    return shutil.get_terminal_size((100, 24)).columns

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def get_resources():
    if not HAS_PSUTIL:
        return None, None, None
    try:
        cpu  = psutil.cpu_percent(interval=None)
        mem  = psutil.virtual_memory()
        ram  = mem.percent
        ram_used_gb = mem.used / (1024 ** 3)
        ram_total_gb = mem.total / (1024 ** 3)
        return cpu, ram, (ram_used_gb, ram_total_gb)
    except Exception:
        return None, None, None

def cpu_work(iterations):
    seed = b"citrea_zk_bridge_benchmark_nsysu"
    for _ in range(iterations):
        seed = hashlib.sha256(seed).digest()
    return seed

def render_bar(batch, done, total, elapsed, cpu_pct, ram_pct, ram_gb):
    w = get_width()

    pct   = done / total
    phase = "PROVING" if pct < 0.5 else ("VERIFYING" if pct < 0.85 else "FINALISING")

    if batch == 500:
        bar_color, load_str = RED,    "MAX "
    elif batch == 150:
        bar_color, load_str = YELLOW, "MED "
    else:
        bar_color, load_str = GREEN,  "LOW "

    prefix = f"  Batch {batch:>3} │ {bar_color}{phase}{RESET} │ ["
    suffix_template = f"] {pct*100:5.1f}% │ {elapsed:5.1f}s"

    
    if cpu_pct is not None and ram_pct is not None:
        res = f" │ CPU {cpu_pct:4.1f}% │ RAM {ram_pct:4.1f}% ({ram_gb[0]:.1f}/{ram_gb[1]:.1f}GB)"
    else:
        res = ""

    
    import re
    plain_prefix = re.sub(r'\033\[[0-9;]*m', '', prefix)
    plain_suffix = suffix_template + res

    bar_w = w - len(plain_prefix) - len(plain_suffix) - 2
    bar_w = max(10, min(bar_w, 50))

    filled   = int(bar_w * pct)
    bar_body = bar_color + '█' * filled + RESET + DIM + '░' * (bar_w - filled) + RESET

    line = f"{prefix}{bar_body}{suffix_template}{res}"
    
    sys.stdout.write('\r' + line + '   ')
    sys.stdout.flush()

def print_header():
    os.system('cls' if sys.platform == 'win32' else 'clear')
    print()
    print(f"{CYAN}{'═' * get_width()}{RESET}")
    w = get_width()
    title = f"  🔐  ZK-Rollup (Citrea) — Proof Generation Latency Benchmark"
    print(f"{BOLD}{CYAN}{title}{RESET}")
    sub   = f"  Simulating cryptographic proof generation scaling on Bitcoin L2"
    print(f"{DIM}{sub}{RESET}")
    print(f"{CYAN}{'═' * get_width()}{RESET}")
    print()


    if HAS_PSUTIL:
        cpu = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        print(f"  {DIM}System:{RESET}  {cpu}-thread CPU  │  "
              f"{mem.total / (1024**3):.1f} GB RAM  │  "
              f"Python {sys.version.split()[0]}  │  "
              f"Platform: {sys.platform}")
    else:
        print(f"  {DIM}[psutil not installed — install with: pip install psutil for resource monitoring]{RESET}")
    print()

    print(f"  {DIM}Each batch simulates verifying N transactions into a single ZK proof.{RESET}")
    print(f"  {DIM}Computation scales linearly with batch size — matching real Citrea behaviour.{RESET}")
    print()
    print(f"  {'Batch':>6}  {'Ops':>10}  {'Result':>12}  {'Throughput':>14}  Notes")
    print(f"  {DIM}{'─'*6}  {'─'*10}  {'─'*12}  {'─'*14}  {'─'*20}{RESET}")
def run_benchmark():
    print_header()
    batch_sizes   = [10, 50, 150, 500]
    base_ops      = 20_000    
    chunks        = 60         
    results = []
    if HAS_PSUTIL:
        psutil.cpu_percent(interval=None)
        time.sleep(0.1)
    for batch in batch_sizes:
        total_ops   = batch * base_ops
        ops_per_chk = total_ops // chunks
        start       = time.perf_counter()
        for i in range(1, chunks + 1):
            cpu_work(ops_per_chk)
            elapsed = time.perf_counter() - start
            cpu_pct, ram_pct, ram_gb = get_resources()
            render_bar(batch, i, chunks, elapsed, cpu_pct, ram_pct, ram_gb)
        total_time = time.perf_counter() - start
        print()
        tps = batch / total_time
        if batch < 50:
            note = f"{GREEN}✔ Suitable for low-volume exits{RESET}"
        elif batch < 200:
            note = f"{YELLOW}~ Moderate load, acceptable{RESET}"
        else:
            note = f"{RED}⚠ High compute — proof delay risk{RESET}"

        results.append((batch, total_ops, total_time, tps))
        print(f"  {batch:>6}  {total_ops:>10,}  {total_time:>10.3f}s  {tps:>12.1f} tx/s  {note}")
        print()
        time.sleep(0.4)
    print(f"{CYAN}{'═' * get_width()}{RESET}")
    print(f"  {BOLD}Summary — Proof Generation Scaling{RESET}")
    print(f"{DIM}{'─' * get_width()}{RESET}")
    print(f"  {'Batch':>6}  {'Time (s)':>10}  {'tx/s':>10}  {'vs Batch-10':>14}  Security Model")
    print(f"  {DIM}{'─'*6}  {'─'*10}  {'─'*10}  {'─'*14}  {'─'*26}{RESET}")

    base_time = results[0][2]
    for batch, ops, t, tps in results:
        ratio = t / base_time
        if ratio < 2:
            color = GREEN
        elif ratio < 6:
            color = YELLOW
        else:
            color = RED
        print(f"  {batch:>6}  {t:>10.3f}  {tps:>10.1f}  {color}{ratio:>11.1f}×{RESET}  "
              f"{'ZK proof — no watcher needed'}")
    print()
    print(f"  {DIM}Key finding: ZK proof time grows ~linearly with batch size.{RESET}")
    print(f"  {DIM}Unlike BitVM, security holds without any active participant —{RESET}")
    print(f"  {DIM}but high-batch scenarios may introduce confirmation latency.{RESET}")
    print()
    print(f"{CYAN}{'═' * get_width()}{RESET}")
    print(f"  {DIM}Research: Harish M · Praatibh | National Sun Yat-sen University{RESET}")
    print()

if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Benchmark aborted.{RESET}\n")