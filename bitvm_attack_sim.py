"""
BitVM L2 Bridge — Existential Honesty & Timeout Attack Simulation
Harish M · Praatibh | National Sun Yat-sen University
"""

import time
import random
import sys
import os
import shutil

def get_width():
    return shutil.get_terminal_size((100, 24)).columns

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
WHITE   = '\033[97m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'

def hr(char='─', color=DIM):
    return f"{color}{char * get_width()}{RESET}"

def center(text, width=None):
    w = width or get_width()
    clean = ''.join(c for c in text if ord(c) >= 32)
    # strip ANSI for length calc
    import re
    plain = re.sub(r'\033\[[0-9;]*m', '', clean)
    pad = max(0, (w - len(plain)) // 2)
    return ' ' * pad + text

def print_header():
    os.system('cls' if sys.platform == 'win32' else 'clear')
    print()
    print(hr('═', CYAN))
    print(center(f"{BOLD}{CYAN} ₿  BitVM Layer-2 Bridge — Attack Simulation  ₿{RESET}"))
    print(center(f"{DIM}Existential Honesty Model | Timeout & Mempool Censorship{RESET}"))
    print(hr('═', CYAN))
    print()

def print_legend():
    print(f"  {CYAN}●{RESET} Challenge Window   {GREEN}●{RESET} Honest Tx   {RED}●{RESET} Spam/Attack Tx   {YELLOW}●{RESET} Warning\n")

def typewrite(text, delay=0.018, newline=True):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        print()

def status_line(icon, color, label, text):
    print(f"  {color}{icon}{RESET}  {BOLD}{label}{RESET}  {DIM}→{RESET}  {text}")

def mempool_bar(fraud_fee, spam_fees, capacity):
    """Visual mempool depth indicator."""
    all_fees = [fraud_fee] + spam_fees
    all_fees.sort(reverse=True)
    bar_w = min(40, get_width() - 30)
    out = []
    for i, f in enumerate(all_fees[:bar_w]):
        if f == fraud_fee:
            out.append(f"{GREEN}█{RESET}")
        else:
            out.append(f"{RED}▓{RESET}")
    # pad
    out += [f"{DIM}░{RESET}"] * max(0, bar_w - len(out))
    legend = f"  Mempool  [{' '.join(out[:bar_w])}]  Block cap: {capacity}"
    print(legend)

def simulate():
    print_header()
    print_legend()

    CHALLENGE_WINDOW = 6
    BLOCK_CAPACITY   = 3
    START_BLOCK      = 840_000
    FRAUD_FEE        = 55       # sats/vB — honest watcher's fee

    typewrite(f"  {DIM}Initialising bridge operator vault...{RESET}", 0.012)
    time.sleep(0.4)
    status_line('🔒', CYAN,  'Vault',    f"Operator pre-signed exit UTXO locked")
    status_line('⏱ ', CYAN,  'Window',  f"{CHALLENGE_WINDOW} blocks  (~{CHALLENGE_WINDOW * 10} min on mainnet)")
    status_line('📦', CYAN,  'Capacity', f"{BLOCK_CAPACITY} txs per block (congested chain)")
    print()
    time.sleep(0.6)

    print(hr('─', RED))
    typewrite(f"  {RED}{BOLD}[!] MALICIOUS EXIT DETECTED{RESET}", 0.015)
    typewrite(f"  {DIM}    Operator submitted fraudulent withdrawal — $1,265 BTC{RESET}", 0.010)
    print(hr('─', RED))
    print()
    time.sleep(0.8)

    typewrite(f"  {GREEN}[✓] Honest watcher identified fraud.{RESET}", 0.015)
    typewrite(f"  {GREEN}    Generating fraud proof challenge tx...{RESET}", 0.012)
    print()
    time.sleep(0.5)

    mempool = [{"id": "FraudProof#W1", "fee": FRAUD_FEE, "type": "honest"}]
    status_line('📡', GREEN, 'Broadcast', f"FraudProof#W1  fee={FRAUD_FEE} sats/vB")
    print()

    print(f"  {YELLOW}{BOLD}▶ ATTACK PHASE — Mempool Censorship via Fee Flooding{RESET}")
    typewrite(f"  {DIM}  Attacker saturates block space with junk transactions...{RESET}", 0.010)
    print()
    time.sleep(1.0)

    result = None

    for block_offset in range(CHALLENGE_WINDOW + 1):
        blocks_left = CHALLENGE_WINDOW - block_offset
        block_num   = START_BLOCK + block_offset

        print(hr('─', DIM))
        print(f"  {CYAN}{BOLD}Block {block_num:,}{RESET}  "
              f"{DIM}({block_offset + 1}/{CHALLENGE_WINDOW + 1})  "
              f"Blocks remaining in window: {YELLOW}{blocks_left}{RESET}")
        print()

        spam_fees = []
        for _ in range(5):
            fee = random.randint(85, 130)
            spam_fees.append(fee)
            mempool.append({"id": f"SpamTx#{random.randint(1000,9999)}", "fee": fee, "type": "spam"})

        mempool.sort(key=lambda x: x['fee'], reverse=True)

        fraud_in_pool = any(t['type'] == 'honest' for t in mempool)
        mempool_bar(FRAUD_FEE if fraud_in_pool else -1, spam_fees, BLOCK_CAPACITY)
        top_fee = mempool[0]['fee']
        print(f"  {DIM}Pool size: {len(mempool)} txs  │  Top fee: {top_fee} sats/vB  │  "
              f"Fraud proof fee: {FRAUD_FEE} sats/vB{RESET}")
        print()

        block   = mempool[:BLOCK_CAPACITY]
        mempool = mempool[BLOCK_CAPACITY:]

        fraud_mined = False
        print(f"  {DIM}Included in block:{RESET}")
        for tx in block:
            if tx['type'] == 'honest':
                print(f"    {GREEN}✔  {tx['id']:<22} fee={tx['fee']} sats/vB  ← FRAUD PROOF{RESET}")
                fraud_mined = True
            else:
                print(f"    {RED}✘  {tx['id']:<22} fee={tx['fee']} sats/vB  (spam){RESET}")
        print()

        if fraud_mined:
            result = 'success'
            break
        else:
            if blocks_left == 0:
                result = 'failure'
                break
            else:
                print(f"  {YELLOW}⚠  Fraud proof still in mempool — {blocks_left} block(s) remaining{RESET}")

        time.sleep(1.5)

    print(hr('═', CYAN))
    print()
    if result == 'success':
        print(center(f"{GREEN}{BOLD}✔  FRAUD PROOF CONFIRMED ON-CHAIN{RESET}"))
        print(center(f"{GREEN}Malicious operator slashed — funds returned to vault{RESET}"))
        print()
        print(center(f"{DIM}Existential honesty held: 1 honest watcher was enough{RESET}"))
    else:
        print(center(f"{RED}{BOLD}✘  CHALLENGE WINDOW EXPIRED — ATTACK SUCCEEDED{RESET}"))
        print(center(f"{RED}Fraudulent exit finalised — user funds stolen{RESET}"))
        print()
        print(center(f"{DIM}Existential honesty failed: watcher existed but was censored{RESET}"))
        print()
        print(f"  {YELLOW}Key finding:{RESET} BitVM's 1-of-N model requires the honest party")
        print(f"  to {BOLD}act in time{RESET}. Mempool censorship converts availability")
        print(f"  failure into a full security breach — even with active watchers.")
    print()
    print(hr('═', CYAN))
    print(f"  {DIM}Research: Harish M · Praatibh | National Sun Yat-sen University{RESET}")
    print()

if __name__ == "__main__":
    try:
        simulate()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Simulation aborted.{RESET}\n")