#!/usr/bin/env python3
"""The settlement engine — enrollment, issuance, redemption, anchoring.

Every state change goes through the ledger. There is no other write path, and
the ledger has no update or delete. That is what makes the record a byproduct of
settlement rather than a report assembled afterward.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime

import auth
import mtc as MTC
import wallet as W
import walmart_cal as cal
from ledger import Ledger

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "logs")


class Engine:
    def __init__(self, name="sim"):
        os.makedirs(DATA, exist_ok=True)
        self.ledger = Ledger(os.path.join(DATA, f"{name}_ledger.csv"))
        self.state_path = os.path.join(DATA, f"{name}_state.json")
        self.s = self._load()

    def _load(self):
        if os.path.exists(self.state_path):
            return json.load(open(self.state_path))
        return {"members": {}, "offers": {}, "passes": {}, "keyring": {},
                "anchors": [], "acm_pushed": 0}

    def _save(self):
        tmp = self.state_path + ".tmp"
        json.dump(self.s, open(tmp, "w"), indent=1)
        os.replace(tmp, self.state_path)     # atomic; a killed process cannot
                                             # leave a half-written state file

    # ---------------------------------------------------------------- readers
    def add_reader(self, reader_id: str) -> str:
        """Provision a scanner with its own signing key. Per-reader, so one
        compromised arcade does not invalidate every code in the field."""
        k = auth.new_key()
        self.s["keyring"][reader_id] = k
        self._save()
        self.ledger.append("READER_PROVISIONED", reader_id, {"alg": auth.ALG})
        return k

    # ------------------------------------------------------------- enrollment
    def enroll(self, user_ref: str) -> dict:
        """Noob path: mint a wallet we custody, push 1 $ACM, record it."""
        w = W.mint(sim=True)
        if not W.is_fresh(w["address"]):
            raise RuntimeError("address not fresh — RNG suspect, refusing")
        self.s["members"][w["address"]] = {
            "user_ref": user_ref, "secret": w["secret"], "acm": 1,
            "joined": datetime.now(cal.TZ).isoformat(timespec="seconds"),
            "sim": w["sim"]}
        self.s["acm_pushed"] += 1
        self._save()
        self.ledger.append("ENROLLED", w["address"],
                           {"user_ref": user_ref, "acm": 1, "sim": w["sim"]})
        return {"address": w["address"], "acm": 1}

    def eligible(self, addr: str) -> bool:
        """The ONLY thing the blockchain is asked. A read, never a spend."""
        return self.s["members"].get(addr, {}).get("acm", 0) >= 1

    # ----------------------------------------------------------------- offers
    def add_offer(self, oid, brand, item, fy, start_week, weeks, value, cap):
        """Offers are denominated in Walmart weeks: 1 minimum, 52 maximum."""
        opens, closes = cal.window(fy, start_week, weeks)   # validates the window
        o = {"id": oid, "brand": brand, "item": item, "fy": fy,
             "start_week": start_week, "weeks": weeks, "value": value,
             "cap": cap, "issued": 0, "redeemed": 0,
             "opens": opens.isoformat(timespec="seconds"),
             "closes": closes.isoformat(timespec="seconds")}
        self.s["offers"][oid] = o
        self._save()
        self.ledger.append("OFFER_FUNDED", oid,
                           {"brand": brand, "item": item, "fy": fy,
                            "wk": f"{start_week}+{weeks}", "value": value,
                            "cap": cap})
        return o

    # ------------------------------------------------------------- issuance
    def push(self, addr: str, offer_id: str, reader_id: str) -> dict:
        """Push one MTC to one member. Eligibility is checked at issuance."""
        o = self.s["offers"][offer_id]
        if not self.eligible(addr):
            raise PermissionError("holder does not have >=1 $ACM")
        if o["issued"] >= o["cap"]:
            raise RuntimeError("offer cap reached")
        p = MTC.issue(o, addr, self.s["keyring"][reader_id], reader_id)
        self.s["passes"][p["mtc_id"]] = p
        o["issued"] += 1
        self._save()
        self.ledger.append("MTC_ISSUED", p["mtc_id"],
                           {"offer": offer_id, "wallet": addr,
                            "closes": p["closes"]})
        return p

    # ------------------------------------------------------------ redemption
    def redeem(self, qr: str, reader_id: str, offline=False) -> dict:
        """Scan. THE settlement event.

        Offline validation proves the code is authentic and unexpired with no
        network. The exactly-once check needs this ledger, so an offline scan
        is queued and reconciled -- accepting a small double-redemption window
        rather than letting an outage stop the lane.
        """
        ok, body = MTC.validate_offline(qr, self.s["keyring"], time.time())
        if not ok:
            self.ledger.append("REDEEM_REJECTED", "-",
                               {"reason": body, "reader": reader_id})
            return {"ok": False, "reason": body}
        mid = body["mtc"]
        p = self.s["passes"].get(mid)
        if p is None:
            self.ledger.append("REDEEM_REJECTED", mid,
                               {"reason": "unknown instrument", "reader": reader_id})
            return {"ok": False, "reason": "unknown instrument"}
        if p["state"] == "REDEEMED":
            # THE EXACTLY-ONCE GUARANTEE. First valid scan wins; every later
            # scan of the same instrument fails here, forever.
            self.ledger.append("REDEEM_REJECTED", mid,
                               {"reason": "already redeemed", "reader": reader_id})
            return {"ok": False, "reason": "already redeemed"}
        p["state"] = "REDEEMED"
        p["redeemed_at"] = datetime.now(cal.TZ).isoformat(timespec="seconds")
        p["reader"] = reader_id
        self.s["offers"][p["offer_id"]]["redeemed"] += 1
        self._save()
        self.ledger.append("MTC_REDEEMED", mid,
                           {"offer": p["offer_id"], "wallet": p["wallet"],
                            "reader": reader_id, "offline": offline,
                            "item": body.get("item", "")})
        return {"ok": True, "mtc": mid, "offer": p["offer_id"]}

    def expire_due(self) -> int:
        """Sweep expired passes. Free -- a timestamp comparison, no chain, no fee.
        This is the whole argument for keeping MTC off-chain in one method."""
        now = time.time()
        n = 0
        for mid, p in self.s["passes"].items():
            if p["state"] != "ISSUED":
                continue
            if datetime.fromisoformat(p["closes"]).timestamp() < now:
                p["state"] = "EXPIRED"
                n += 1
                self.ledger.append("MTC_EXPIRED", mid, {"offer": p["offer_id"]})
        if n:
            self._save()
        return n

    # -------------------------------------------------------------- anchoring
    def anchor_week(self, fy: int, week: int) -> dict:
        """Publish a Merkle root for one Walmart week.

        Simulated here. In production this writes the root to Solana, so a brand
        can verify its own redemptions against a commitment nobody -- including
        us -- can revise. The repo holds the data; the chain holds the proof.
        """
        root = self.ledger.merkle_root(fy, week)
        a = {"fy": fy, "week": week, "root": root,
             "at": datetime.now(cal.TZ).isoformat(timespec="seconds"),
             "chain": "SIMULATED"}
        self.s["anchors"].append(a)
        self._save()
        self.ledger.append("WEEK_ANCHORED", f"FY{fy}W{week}", {"root": root})
        return a
