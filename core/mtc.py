#!/usr/bin/env python3
"""MTC — Meme Token Credit. NOT a coin. An Apple Wallet pass with a QR code.

THE CORRECTION THAT MATTERS: MTC never touches the blockchain. The chain does
exactly one job in this system -- prove the holder has at least 1 $ACM -- and
that is a read. An MTC is a signed pass delivered to the iPhone's Wallet app:
graphics plus a QR code whose payload is an HMAC token.

Two different things were both called "wallet" and that is what makes this
confusing on first pass:
    SOL wallet    holds 1 $ACM. Eligibility. Read-only, never spent.
    Apple Wallet  holds the MTC pass. The offer. Scanned to redeem.

WHY THIS BEATS AN ON-CHAIN CREDIT
  * issuing a credit is a database write, not a transaction with a fee
  * expiring ten thousand credits is one timestamp query, not ten thousand burns
  * non-transferability is true by construction, not by a token extension
  * "extinguished exactly once" is the first valid scan winning a race in the
    ledger -- the patent's core claim, satisfied without a burn transaction
  * the user needs no SOL, no gas, and no understanding of any of it

EXPIRY is denominated in Walmart weeks and always lands Friday 23:59:59 Eastern.
A pass carries that as its native expiration so Apple greys it out on its own,
and the ledger enforces it independently so a modified pass gains nothing.
"""
from __future__ import annotations

import secrets

import auth
import walmart_cal as cal


def issue(offer: dict, wallet_addr: str, key: str, key_id: str) -> dict:
    """Mint one MTC pass record bound to one wallet and one offer.

    The instrument is unique per issuance -- one promise, one instrument, one
    extinguishment. Two customers never share a code, and one customer's code
    cannot be reused after it is spent.
    """
    mtc_id = "MTC-" + secrets.token_hex(6).upper()
    opens, closes = cal.window(offer["fy"], offer["start_week"], offer["weeks"])
    payload = {
        "mtc": mtc_id,
        "offer": offer["id"],
        "brand": offer["brand"],
        "item": offer["item"],
        "wallet": wallet_addr,
        "fy": offer["fy"],
        "wk_open": offer["start_week"],
        "wk_close": offer["start_week"] + offer["weeks"] - 1,
        "exp": int(closes.timestamp()),
    }
    # THE QR PAYLOAD. Signed so a reader validates it with no network at all.
    token = auth.sign(payload, key, key_id)
    return {"mtc_id": mtc_id, "offer_id": offer["id"], "wallet": wallet_addr,
            "qr": token, "opens": opens.isoformat(timespec="seconds"),
            "closes": closes.isoformat(timespec="seconds"),
            "state": "ISSUED"}


def validate_offline(qr: str, keyring: dict, now_ts: float) -> tuple:
    """What a scanner does with NO network. Returns (ok, payload_or_reason).

    This checks authenticity and expiry only. It cannot check whether the code
    was already spent -- that needs the server. The tradeoff is deliberate: a
    reader that can validate offline keeps the lane moving through a Starlink
    outage, accepting a small double-redemption window, instead of going dark.
    """
    ok, body = auth.verify(qr, keyring)
    if not ok:
        return False, body
    if now_ts > float(body.get("exp", 0)):
        return False, "expired"
    return True, body
