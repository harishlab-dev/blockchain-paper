# ₿ Bitcoin L2 Bridge Security — Empirical Prototypes

> **Research prototypes** accompanying the paper  
> *"A Comparative Security Analysis of Bitcoin Layer-2 Bridges: Multisignature vs BitVM-Based Recovery Models"*  
> Harish M & Praatibh · Dept. of Computer Science & Engineering · National Sun Yat-sen University · May 2026

---

## Overview

This repository contains two standalone Python simulations that empirically validate the core security trade-offs of Bitcoin Layer-2 bridge designs:

| Script | Models | Key question |
|---|---|---|
| `bitvm_attack_sim.py` | BitVM / Bitlayer | Can a censor defeat an honest watcher by flooding the mempool? |
| `zk_latency_bench.py` | ZK Rollup / Citrea | How does proof generation latency scale with transaction batch size? |

Together they provide concrete, reproducible evidence for the claim that bridge security is a balance of **trust**, **participation**, and **computation** — each approach shifts risk rather than eliminating it.

---

## Repository Structure

```
bitcoin-l2-bridge-security/
├── bitvm_attack_sim.py        # Prototype 1 — BitVM timeout & censorship attack
├── zk_latency_bench.py        # Prototype 2 — ZK proof generation latency benchmark
├── README.md
└── report/
    └── BitVM_Bridge_Technical_Report.pdf   # Full technical report (optional)
```

---

## Prototype 1 — BitVM Timeout & Censorship Simulator

### What it does

Simulates a **mempool censorship timeout attack** against a BitVM-based bridge.

A fraudulent operator submits a malicious withdrawal. An honest watcher detects it and broadcasts a fraud-proof challenge transaction. Meanwhile, an attacker floods the mempool with high-fee spam to prevent the fraud proof from being confirmed before the challenge window closes.

```
Operator submits fraudulent exit
        │
        ▼
Challenge window opens (N blocks)
        │
        ├─ Honest watcher broadcasts fraud proof (low fee)
        │
        └─ Attacker floods mempool (high-fee spam)
                │
                ├─ Fraud proof confirmed  →  Attack FAILS  ✔
                └─ Window expires         →  Attack SUCCEEDS  ✘
```

### Key parameters

| Parameter | Default | Description |
|---|---|---|
| `CHALLENGE_WINDOW` | `6` blocks | Duration of the fraud-proof window (~60 min on mainnet) |
| `BLOCK_CAPACITY` | `3` txs | Transactions mined per block (simulates congestion) |
| `FRAUD_FEE` | `55` sat/vB | Fee offered by the honest watcher |
| Attacker fee range | `85–130` sat/vB | Spam transaction fees (always outbids the watcher) |

Adjust these at the top of the file to model different congestion levels and adversarial budgets.

### What it demonstrates

- **C2 — Liveness (Low):** BitVM bridges depend on timely *on-chain* confirmation of the fraud proof, not just the watcher being honest.
- **C5 — Latency Sensitivity (High):** Block congestion during the challenge window directly converts to a security failure.
- **Core finding:** *Existential honesty is necessary but not sufficient.* Even an active, honest watcher can be silenced by a well-funded attacker.

### Sample output

```
══════════════════════════════════════════════════════════════════
   ₿  BitVM Layer-2 Bridge — Attack Simulation  ₿
   Existential Honesty Model | Timeout & Mempool Censorship
══════════════════════════════════════════════════════════════════

  ● Challenge Window   ● Honest Tx   ● Spam/Attack Tx   ● Warning

  🔒  Vault     →  Operator pre-signed exit UTXO locked
  ⏱   Window   →  6 blocks  (~60 min on mainnet)
  📦  Capacity  →  3 txs per block (congested chain)

[!] MALICIOUS EXIT DETECTED
    Operator submitted fraudulent withdrawal — $1,265 BTC

[✓] Honest watcher identified fraud.
    Generating fraud proof challenge tx...

Block 840,000  (1/7)  Blocks remaining in window: 6
  Mempool  [▓ ▓ ▓ ▓ ▓ █ ▓ ▓ ░ ░]  Block cap: 3
  Pool size: 6 txs  │  Top fee: 128 sats/vB  │  Fraud proof fee: 55 sats/vB

  Included in block:
    ✘  SpamTx#4821          fee=128 sats/vB  (spam)
    ✘  SpamTx#3017          fee=115 sats/vB  (spam)
    ✘  SpamTx#7823          fee=97  sats/vB  (spam)

  ⚠  Fraud proof still in mempool — 6 block(s) remaining
  ...

══════════════════════════════════════════════════════════════════
         ✘  CHALLENGE WINDOW EXPIRED — ATTACK SUCCEEDED
              Fraudulent exit finalised — user funds stolen

     Existential honesty failed: watcher existed but was censored
══════════════════════════════════════════════════════════════════
```

---

## Prototype 2 — ZK Proof Generation Latency Benchmark

### What it does

Benchmarks the **computational cost of ZK-proof-based bridge security** by measuring how proof generation time scales with transaction batch size. Uses a recursive SHA-256 hashing chain as a deterministic, CPU-bound proxy for zk-SNARK / STARK proving workloads.

```
Batch of N transactions
        │
        ▼
Recursive SHA-256 chain  (N × base_ops iterations)
        │
        ▼
Measure wall-clock time, CPU%, RAM usage
        │
        ▼
Report: latency, throughput (tx/s), scaling ratio vs Batch-10
```

### Key parameters

| Parameter | Default | Description |
|---|---|---|
| `batch_sizes` | `[10, 50, 150, 500]` | Transaction counts per proof cycle |
| `base_ops` | `20,000` | Hashing iterations per transaction (proof complexity proxy) |
| `chunks` | `60` | Progress update granularity |

### What it demonstrates

- **C3 — Fraud Detection (Very Strong):** An invalid batch cannot produce a valid proof — correctness is enforced before any state transition is accepted.
- **C6 — Decentralisation (Very High):** Security holds with zero active watchers; any node can independently verify the posted proof.
- **C5 — Latency Sensitivity (Medium):** Security is unaffected by confirmation delays, but large batches introduce user-visible confirmation latency.
- **Core finding:** Proof generation time scales linearly with batch size. ZK trades timing risk (BitVM) for computation risk.

### Sample output

```
══════════════════════════════════════════════════════════════════
  🔐  ZK-Rollup (Citrea) — Proof Generation Latency Benchmark
  Simulating cryptographic proof generation scaling on Bitcoin L2
══════════════════════════════════════════════════════════════════

  System:  8-thread CPU  │  16.0 GB RAM  │  Python 3.11.4  │  linux

   Batch        Ops        Result    Throughput   Notes
  ──────  ──────────  ──────────  ──────────────  ────────────────────
    10     200,000      0.251s       39.8 tx/s   ✔ Suitable for low-volume exits
    50   1,000,000      1.253s       39.9 tx/s   ~ Moderate load, acceptable
   150   3,000,000      3.761s       39.9 tx/s   ⚠ High compute — proof delay risk
   500  10,000,000     12.540s       39.9 tx/s   ⚠ High compute — proof delay risk

  Summary — Proof Generation Scaling
  ──────  ──────────  ──────────  ──────────────  ──────────────────────────────
   Batch    Time (s)    tx/s       vs Batch-10    Security Model
      10       0.251      39.8           1.0×    ZK proof — no watcher needed
      50       1.253      39.9           5.0×    ZK proof — no watcher needed
     150       3.761      39.9          15.0×    ZK proof — no watcher needed
     500      12.540      39.9          49.9×    ZK proof — no watcher needed
```

---

## Requirements

### Minimum (both scripts)

- Python **3.9+**
- No external dependencies — stdlib only (`hashlib`, `time`, `random`, `os`, `shutil`, `sys`)

### Optional (recommended for Prototype 2)

```bash
pip install psutil
```

Enables live **CPU% and RAM usage** telemetry in the ZK benchmark progress bar.

### ANSI colour support

Both scripts use ANSI escape codes for terminal colouring.

- **Linux / macOS:** Works out of the box in any standard terminal.
- **Windows:** Requires Windows 10 build 1511+ (Virtual Terminal enabled automatically by the script via `SetConsoleMode`). Use Windows Terminal or PowerShell for best results.

---

## Running the Simulations

### Clone the repository

```bash
git clone https://github.com/<your-username>/bitcoin-l2-bridge-security.git
cd bitcoin-l2-bridge-security
```

### Prototype 1 — BitVM Attack Simulator

```bash
python bitvm_attack_sim.py
```

To experiment with different scenarios, edit the constants near the top of the file:

```python
CHALLENGE_WINDOW = 6    # Try 3 for a tighter window
BLOCK_CAPACITY   = 3    # Try 10 to simulate an uncongested chain
FRAUD_FEE        = 55   # Try 200 to see the watcher outbid the attacker
```

### Prototype 2 — ZK Latency Benchmark

```bash
# Without resource telemetry
python zk_latency_bench.py

# With CPU/RAM monitoring
pip install psutil && python zk_latency_bench.py
```

To extend the benchmark with custom batch sizes:

```python
batch_sizes = [10, 50, 150, 500, 1000]   # add larger batches
base_ops    = 20_000                      # increase for heavier simulation
```

---

## Security Model Comparison

| Property | BitVM (Bitlayer) | ZK Rollup (Citrea) |
|---|---|---|
| **Trust assumption** | ≥1 honest, *active* watcher | Soundness of the proof system |
| **Liveness** | 🔴 Low — timely challenge required | 🟢 High — no participant needed |
| **Fraud detection** | 🟡 Strong — reactive (post-facto) | 🟢 Very Strong — preventive |
| **Key attack surface** | Mempool censorship / timeout | Proof generation bottleneck |
| **Latency sensitivity** | 🔴 High — fixed challenge window | 🟡 Medium — scales with batch |
| **Decentralisation** | 🟡 High — open challenger set | 🟢 Very High — no challenger needed |
| **Computational cost** | 🟢 Low | 🔴 High — proving is expensive |

---

## Limitations

These are research-grade simulations, not production implementations.

- **BitVM simulator** uses a simplified mempool model (no RBF, no CPFP, no dynamic fee bumping). A real watcher could partially mitigate censorship by fee-bumping aggressively.
- **ZK benchmark** uses SHA-256 chaining as a workload proxy. It preserves the linear scaling property of real ZK provers but does not model parallelism or hardware acceleration (GPUs, FPGAs).
- Neither prototype models the **economic cost to the attacker** of sustaining a fee flood for ~60 minutes on mainnet.

---

## Citation

If you use these prototypes in academic work, please cite:

```bibtex
@techreport{harish2026btcl2,
  title   = {A Comparative Security Analysis of Bitcoin Layer-2 Bridges:
             Multisignature vs BitVM-Based Recovery Models},
  author  = {Harish M and Praatibh},
  institution = {National Sun Yat-sen University},
  year    = {2026},
  month   = {May}
}
```

---

## License

This project is released for academic and research purposes.  
© 2026 Harish M & Praatibh — National Sun Yat-sen University
