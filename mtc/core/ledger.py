#!/usr/bin/env python3
"""The settlement ledger — append-only, hash-chained, anchorable.

This is the product. KRW-C-2026-002: "The measurement is not a product built
alongside the system. It is what the system leaves behind."

WHY HASH-CHAINED
Each row carries the hash of the row before it, so altering any historical row
changes every hash after it and the break is detectable by anyone holding a
later hash. Git gives the same property for the file, but git history can be
force-pushed and rewritten by anyone with write access, and nothing inside the
repo would prove it happened.

WHY ANCHORED
So we periodically publish a MERKLE ROOT of the ledger to a public chain. The
data lives in the repository; the PROOF that the data has not moved lives
somewhere nobody controls, including us. A brand can then verify its own
redemptions against an anchor we cannot revise. That is the difference between
tamper-evident and tamper-evident-to-someone-who-already-trusts-you.

The anchor is also the honest version of "the record is a byproduct of
settlement" -- it is produced by the act of settling, not assembled afterward
by a reporting process that could be told what to say.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime

from walmart_cal import TZ, current

GENESIS = "0" * 64
FIELDS = ["seq", "utc", "fy", "week", "event", "subject", "detail",
          "prev_hash", "row_hash"]


def _hash_row(seq, utc, fy, week, event, subject, detail, prev_hash) -> str:
    """Hash over every field including the previous hash. Order is part of the
    contract -- change it and every historical hash becomes unverifiable."""
    blob = json.dumps([seq, utc, fy, week, event, subject, detail, prev_hash],
                      separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


class Ledger:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(FIELDS)

    def rows(self):
        with open(self.path) as f:
            return list(csv.DictReader(f))

    def tip(self):
        r = self.rows()
        return (int(r[-1]["seq"]), r[-1]["row_hash"]) if r else (0, GENESIS)

    def append(self, event: str, subject: str, detail: dict) -> dict:
        """Add one event. The only write path -- there is no update or delete."""
        seq, prev = self.tip()
        seq += 1
        now = datetime.now(TZ)
        fy, week = current(now)
        utc = now.isoformat(timespec="seconds")
        det = json.dumps(detail, separators=(",", ":"), sort_keys=True)
        rh = _hash_row(seq, utc, fy, week, event, subject, det, prev)
        row = dict(zip(FIELDS, [seq, utc, fy, week, event, subject, det, prev, rh]))
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([row[k] for k in FIELDS])
        return row

    def verify(self):
        """Re-walk the chain. Returns (ok, first_broken_seq_or_None, count)."""
        prev = GENESIS
        rows = self.rows()
        for r in rows:
            want = _hash_row(int(r["seq"]), r["utc"], int(r["fy"]), int(r["week"]),
                             r["event"], r["subject"], r["detail"], prev)
            if want != r["row_hash"] or r["prev_hash"] != prev:
                return False, int(r["seq"]), len(rows)
            prev = r["row_hash"]
        return True, None, len(rows)

    def merkle_root(self, fy=None, week=None) -> str:
        """Root over row hashes, optionally scoped to one Walmart week.

        Scoping to a week is the point: the anchor published at the close of a
        week commits exactly that week's settlement facts, which is the period
        a brand's trade report is denominated in.
        """
        hs = [bytes.fromhex(r["row_hash"]) for r in self.rows()
              if (fy is None or int(r["fy"]) == fy)
              and (week is None or int(r["week"]) == week)]
        if not hs:
            return GENESIS
        while len(hs) > 1:
            if len(hs) % 2:
                hs.append(hs[-1])
            hs = [hashlib.sha256(hs[i] + hs[i + 1]).digest()
                  for i in range(0, len(hs), 2)]
        return hs[0].hex()


if __name__ == "__main__":
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "t.csv")
    L = Ledger(p)
    for i in range(5):
        L.append("TEST", f"subj-{i}", {"i": i})
    print("  clean chain      :", L.verify())
    print("  week merkle root :", L.merkle_root(*current())[:32], "...")
    # tamper with row 3 and prove the chain catches it
    rows = L.rows()
    rows[2]["detail"] = '{"i":999}'
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(rows)
    print("  after tampering  :", L.verify(), " <- detected at that seq")
