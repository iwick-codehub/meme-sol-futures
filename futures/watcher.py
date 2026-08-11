#!/usr/bin/env python3
"""CONTRACT-001 escrow watcher — read-only, KRW spectroscope law.

Observes the escrow wallet and records what it sees. Never signs, never moves
funds, never calls anything but public read RPC.

One shot per invocation (cron/loop it). Writes:
  futures/logs/escrow_state.json   — current state (dashboard/health source)
  futures/logs/escrow_watch.log    — append-only, hash-chained observation log

Exit 0 = escrow intact (1,000,000 ACM). Exit 1 = balance deviates: before the
release window that means a breach of the irrevocable-sale escrow; on/after
Aug 31 11:59 EST it is the expected release. The state file says which.
"""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ESCROW_WALLET = "DsP3zSSrHeEwSHUvjiZo3brqeXDMS6CZB3DeRxBk2BNH"
ACM_MINT = "4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump"
EXPECTED_ACM = 1_000_000
RPC = "https://api.mainnet-beta.solana.com"
EST = timezone(timedelta(hours=-5))
RELEASE_AT = datetime(2026, 8, 31, 11, 59, tzinfo=EST)

LOGS = Path(__file__).parent / "logs"
STATE = LOGS / "escrow_state.json"
LOG = LOGS / "escrow_watch.log"


def rpc_balance() -> tuple[float, int]:
    """Return (ACM balance in escrow, slot) from public read RPC."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "getTokenAccountsByOwner",
        "params": [ESCROW_WALLET, {"mint": ACM_MINT}, {"encoding": "jsonParsed"}],
    }).encode()
    req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    result = data["result"]
    slot = result["context"]["slot"]
    total = sum(
        float(acct["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmountString"])
        for acct in result["value"])
    return total, slot


def chained_log(entry: dict) -> None:
    prev = "genesis"
    if LOG.exists():
        lines = LOG.read_text().strip().splitlines()
        if lines:
            prev = json.loads(lines[-1])["hash"]
    entry["prev"] = prev
    entry["hash"] = hashlib.sha256(
        json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with LOG.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    LOGS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    in_release_window = now >= RELEASE_AT.astimezone(timezone.utc)
    try:
        balance, slot = rpc_balance()
        error = None
    except Exception as exc:  # RPC failure is an observation, not a breach
        balance, slot, error = None, None, str(exc)

    if error:
        status = "RPC_ERROR"
    elif balance == EXPECTED_ACM:
        status = "INTACT"
    elif in_release_window:
        status = "RELEASED" if balance == 0 else "RELEASING"
    else:
        status = "BREACH"

    state = {
        "contract": "CONTRACT-001",
        "ts": now.isoformat(timespec="seconds"),
        "slot": slot,
        "escrow_wallet": ESCROW_WALLET,
        "balance_acm": balance,
        "expected_acm": EXPECTED_ACM,
        "release_at": RELEASE_AT.isoformat(),
        "in_release_window": in_release_window,
        "status": status,
        "error": error,
    }
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    chained_log(dict(state))
    print(f"{state['ts']} slot={slot} balance={balance} status={status}")
    return 0 if status in ("INTACT", "RELEASED", "RPC_ERROR") else 1


if __name__ == "__main__":
    raise SystemExit(main())
