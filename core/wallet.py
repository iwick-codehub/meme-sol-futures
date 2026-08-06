#!/usr/bin/env python3
"""Wallet minting for the NOOB path — we hold the key, the user never sees one.

THE MECHANISM, and why it is simpler than people expect:
Solana does not mine keys. Bitcoin's proof-of-work orders TRANSACTIONS; it has
nothing to do with creating a key. A Solana private key is literally 32 random
bytes. The public address is DERIVED from it mathematically, offline, in
microseconds -- there is nothing to search for and no network call involved.

So the flow is:
  1. 32 bytes from the OS CSPRNG (SecRandomCopyBytes on macOS, via secrets).
  2. Derive the ed25519 public key -> that IS the wallet address.
  3. Confirm the address has never been used.
  4. Push 1 $ACM to it. That token is the eligibility credential, nothing more.

STEP 3 IS NOT ABOUT COLLISIONS. The odds of colliding with an existing wallet
are 1 in 2^256, which is not a real risk. It is about catching a broken RNG on
our side -- and a bug in our own randomness is nowhere near 1 in 2^256. One
cheap RPC call turns a silent catastrophic failure into a loud one.

CUSTODY: holding the key on the user's behalf is custody, with the regulatory
posture that implies. Flagged for counsel; the architecture is positioned for it
(MTC carries no cash value, $ACM is never spendable inside the system) but
"we can revoke it" and "the user owns it" are different claims and only one can
be true.

KEY STORAGE AT SCALE: this sim writes keys to a local file, which is fine for a
simulation and WRONG for production. N independent keys means N secrets to
protect and one breach exposes everyone. Production wants hierarchical
deterministic derivation -- one master seed in an HSM, each user's key derived
by index -- so there is one secret to guard and no database of private keys
exists to steal.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets

try:
    from solders.keypair import Keypair
    REAL_CRYPTO = True
except ImportError:
    REAL_CRYPTO = False

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out


def mint(sim: bool = True) -> dict:
    """Create a wallet. Returns address + secret; the caller stores the secret.

    `sim=True` marks the record so a simulated wallet can never be mistaken for
    one holding real value.
    """
    seed = secrets.token_bytes(32)              # OS CSPRNG
    if REAL_CRYPTO:
        kp = Keypair.from_seed(seed)
        addr = str(kp.pubkey())
    else:
        # Sim fallback when solders is absent. Produces a well-formed,
        # deterministic-from-seed address so the flow can be exercised; it is
        # NOT a real ed25519 public key and must never be funded.
        addr = _b58(hashlib.sha256(b"simkey" + seed).digest())
    return {"address": addr,
            "secret": base64.b64encode(seed).decode(),
            "sim": sim or not REAL_CRYPTO,
            "real_crypto": REAL_CRYPTO}


def is_fresh(address: str, rpc=None) -> bool:
    """Has this address ever been touched? Sim always answers yes.

    In production this is one getSignaturesForAddress call. Cheap, and the only
    thing standing between a broken RNG and issuing two users the same wallet.
    """
    if rpc is None:
        return True
    r = rpc({"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress",
             "params": [address, {"limit": 1}]})
    return not (r.get("result") or [])


if __name__ == "__main__":
    print(f"  real ed25519 available: {REAL_CRYPTO}\n")
    for i in range(3):
        w = mint()
        print(f"  {w['address']}  (sim={w['sim']}, secret held by us, "
              f"{len(base64.b64decode(w['secret']))} bytes)")
    print("\n  addresses are unique and derived offline -- no chain call to create")
