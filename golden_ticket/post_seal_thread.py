#!/usr/bin/env python3
"""One-off: post the Golden Ticket SEALED thread — 3 posts, 5 minutes apart.

Approved by Todd 2026-09-11. Resumable: progress is saved after every post, so
a rerun continues the thread instead of double-posting. Reuses tweet_top10's
credential loading and signed call; this file never reads or prints the keys.
"""
import datetime, json, re, sys, time
from pathlib import Path
import tweet_top10 as tt

HERE = Path(__file__).resolve().parent
STATE = HERE / "out" / "seal_thread_state.json"
GAP = 300
c = json.load(open(HERE / "out" / "golden_ticket_certificate.json"))
H, root, slot = c["holders"], c["merkle_root"], c["solana_slot"]
PEER = ["Grand Vizier", "Vizier", "Necromancer", "Wizard", "Prime Magi",
        "Magi", "Conjurer", "Evoker", "Apprentice", "Acolyte"]
frag = lambda w: f"{w[:6]}…{w[-4:]}"   # pulled from the certificate, never retyped

POSTS = [
    "🎟️ THE GOLDEN TICKET IS SEALED.\n\n"
    f"Noon ET, Labor Day. Solana slot {slot:,}.\n\n"
    "The Top 100 $ACM holders, locked forever in one Merkle root:\n"
    f"{root[:8]}…{root[-6:]}\n\n"
    "Ten of them now hold the Peerage of the Castle. For all time.",

    "THE PEERAGE OF THE CASTLE 👑\n\n" + "\n".join(
        f"{h['rank']} {t} {frag(h['wallet'])}" for h, t in zip(H[:10], PEER)),

    "A correction, in the open: our automated board posts kept running for four days "
    "after the freeze. They were not part of the Golden Ticket. "
    f"The sealed list at slot {slot:,} is the only one that counts.",
]


def xlen(s):
    """X weighting: URLs = 23; code points in the light ranges = 1; else 2."""
    s = re.sub(r"https?://\S+", "x" * 23, s).replace("️", "")
    light = [(0, 4351), (8192, 8205), (8208, 8223), (8242, 8247)]
    return sum(1 if any(a <= ord(ch) <= b for a, b in light) else 2 for ch in s)


for i, p in enumerate(POSTS, 1):          # refuse to start a thread that can't finish
    assert xlen(p) <= 280, f"post {i} is {xlen(p)}/280"

if "--dry" in sys.argv:
    for i, p in enumerate(POSTS, 1):
        print(f"--- post {i} ({xlen(p)}/280)\n{p}\n")
    sys.exit(0)

st = json.loads(STATE.read_text()) if STATE.exists() else {"ids": [], "at": []}
e = tt.env()
for i in range(len(st["ids"]), len(POSTS)):
    if st["at"]:
        wait = st["at"][-1] + GAP - time.time()
        if wait > 0:
            print(f"waiting {int(wait)}s before post {i + 1}", flush=True)
            time.sleep(wait)
    body = {"text": POSTS[i]}
    if st["ids"]:
        body["reply"] = {"in_reply_to_tweet_id": st["ids"][-1]}
    res = tt._auth_call(e, "https://api.x.com/2/tweets", json.dumps(body).encode(),
                        {"Content-Type": "application/json"})
    tid = (res or {}).get("data", {}).get("id")
    if not tid:
        print(f"POST {i + 1} FAILED — thread stopped, nothing further posted: {res}", flush=True)
        sys.exit(1)
    st["ids"].append(tid)
    st["at"].append(time.time())
    STATE.write_text(json.dumps(st, indent=1))
    print(f"posted {i + 1}/3 at {datetime.datetime.now():%I:%M:%S %p} — https://x.com/i/status/{tid}",
          flush=True)
print("THREAD COMPLETE")
