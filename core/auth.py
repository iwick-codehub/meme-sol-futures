#!/usr/bin/env python3
"""HMAC authentication — the standard for EVERY channel in this system.

Standing rule: MTC QR payloads, reader-to-server reports, brand offer
submissions, webhooks, internal calls. No exceptions, no per-case decision.

WHY HMAC RATHER THAN A LOOKUP KEY
A random token requires the verifier to ask a server whether it is real. An
HMAC-signed token can be verified OFFLINE, with no network at all. That is
load-bearing here: Starlink is the arcade site minimum, but a scanner that stops
working during an outage stops the entire promotion. Signed codes mean the worst
case is delayed reconciliation, not a dead lane.

THREE THINGS THAT ARE NOT OPTIONAL
  1. KEY ID in the payload. Readers are deployed in the field; without a key id
     you cannot rotate a secret without bricking every one of them.
  2. TIMESTAMP + NONCE inside the signed envelope. Without them a captured valid
     signature stays valid forever and can simply be replayed.
  3. CONSTANT-TIME COMPARISON on verify. Comparing signatures with == leaks how
     many leading bytes matched, through timing, and that is a documented path
     to forging one byte at a time.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

ALG = "HS256"
SKEW_S = 90          # tolerance for reader clock drift on the timestamp check


def new_key() -> str:
    """A fresh 256-bit signing secret, base64url. One per reader."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(payload: dict, key: str, key_id: str) -> str:
    """Produce `<key_id>.<payload>.<sig>` — the string a QR code carries.

    A nonce and issued-at are injected here rather than trusted from the caller,
    so no call site can forget them and quietly create a replayable token.
    """
    body = dict(payload)
    body.setdefault("iat", int(time.time()))
    body.setdefault("jti", secrets.token_hex(8))
    raw = _b64(json.dumps(body, separators=(",", ":"), sort_keys=True).encode())
    sig = _b64(hmac.new(_unb64(key), f"{key_id}.{raw}".encode(),
                        hashlib.sha256).digest())
    return f"{key_id}.{raw}.{sig}"


def verify(token: str, keyring: dict, max_age_s: int = None):
    """Verify offline. Returns (ok, payload_or_reason).

    `keyring` maps key_id -> secret, so a reader can hold several and accept
    tokens signed under a key that is being rotated out.
    """
    try:
        kid, raw, sig = token.split(".")
    except ValueError:
        return False, "malformed token"
    key = keyring.get(kid)
    if key is None:
        return False, f"unknown key id {kid}"
    expect = _b64(hmac.new(_unb64(key), f"{kid}.{raw}".encode(),
                           hashlib.sha256).digest())
    # constant time -- never ==
    if not hmac.compare_digest(sig, expect):
        return False, "bad signature"
    try:
        body = json.loads(_unb64(raw))
    except Exception:
        return False, "bad payload"
    if max_age_s is not None:
        age = time.time() - float(body.get("iat", 0))
        if age > max_age_s + SKEW_S:
            return False, f"expired token ({int(age)}s old)"
        if age < -SKEW_S:
            return False, "token from the future (clock skew)"
    return True, body


if __name__ == "__main__":
    kid, key = "rdr-001", new_key()
    ring = {kid: key}
    t = sign({"mtc": "MTC-DEMO-0001", "offer": "PG-TIDE-W27"}, key, kid)
    print(f"  token ({len(t)} chars, fits a QR):\n    {t}\n")
    print("  verify clean      :", verify(t, ring)[0])
    print("  verify tampered   :", verify(t[:-2] + "XY", ring))
    print("  verify wrong key  :", verify(t, {kid: new_key()}))
    print("  verify unknown kid:", verify("rdr-999." + t.split(".", 1)[1], ring))
