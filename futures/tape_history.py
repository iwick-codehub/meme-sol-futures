#!/usr/bin/env python3
"""Daily tape snapshot — builds the rolling 7D / 2W history for the Terminal.

Run once a day (cron). It:
1. fetches the top-traded list (+ ACM) from Jupiter,
2. appends today's prices to futures/logs/tape_history.json,
3. bakes reference prices (7 and 14 days back) into body_terminal.html
   between the HIST markers — the page then shows LIVE 7D/2W change
   (live price vs the baked reference), fresh every 30s between snapshots,
4. republishes the Terminal page.

Columns read "—" until the history is deep enough (7/14 days from first run,
2026-08-11).
"""
import datetime
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
LOGS = HERE / "logs"
HIST_FILE = LOGS / "tape_history.json"
BODY = HERE / "shopify" / "body_terminal.html"
LITE = "https://lite-api.jup.ag"
ACM = "4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump"
KEEP_DAYS = 20


def get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "instar-tape/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_prices() -> dict:
    tokens = get(f"{LITE}/tokens/v2/toptraded/24h?limit=100")
    if not any(t["id"] == ACM for t in tokens):
        tokens += [t for t in get(f"{LITE}/tokens/v2/search?query={ACM}")
                   if t.get("id") == ACM]
    return {t["id"]: float(t["usdPrice"]) for t in tokens if t.get("usdPrice")}


def ref_price(days: dict, back: int, today: datetime.date):
    """Price closest to `back` days ago (accept back..back+3 days old)."""
    for age in range(back, back + 4):
        key = (today - datetime.timedelta(days=age)).isoformat()
        if key in days:
            return days[key]
    return None


def main() -> int:
    LOGS.mkdir(exist_ok=True)
    today = datetime.date.today()
    hist = json.loads(HIST_FILE.read_text()) if HIST_FILE.exists() else {}

    for mint, px in fetch_prices().items():
        days = hist.setdefault(mint, {})
        days[today.isoformat()] = px
        for k in [k for k in days
                  if (today - datetime.date.fromisoformat(k)).days > KEEP_DAYS]:
            del days[k]
    HIST_FILE.write_text(json.dumps(hist, indent=0))

    refs = {}
    for mint, days in hist.items():
        d7, d14 = ref_price(days, 7, today), ref_price(days, 14, today)
        if d7 or d14:
            refs[mint] = {"d7": d7, "d14": d14}

    body = BODY.read_text()
    new = re.sub(r"/\*HIST_START\*/.*?/\*HIST_END\*/",
                 "/*HIST_START*/var HIST=" + json.dumps(refs, separators=(",", ":"))
                 + ";/*HIST_END*/", body, flags=re.S)
    if new == body and "/*HIST_START*/" not in body:
        print("ERROR: HIST markers missing from body_terminal.html", file=sys.stderr)
        return 1
    BODY.write_text(new)

    subprocess.run([sys.executable, str(HERE / "shopify" / "publish.py")], check=True)
    print(f"{today}: snapshot {len(hist)} mints, refs for {len(refs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
