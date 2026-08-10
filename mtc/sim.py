#!/usr/bin/env python3
"""Sim-2.0 driver — runs a season of promotions end to end.

NOTHING HERE IS REAL. No chain writes, no funded wallets, no scanners. Brands
are P&G names used as TEST FIXTURES ONLY to make the flow legible; there is no
relationship, agreement or endorsement implied.

What it exercises, in order:
    provision readers -> fund offers -> enrol members -> push MTCs ->
    redeem (incl. offline, duplicate and expired attempts) -> sweep expiries ->
    anchor the week -> verify the chain
"""
from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))

import walmart_cal as cal
from engine import Engine

random.seed(20260803)          # reproducible: the same run twice is the same run

# TEST FIXTURES ONLY -- illustrative, not commercial relationships
BRANDS = [
    ("PG-TIDE",   "Procter & Gamble", "Tide Pods 42ct",        1.50),
    ("PG-DAWN",   "Procter & Gamble", "Dawn Powerwash 16oz",   1.00),
    ("PG-CHRM",   "Procter & Gamble", "Charmin Ultra 12mega",  2.00),
    ("PG-GILL",   "Procter & Gamble", "Gillette Labs Razor",   3.00),
    ("PG-OLAY",   "Procter & Gamble", "Olay Regenerist 1.7oz", 2.50),
]
ARCADES = ["ARC-CINCY-01", "ARC-DAYTON-01", "ARC-COLUMBUS-01"]


def run(members=140, verbose=True):
    fy, wk = cal.current()
    E = Engine("sim")
    say = print if verbose else (lambda *a, **k: None)

    say(f"\n{'='*72}\n  SIM-2.0  ·  {cal.label(fy, wk)}\n"
        f"  all brands are TEST FIXTURES · no chain writes · no funded wallets\n{'='*72}\n")

    say("01  PROVISION READERS  (each arcade gets its own signing key)")
    for a in ARCADES:
        E.add_reader(a)
        say(f"      {a}  key issued")

    say("\n02  FUND OFFERS  (windows in Walmart weeks: 1 min, 52 max)")
    plans = [(BRANDS[0], wk, 1, 300), (BRANDS[1], wk, 2, 250),
             (BRANDS[2], wk, 4, 200), (BRANDS[3], wk, 13, 150),
             (BRANDS[4], wk, 52, 100)]
    for (oid, brand, item, val), sw, weeks, cap in plans:
        o = E.add_offer(f"{oid}-W{sw}", brand, item, fy, sw, weeks, val, cap)
        say(f"      {o['id']:16s} {item:24s} ${val:.2f}  "
            f"WK{sw}+{weeks:2d}  closes {o['closes'][:10]}  cap {cap}")

    say(f"\n03  ENROL MEMBERS  (mint wallet we custody, push 1 $ACM)")
    addrs = [E.enroll(f"user-{i:04d}")["address"] for i in range(members)]
    say(f"      {len(addrs)} wallets minted, 1 $ACM each, "
        f"{E.s['acm_pushed']} ACM out of float")
    say(f"      sample: {addrs[0]}")

    say("\n04  PUSH MTCs  (eligibility checked: >=1 $ACM)")
    issued = []
    for oid in list(E.s["offers"]):
        o = E.s["offers"][oid]
        for a in random.sample(addrs, min(len(addrs), o["cap"] // 3)):
            try:
                issued.append(E.push(a, oid, random.choice(ARCADES)))
            except RuntimeError:
                break
    say(f"      {len(issued)} passes issued to Apple Wallet (no chain writes)")
    say(f"      QR payload is {len(issued[0]['qr'])} chars, HMAC-signed")

    say("\n05  REDEEM  (scan at the arcade)")
    redeemed = [p for p in random.sample(issued, int(len(issued) * 0.42))]
    ok = 0
    for p in redeemed:
        if E.redeem(p["qr"], random.choice(ARCADES))["ok"]:
            ok += 1
    say(f"      {ok} redeemed cleanly")

    say("\n06  ADVERSARIAL SCANS  (what the guard has to stop)")
    dup = E.redeem(redeemed[0]["qr"], ARCADES[0])
    say(f"      duplicate scan      -> {dup['reason']}")
    forged = redeemed[1]["qr"][:-4] + "AAAA"
    say(f"      tampered QR         -> {E.redeem(forged, ARCADES[0])['reason']}")
    unknown = issued[0]["qr"].split(".", 1)
    say(f"      unknown reader key  -> "
        f"{E.redeem('ARC-FAKE-99.' + unknown[1], ARCADES[0])['reason']}")

    say("\n07  OFFLINE VALIDATION  (Starlink down — does the lane keep moving?)")
    spare = [p for p in issued if p not in redeemed][:3]
    for p in spare:
        okk, body = __import__("mtc").validate_offline(p["qr"], E.s["keyring"], time.time())
        say(f"      {p['mtc_id']}  offline-valid={okk}  "
            f"(authentic + unexpired, NO network)")

    say("\n08  EXPIRY SWEEP  (a timestamp query — no chain, no fee)")
    say(f"      {E.expire_due()} passes expired this sweep")

    say("\n09  ANCHOR THE WEEK  (Merkle root -> chain, simulated)")
    a = E.anchor_week(fy, wk)
    say(f"      FY{a['fy']} WK{a['week']}  root {a['root'][:40]}...")

    say("\n10  VERIFY THE LEDGER  (re-walk the hash chain)")
    okc, broken, n = E.ledger.verify()
    say(f"      {n} events · chain intact: {okc}"
        f"{'' if okc else f' BROKEN AT SEQ {broken}'}")

    say(f"\n{'='*72}")
    for oid, o in E.s["offers"].items():
        say(f"  {oid:16s} issued {o['issued']:3d}  redeemed {o['redeemed']:3d}  "
            f"({100*o['redeemed']/max(o['issued'],1):4.1f}%)  "
            f"${o['redeemed']*o['value']:7.2f} settled")
    say(f"{'='*72}\n")
    return E


if __name__ == "__main__":
    import shutil
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    if "--fresh" in sys.argv and os.path.isdir(d):
        shutil.rmtree(d)
    run()
