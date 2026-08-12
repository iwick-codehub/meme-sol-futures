#!/usr/bin/env python3
"""Corridor pricer — the ratified Pricing Engine (MARKET-SPEC).

For a mint + lot, computes the exact corridor from live markets via Jupiter:

  floor  = PoolExit% — what market-selling the lot RIGHT NOW actually nets,
           quoted by the Jupiter router (real route, real price impact).
  ceiling= 95% of spot value.
  strike = floor + k * (ceiling - floor), baseline k = 0.25.
  net    = strike * 90% (commission), minus the 1.5 SOL flat fee
           (waived for the house coin, $ACM).

Read-only: quotes only, never swaps. Usage:
  pricer.py <mint> <lot_in_whole_coins> [k]
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

LITE = "https://lite-api.jup.ag"
WSOL = "So11111111111111111111111111111111111111112"
ACM = "4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump"
K_BASE = 0.25
CEILING = 0.95
COMMISSION = 0.10
FLAT_FEE_SOL = 1.5


def get(url: str):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"Accept": "application/json",
                                  "User-Agent": "instar-pricer/1.0"}), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(2 ** (attempt + 1))  # free tier — pace, don't hammer


def token_meta(mint: str) -> dict:
    d = get(f"{LITE}/tokens/v2/search?query={mint}")
    for t in d:
        if t.get("id") == mint:
            return t
    raise SystemExit(f"mint not found: {mint}")


def sol_usd() -> float:
    d = get(f"{LITE}/price/v3?ids={WSOL}")
    return float(d[WSOL]["usdPrice"])


def pool_exit_sol(mint: str, lot_base: int) -> float:
    q = urllib.parse.urlencode({
        "inputMint": mint, "outputMint": WSOL, "amount": lot_base,
        "slippageBps": 10000, "swapMode": "ExactIn"})
    d = get(f"{LITE}/swap/v1/quote?{q}")
    return int(d["outAmount"]) / 1e9


def corridor(mint: str, lot_whole: float, k: float = K_BASE) -> dict:
    meta = token_meta(mint)
    dec = int(meta["decimals"])
    sol = sol_usd()
    spot_lot_usd = lot_whole * float(meta["usdPrice"])
    spot_lot_sol = spot_lot_usd / sol
    exit_mode = "jupiter-quote"
    try:
        exit_sol = pool_exit_sol(mint, int(lot_whole * 10 ** dec))
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        # Free-tier quota exhausted (hcp-arb shares it): constant-product
        # approximation from published pool liquidity. x*y=k sell of value v
        # against one-sided depth x: proceeds = v / (1 + v/x).
        x_usd = float(meta.get("liquidity") or 0) / 2
        exit_sol = (spot_lot_usd / (1 + spot_lot_usd / x_usd) / sol) if x_usd else 0.0
        exit_mode = "liquidity-approx"
    floor = exit_sol / spot_lot_sol if spot_lot_sol else 0.0
    strike_pct = min(CEILING, floor + k * (CEILING - floor))
    strike_sol = strike_pct * spot_lot_sol
    net_sol = strike_sol * (1 - COMMISSION) - (0 if mint == ACM else FLAT_FEE_SOL)
    return {
        "symbol": meta["symbol"], "lot": lot_whole, "exit_mode": exit_mode,
        "spot_lot_sol": round(spot_lot_sol, 3), "spot_lot_usd": round(spot_lot_usd, 2),
        "pool_exit_sol": round(exit_sol, 3), "floor_pct": round(floor * 100, 1),
        "k": k, "strike_pct": round(strike_pct * 100, 1),
        "strike_sol": round(strike_sol, 3),
        "net_to_seller_sol": round(max(net_sol, 0), 3),
        "net_to_seller_usd": round(max(net_sol, 0) * sol, 2),
        "discount_vs_spot_pct": round((1 - max(net_sol, 0) / spot_lot_sol) * 100, 1)
        if spot_lot_sol else None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mint, lot = sys.argv[1], float(sys.argv[2])
    k = float(sys.argv[3]) if len(sys.argv) > 3 else K_BASE
    print(json.dumps(corridor(mint, lot, k), indent=2))
