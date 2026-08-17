#!/usr/bin/env python3
"""TOP 100 GOLDEN TICKET — ACM holder leaderboard + sealed snapshot.

  top100.py live    -> refresh the leaderboard JSON baked into the site page
                       (cron every few minutes until the freeze)
  top100.py checkpoint -> save the noon/midnight ET reference ranks (MOVE column
                       + Peerage-change banner measure against this, not the 60s refresh)
  top100.py freeze  -> THE authoritative snapshot at the appointed instant:
                       ranks holders, builds the Merkle root, writes the
                       sealed certificate + per-holder proofs, republishes
                       the page as FROZEN.

Freeze instant: Labor Day, Monday Sept 7, 2026, 12:00 PM Eastern (EDT) =
16:00:00 UTC. The snapshot records the Solana slot so anyone can re-derive
the identical root independently.

Rules (Todd, 2026-08-12):
  - Aggregate by OWNER wallet (a wallet may hold several token accounts).
  - EXCLUDE non-humans: the two Streamflow lock escrows, the PumpSwap pool,
    house wallets, and Contract One's escrow. Excluded rows are shown
    separately, never ranked.
  - No anti-gaming: simple, honest — "can't un-game crypto."
"""
import datetime
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent
PAGE = REPO / "futures" / "shopify" / "body_golden_ticket.html"
OUT = HERE / "out"
CHECKPOINT = HERE / "checkpoint.json"   # ranks as of the last noon/midnight ET
HISTORY = HERE / "history.json"          # EVERY checkpoint, all 100 rows, forever
HISTORY_CSV = HERE / "history.csv"       # same, flat, for spreadsheets
PEERAGE = ["Grand Vizier", "Vizier", "Necromancer", "Wizard", "Prime Magi",
           "Magi", "Conjurer", "Evoker", "Apprentice", "Acolyte"]
RPC = "https://api.mainnet-beta.solana.com"
MINT = "4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
FREEZE_UTC = "2026-09-07T16:00:00Z"

EXCLUDE = {
    "ABdGyTVQuemWxGWQTqeXCeXZ79prw7p9VtnTkhiWkQQ9": "Streamflow lock escrow — Lock 1 (402,717,631)",
    "7FdE5s2ejBX6g6socL3UrXFHaP79GUykMoRP8jhLsA4f": "Streamflow lock escrow — Lock 2 (97,282,369)",
    "HKSDMJ6KThscZXMVVuS24wvK3WGzfuepQhwdKCjHKEpZ": "PumpSwap liquidity pool",
    "Fc8T5MKEsqkK24JpQv8VNmk7cNehTN1RuixTtr1RUyho": "House — ACM creator wallet",
    "GNkKQWa4XHdvgF1x4edV3qF54xdz3LykWyd8cgWnVsHQ": "House — lock recipient wallet",
    "DsP3zSSrHeEwSHUvjiZo3brqeXDMS6CZB3DeRxBk2BNH": "Contract One escrow (house after Aug 31)",
    "3n2ETkQbVqNFaPAx8Sbcha5Vp6PZH1AsnqXioiGTixx9": "House — Todd's liquid account",
}


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["result"]


def snapshot():
    slot = rpc("getSlot", [{"commitment": "finalized"}])
    accts = rpc("getProgramAccounts", [TOKEN_PROGRAM, {
        "encoding": "jsonParsed", "commitment": "finalized",
        "filters": [{"dataSize": 165}, {"memcmp": {"offset": 0, "bytes": MINT}}]}])
    owners = {}
    for a in accts:
        info = a["account"]["data"]["parsed"]["info"]
        raw = int(info["tokenAmount"]["amount"])
        if raw > 0:
            owners[info["owner"]] = owners.get(info["owner"], 0) + raw
    dec = int(accts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"]) if accts else 6
    ranked = sorted(((o, b) for o, b in owners.items() if o not in EXCLUDE), key=lambda kv: -kv[1])
    excluded = [(o, owners.get(o, 0), why) for o, why in EXCLUDE.items() if owners.get(o, 0) > 0]
    return {"slot": slot, "decimals": dec, "holders": len(owners),
            "top": ranked[:100], "excluded": excluded,
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}


def leaf(rank, owner, raw):
    return hashlib.sha256(f"{rank}|{owner}|{raw}".encode()).hexdigest()


def merkle(leaves):
    """Returns (root, proofs) — proofs[i] = list of (sibling_hex, side)."""
    if not leaves:
        return hashlib.sha256(b"empty").hexdigest(), []
    layers = [leaves[:]]
    while len(layers[-1]) > 1:
        cur = layers[-1]
        if len(cur) % 2:
            cur = cur + [cur[-1]]
        layers.append([hashlib.sha256((cur[i] + cur[i + 1]).encode()).hexdigest()
                       for i in range(0, len(cur), 2)])
    proofs = []
    for i in range(len(leaves)):
        p, idx = [], i
        for layer in layers[:-1]:
            L = layer if len(layer) % 2 == 0 else layer + [layer[-1]]
            sib = idx ^ 1
            p.append((L[sib], "R" if sib > idx else "L"))
            idx //= 2
        proofs.append(p)
    return layers[-1][0], proofs


def load_checkpoint():
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return None


def save_checkpoint(snap, label=None):
    prev = load_checkpoint() or {"ranks": {}}
    dec = snap["decimals"]
    CHECKPOINT.write_text(json.dumps({
        "taken": snap["ts"], "slot": snap["slot"],
        "ranks": {o: i + 1 for i, (o, _) in enumerate(snap["top"])},
        "peerage": [o for o, _ in snap["top"][:10]],
    }, indent=0))
    # permanent history: every checkpoint, all 100 rows, with movement vs the one before
    hist = json.loads(HISTORY.read_text()) if HISTORY.exists() else {"checkpoints": []}
    rows = []
    for i, (o, raw) in enumerate(snap["top"]):
        was = prev["ranks"].get(o)
        rows.append({"rank": i + 1, "wallet": o, "balance": raw / 10 ** dec,
                     "prev_rank": was, "move": None if was is None else was - (i + 1),
                     "title": PEERAGE[i] if i < 10 else None})
    entry = {"label": label or ("noon ET" if datetime.datetime.fromisoformat(snap["ts"]).astimezone(
                 datetime.timezone(datetime.timedelta(hours=-4))).hour == 12 else "midnight ET"),
             "taken_utc": snap["ts"], "slot": snap["slot"], "holders": snap["holders"], "rows": rows}
    hist["checkpoints"].append(entry)
    HISTORY.write_text(json.dumps(hist, indent=1))
    with HISTORY_CSV.open("a") as f:
        if f.tell() == 0:
            f.write("checkpoint_label,taken_utc,slot,rank,title,wallet,balance,prev_rank,move\n")
        for r in rows:
            f.write(f"{entry['label']},{snap['ts']},{snap['slot']},{r['rank']},{r['title'] or ''},"
                    f"{r['wallet']},{r['balance']:.6f},{'' if r['prev_rank'] is None else r['prev_rank']},"
                    f"{'' if r['move'] is None else r['move']}\n")


def bake(snap, frozen, cert=None):
    dec = snap["decimals"]
    cp = load_checkpoint() or {"taken": None, "ranks": {}, "peerage": []}
    prev = cp["ranks"]
    moves = []
    top_rows = []
    for i, (o, raw) in enumerate(snap["top"]):
        rank = i + 1
        was = prev.get(o)
        delta = None if was is None else was - rank   # + = climbed
        top_rows.append({"rank": rank, "wallet": o, "balance": raw / 10 ** dec,
                         "was": was, "delta": delta})
    # Peerage changes since checkpoint
    old_peer = cp.get("peerage", [])
    for i, (o, _) in enumerate(snap["top"][:10]):
        if i < len(old_peer) and old_peer[i] != o:
            moves.append({"title": PEERAGE[i], "rank": i + 1, "wallet": o,
                          "kind": "NEW" if o not in old_peer else "MOVED"})
    payload = {
        "frozen": frozen, "slot": snap["slot"], "ts": snap["ts"],
        "holders": snap["holders"], "freeze_utc": FREEZE_UTC,
        "checkpoint": cp.get("taken"), "moves": moves,
        "top": top_rows,
        "excluded": [{"wallet": o, "balance": raw / 10 ** dec, "why": why}
                     for o, raw, why in snap["excluded"]],
        "root": (cert or {}).get("merkle_root"),
    }
    html = PAGE.read_text()
    blob = "/*GT_START*/var GT=" + json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + ";/*GT_END*/"
    new = re.sub(r"/\*GT_START\*/.*?/\*GT_END\*/", lambda _m: blob, html, flags=re.S)
    PAGE.write_text(new)
    subprocess.run([sys.executable, str(REPO / "futures" / "shopify" / "publish.py")], check=True)


def freeze(snap):
    OUT.mkdir(exist_ok=True)
    leaves = [leaf(i + 1, o, raw) for i, (o, raw) in enumerate(snap["top"])]
    root, proofs = merkle(leaves)
    cert = {
        "instrument": "ACM Top 100 Golden Ticket — MTC certification",
        "freeze_instant_utc": FREEZE_UTC, "taken_utc": snap["ts"],
        "solana_slot": snap["slot"], "mint": MINT,
        "leaf_rule": "sha256(f'{rank}|{owner}|{raw_balance}')",
        "tree_rule": "sha256(left+right) over hex strings, odd node duplicated",
        "excluded": [{"wallet": o, "why": why} for o, _, why in snap["excluded"]],
        "merkle_root": root,
        "holders": [{"rank": i + 1, "wallet": o, "raw_balance": raw,
                     "leaf": leaves[i], "proof": proofs[i]}
                    for i, (o, raw) in enumerate(snap["top"])],
    }
    (OUT / "golden_ticket_certificate.json").write_text(json.dumps(cert, indent=1))
    (OUT / "MERKLE_ROOT.txt").write_text(root + "\n")
    print(f"FROZEN at slot {snap['slot']} — root {root}")
    return cert


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    snap = snapshot()
    if mode == "checkpoint":
        save_checkpoint(snap, sys.argv[2] if len(sys.argv) > 2 else None)
        bake(snap, False)
        subprocess.run([sys.executable, str(HERE / "history_build.py")], check=True)
        print(f"checkpoint saved at slot {snap['slot']} ({snap['ts']})")
    elif mode == "freeze":
        cert = freeze(snap)
        bake(snap, True, cert)
    else:
        bake(snap, False)
        print(f"live: slot {snap['slot']}, {snap['holders']} holders, top #{1}: "
              f"{snap['top'][0][0][:8]}… {snap['top'][0][1]/10**snap['decimals']:,.0f}")
