#!/usr/bin/env python3
"""NEW-COIN RADAR — hidden research database. NEVER published to the site.

Rule (Todd, 2026-08-11): the moment a coin newer than 24h hits our radar
(the top-traded tape), the desk PAPER-buys the standard 1M-coin forward at
the live corridor bid. No funds ever move — this is a simulated long book
to find the patterns: does the early holder who locks in gains win, or the
buyer who paid the discount? Every position self-settles at +14 days
against the then-live price.

Run daily (cron). Appends to newcoins.json:
  - full token snapshot at detection (price, mcap, fdv, liq, holders,
    organic score, audit, tags, launch pool, all stats windows)
  - the paper contract (corridor strike/bid on the 1M lot, expiry +14d)
  - on later runs: settles expired positions and records the outcome
"""
import datetime
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "newcoins.json"
LITE = "https://lite-api.jup.ag"
NEW_HOURS = 24
TERM_DAYS = 14
CEILING, K = 0.95, 0.25


def get(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json", "User-Agent": "instar-radar/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(2 ** (attempt + 1))


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def corridor_bid(price, liq):
    """Paper quote on the 1M lot from the x*y=k liquidity approximation."""
    v = 1e6 * price
    x = (liq or 0) / 2
    if not x or not v:
        return None
    floor = (v / (1 + v / x)) / v
    strike = min(CEILING, floor + K * (CEILING - floor))
    return {"pool_exit_pct": round(floor * 100, 2),
            "strike_pct": round(strike * 100, 2),
            "ask_usd": round(strike * v, 2),          # buyer pays (paper)
            "bid_usd": round(strike * v * 0.90, 2)}   # seller nets (paper)


HERO_ALLOC = 2_000        # $ per hero position (paper)
HERO_DAILY_CAP = 10_000   # max $ of new hero exposure per day
HERO_STRIKE_MULT = 2.0    # the ACM model: strike = 2x detection valuation


def hero_worthy(t):
    """Claude's hero bar, codified: real launch-day traction only."""
    e = t
    audit = e.get("audit") or {}
    return ((e.get("holderCount") or 0) >= 800 and
            (e.get("liquidity") or 0) >= 40_000 and
            (e.get("mcap") or 0) >= 250_000 and
            (audit.get("topHoldersPercentage") or 100) <= 40 and
            (e.get("organicScoreLabel") or "low") in ("medium", "high"))


def open_heroes(db, new_positions):
    today = now_utc().date().isoformat()
    db.setdefault("hero_positions", [])
    spent = sum(h["allocation_usd"] for h in db["hero_positions"]
                if h["detected"][:10] == today)
    have = {h["mint"] for h in db["hero_positions"]}
    candidates = [p for p in db["positions"]
                  if p["detected"][:10] == today and p["mint"] not in have]
    # richest launches first — conviction ranking by traction
    candidates.sort(key=lambda p: (p["entry"].get("holderCount") or 0) *
                    ((p["entry"].get("liquidity") or 0) ** 0.5), reverse=True)
    opened = []
    for p in candidates:
        if spent + HERO_ALLOC > HERO_DAILY_CAP:
            break
        if not hero_worthy(p["entry"]):
            continue
        entry_px = p["entry"]["usdPrice"]
        strike_px = entry_px * HERO_STRIKE_MULT
        h = {
            "mint": p["mint"], "symbol": p["symbol"],
            "detected": p["detected"], "expiry": p["expiry"],
            "model": "2x-strike (ACM/Contract-One shape)",
            "entry_usdPrice": entry_px, "strike_usdPrice": strike_px,
            "entry_mcap": p["entry"]["mcap"],
            "strike_mcap": (p["entry"]["mcap"] or 0) * HERO_STRIKE_MULT,
            "allocation_usd": HERO_ALLOC,
            "coins": round(HERO_ALLOC / strike_px) if strike_px else 0,
            "status": "OPEN", "settlement": None,
        }
        db["hero_positions"].append(h)
        opened.append(h)
        spent += HERO_ALLOC
    return opened


def settle_heroes(db):
    ts = now_utc()
    settled = []
    for h in db.get("hero_positions", []):
        if h["status"] != "OPEN" or datetime.datetime.fromisoformat(h["expiry"]) > ts:
            continue
        try:
            found = get(f"{LITE}/tokens/v2/search?query={h['mint']}")
            t = next((x for x in found if x.get("id") == h["mint"]), None)
        except Exception:
            t = None
        px = (t or {}).get("usdPrice") or 0.0
        value = px * h["coins"]
        h["settlement"] = {
            "settled": ts.isoformat(timespec="seconds"), "usdPrice": px,
            "vs_strike": round(px / h["strike_usdPrice"], 3) if h["strike_usdPrice"] else None,
            "value_usd": round(value, 2),
            "pnl_usd": round(value - h["allocation_usd"], 2),
            "pnl_pct": round((value / h["allocation_usd"] - 1) * 100, 1),
            "delisted": t is None,
        }
        h["status"] = "SETTLED"
        settled.append(h)
        time.sleep(2)
    return settled


def detect(db):
    ts = now_utc()
    tokens = get(f"{LITE}/tokens/v2/toptraded/24h?limit=100")
    found = []
    for t in tokens:
        created = ((t.get("firstPool") or {}).get("createdAt"))
        if not created:
            continue
        age_h = (ts - datetime.datetime.fromisoformat(
            created.replace("Z", "+00:00"))).total_seconds() / 3600
        if age_h > NEW_HOURS or age_h < 0:
            continue
        if t.get("freezeAuthority") or t.get("mintAuthority"):
            continue  # untradeable — we wouldn't write the contract
        mint = t["id"]
        if any(p["mint"] == mint for p in db["positions"]):
            continue  # already on the book
        quote = corridor_bid(t.get("usdPrice") or 0, t.get("liquidity") or 0)
        if not quote:
            continue
        pos = {
            "mint": mint, "symbol": t.get("symbol"), "name": t.get("name"),
            "detected": ts.isoformat(timespec="seconds"),
            "pool_created": created, "age_hours_at_detect": round(age_h, 2),
            "expiry": (ts + datetime.timedelta(days=TERM_DAYS)).isoformat(timespec="seconds"),
            "lot": 1_000_000,
            "entry": {  # everything we can see at detection
                "usdPrice": t.get("usdPrice"), "mcap": t.get("mcap"),
                "fdv": t.get("fdv"), "liquidity": t.get("liquidity"),
                "holderCount": t.get("holderCount"),
                "organicScore": t.get("organicScore"),
                "organicScoreLabel": t.get("organicScoreLabel"),
                "tags": t.get("tags"), "audit": t.get("audit"),
                "dev": t.get("dev"), "decimals": t.get("decimals"),
                "stats5m": t.get("stats5m"), "stats1h": t.get("stats1h"),
                "stats6h": t.get("stats6h"), "stats24h": t.get("stats24h"),
            },
            "paper_contract": quote,   # we are the paper BUYER at ask_usd
            "status": "OPEN",
            "settlement": None,
        }
        db["positions"].append(pos)
        found.append(pos)
    return found


def settle(db):
    ts = now_utc()
    due = [p for p in db["positions"]
           if p["status"] == "OPEN" and datetime.datetime.fromisoformat(p["expiry"]) <= ts]
    settled = []
    for p in due:
        try:
            found = get(f"{LITE}/tokens/v2/search?query={p['mint']}")
            t = next((x for x in found if x.get("id") == p["mint"]), None)
        except Exception:
            t = None
        px = (t or {}).get("usdPrice") or 0.0
        lot_value = px * p["lot"]
        paid = p["paper_contract"]["ask_usd"]
        p["settlement"] = {
            "settled": ts.isoformat(timespec="seconds"),
            "usdPrice": px, "mcap": (t or {}).get("mcap"),
            "liquidity": (t or {}).get("liquidity"),
            "lot_value_usd": round(lot_value, 2),
            "buyer_pnl_usd": round(lot_value - paid, 2),
            "buyer_pnl_pct": round((lot_value / paid - 1) * 100, 1) if paid else None,
            "delisted": t is None,
        }
        p["status"] = "SETTLED"
        settled.append(p)
        time.sleep(2)  # free-tier pacing
    return settled


def main():
    db = json.loads(DB.read_text()) if DB.exists() else {"positions": []}
    found = detect(db)
    heroes = open_heroes(db, found)
    settled = settle(db)
    hero_settled = settle_heroes(db)
    DB.write_text(json.dumps(db, indent=1))
    open_n = sum(1 for p in db["positions"] if p["status"] == "OPEN")
    hero_open = sum(1 for h in db.get("hero_positions", []) if h["status"] == "OPEN")
    print(f"{now_utc().date()}: DRAGNET +{len(found)} new, {len(settled)} settled, "
          f"{open_n} open | HEROES +{len(heroes)} new, {len(hero_settled)} settled, "
          f"{hero_open} open")
    for h in heroes:
        print(f"  HERO {h['symbol']:12s} entry ${h['entry_usdPrice']:.6g} -> strike "
              f"${h['strike_usdPrice']:.6g} (2x)  ${h['allocation_usd']:,} for "
              f"{h['coins']:,} coins  wins if >2x by {h['expiry'][:10]}")
    for h in hero_settled:
        print(f"  HERO SETTLED {h['symbol']:12s} P/L {h['settlement']['pnl_pct']}%")
    for p in found:
        e = p["entry"]
        print(f"  NEW {p['symbol']:12s} age {p['age_hours_at_detect']:5.1f}h  "
              f"px ${e['usdPrice']:.6g}  mcap ${e['mcap']:,.0f}  "
              f"liq ${e['liquidity']:,.0f}  holders {e['holderCount']}  "
              f"paper ask ${p['paper_contract']['ask_usd']:,.2f}")
    for p in settled:
        s = p["settlement"]
        print(f"  SETTLED {p['symbol']:12s} buyer P/L {s['buyer_pnl_pct']}%")


if __name__ == "__main__":
    main()
