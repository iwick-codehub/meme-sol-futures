#!/usr/bin/env python3
"""Auto-post the Top 10 Peerage board to X at each checkpoint.

  tweet_top10.py [--dry] [--always]

Renders a Top-10-only PNG of the live leaderboard (headless Chrome), writes a
caption from the current checkpoint's movement, and posts image + caption to
@AladdinsCastleM via X API v2 (OAuth 1.0a user context). Credentials in
.x.env (gitignored). POLICY (Todd, 2026-08-18): a 12-hour PLAY-BY-PLAY posts at EVERY noon/midnight
checkpoint — Peerage changes lead, then accumulation, then who cracked / left
the Top 100. Runs at :03 after each checkpoint.
"""
import base64, datetime, json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PAGE = REPO / "futures" / "shopify" / "body_golden_ticket.html"
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LINK = "https://instarbrands.com/pages/golden-ticket"
FREEZE = datetime.datetime(2026, 9, 7, 16, 0, tzinfo=datetime.timezone.utc)
DRY = "--dry" in sys.argv
ALWAYS = "--always" in sys.argv


def env():
    e = {}
    for line in (REPO / ".x.env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    for k in ("X_OAUTH2_CLIENT_ID", "X_OAUTH2_CLIENT_SECRET", "X_OAUTH2_ACCESS_TOKEN", "X_OAUTH2_REFRESH_TOKEN"):
        if not e.get(k) or e[k].startswith("paste_here"):
            raise SystemExit(f"{k} not set in .x.env")
    return e


def payload():
    """Board payload, but with MOVEMENT taken from the latest checkpoint's own
    record (diffed vs the checkpoint before it) — not re-diffed live, which
    would compare the board to the baseline that was saved 3 minutes ago."""
    s = PAGE.read_text()
    gt = json.loads(re.search(r"/\*GT_START\*/var GT=(.*?);/\*GT_END\*/", s, flags=re.S).group(1))
    hist = json.loads((HERE / "history.json").read_text())["checkpoints"]
    if len(hist) >= 2:
        latest, prev = hist[-1], hist[-2]
        prev_peer = [r["wallet"] for r in prev["rows"][:10]]
        peer = ["Grand Vizier","Vizier","Necromancer","Wizard","Prime Magi","Magi","Conjurer","Evoker","Apprentice","Acolyte"]
        moves = []
        for i, r in enumerate(latest["rows"][:10]):
            if i >= len(prev_peer) or prev_peer[i] != r["wallet"]:
                moves.append({"title": peer[i], "rank": i + 1, "wallet": r["wallet"],
                              "kind": "NEW" if r["wallet"] not in prev_peer else "MOVED"})
        gt["moves"] = moves
        gt["checkpoint_label"] = latest["label"]
        gt["checkpoint"] = prev["taken_utc"]
        gt["top"] = [{"rank": r["rank"], "wallet": r["wallet"], "balance": r["balance"],
                      "was": r["prev_rank"], "delta": r["move"]} for r in latest["rows"]]
    return gt


def render_png(gt):
    """Top-10-only shot: hide scene + info, keep header/countdown/banner, trim rows to 10.
    IMPORTANT: bakes THIS payload (gt) into the HTML so arrows/banner reflect the
    checkpoint being announced, not whatever the live page last showed."""
    s = PAGE.read_text()
    blob = "/*GT_START*/var GT=" + json.dumps(gt, separators=(",", ":"), ensure_ascii=True) + ";/*GT_END*/"
    s = re.sub(r"/\*GT_START\*/.*?/\*GT_END\*/", lambda _m: blob, s, flags=re.S)
    s = s.replace('<div class="gt-scene">', '<div class="gt-scene" style="display:none">')
    s = s.replace('<div class="gt-info">', '<div class="gt-info" style="display:none">')
    s = s.replace('<details class="gt-excl">', '<details class="gt-excl" style="display:none">')
    s = s.replace('if (!GT.frozen) setTimeout(function () { location.reload(); }, 60000);', '')
    s = s.replace('GT.top.map(function (r) {', 'GT.top.slice(0,10).map(function (r) {')
    s = s.replace('<div class="gt-foot px">', '<div class="gt-foot px" style="display:none">')
    html = ("<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;background:#07050b}"
            ".gt{width:1100px !important;left:0 !important;transform:none !important;margin:0 auto}</style></head><body>"
            + s + "</body></html>")
    src = OUT / "top10_shot.html"; src.write_text(html)
    png = OUT / f"top10_{datetime.datetime.utcnow():%Y%m%d_%H%M}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1200,1090", f"--screenshot={png}", f"file://{src}"],
                   check=True, capture_output=True, timeout=90)
    return png


def caption(gt):
    """12-hour play-by-play, house style: no emoji, clean bullets, full sentences.
    Premium account -> long-form allowed; we still keep it tight and scannable."""
    hist = json.loads((HERE / "history.json").read_text())["checkpoints"]
    cur, prev = hist[-1], (hist[-2] if len(hist) > 1 else None)
    peer = ["Grand Vizier","Vizier","Necromancer","Wizard","Prime Magi","Magi","Conjurer","Evoker","Apprentice","Acolyte"]
    now = datetime.datetime.now(datetime.timezone.utc)
    days = max(0, (FREEZE - now).days)
    et = now.astimezone(datetime.timezone(datetime.timedelta(hours=-4)))
    when = "Noon" if 11 <= et.hour <= 13 else "Midnight" if et.hour in (23, 0, 1) else et.strftime("%-I %p")
    mentioned = []
    def sh(w):
        if w not in mentioned: mentioned.append(w)
        return f"{w[:6]}…{w[-4:]}"
    fm = lambda n: f"{n/1e6:.2f}M" if abs(n) >= 1e6 else f"{n/1e3:.0f}K" if abs(n) >= 1e3 else f"{n:.0f}"
    B = "• "
    out = [f"$ACM Top 100 Golden Ticket — {when} ET update", ""]
    if not prev:
        out.append(f"{B}Grand Vizier: {sh(cur['rows'][0]['wallet'])} with {fm(cur['rows'][0]['balance'])}")
    else:
        A = {r["wallet"]: r for r in prev["rows"]}; Bm = {r["wallet"]: r for r in cur["rows"]}
        pp = [r["wallet"] for r in prev["rows"][:10]]
        peer_lines = []
        for i, r in enumerate(cur["rows"][:10]):
            if i >= len(pp) or pp[i] != r["wallet"]:
                was = A.get(r["wallet"], {}).get("rank")
                tag = "enters the Peerage as" if r["wallet"] not in pp else f"moves from #{was} to"
                peer_lines.append(f"{B}{sh(r['wallet'])} {tag} {peer[i]} (#{i+1}) with {fm(r['balance'])}")
        if peer_lines:
            out.append("PEERAGE CHANGES"); out += peer_lines; out.append("")
        else:
            out.append("PEERAGE: all ten seats held, same order.")
            out.append("")
        # accumulation among the top 10 (all moves >= 50K, biggest first)
        acc = sorted(((r["balance"] - A[r["wallet"]]["balance"], r) for r in cur["rows"][:10] if r["wallet"] in A and abs(r["balance"] - A[r["wallet"]]["balance"]) >= 50_000), key=lambda x: -abs(x[0]))
        if acc:
            out.append("TOP 10 ACTIVITY")
            for d, r in acc[:4]:
                verb = "added" if d > 0 else "trimmed"
                out.append(f"{B}{peer[r['rank']-1]} {sh(r['wallet'])} {verb} {fm(abs(d))}, now {fm(r['balance'])}")
            out.append("")
        # movers outside the top 10
        climbs = sorted(((A[r["wallet"]]["rank"] - r["rank"], r) for r in cur["rows"][10:] if r["wallet"] in A and A[r["wallet"]]["rank"] - r["rank"] >= 3), key=lambda x: -x[0])
        newc = [r for r in cur["rows"] if r["wallet"] not in A]
        gone = [r for r in prev["rows"] if r["wallet"] not in Bm]
        if climbs or newc or gone:
            out.append("THE BOARD")
            for up, r in climbs[:3]:
                out.append(f"{B}{sh(r['wallet'])} climbs {up} places to #{r['rank']} ({fm(r['balance'])})")
            for r in newc[:4]:
                out.append(f"{B}New to the Top 100: {sh(r['wallet'])} at #{r['rank']} ({fm(r['balance'])})")
            if len(newc) > 4: out.append(f"{B}…and {len(newc)-4} more new entries")
            for r in sorted(gone, key=lambda r: -r["balance"])[:3]:
                out.append(f"{B}Left the Top 100: {sh(r['wallet'])}, was #{r['rank']} ({fm(r['balance'])})")
            out.append("")
        if len(out) <= 4 and not peer_lines and not acc:
            out.append("A quiet twelve hours. No changes to the Peerage or the Top 100."); out.append("")
    tot = sum(r["balance"] for r in cur["rows"])
    out.append(f"Top 100 holds {fm(tot)} ACM across {cur['holders']} total holders. {days} days to the freeze — noon ET, Labor Day, September 7.")
    out.append("")
    out.append("The Peerage of the Castle: titles held for all time.")
    out.append(LINK)
    if mentioned:
        out.append("")
        out.append("Wallets named above:")
        for w in mentioned[:8]:
            out.append(f"{w[:6]}…{w[-4:]}  solscan.io/account/{w}")
    return "\n".join(out)


# ---- OAuth 2.0 user context (auto-refresh; tokens live in .x.env) ----
ENV_PATH = REPO / ".x.env"

def _write_env(k, v):
    lines = ENV_PATH.read_text().splitlines()
    out, seen = [], False
    for ln in lines:
        if ln.startswith(k + "="):
            out.append(f"{k}={v}"); seen = True
        else:
            out.append(ln)
    if not seen: out.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(out) + "\n")

def refresh(e):
    """Exchange the refresh token for a new access token (X rotates both)."""
    data = urllib.parse.urlencode({"grant_type": "refresh_token",
                                   "refresh_token": e["X_OAUTH2_REFRESH_TOKEN"],
                                   "client_id": e["X_OAUTH2_CLIENT_ID"]}).encode()
    basic = base64.b64encode(f"{e['X_OAUTH2_CLIENT_ID']}:{e['X_OAUTH2_CLIENT_SECRET']}".encode()).decode()
    req = urllib.request.Request("https://api.twitter.com/2/oauth2/token", data,
                                 {"Content-Type": "application/x-www-form-urlencoded",
                                  "Authorization": f"Basic {basic}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.load(r)
    e["X_OAUTH2_ACCESS_TOKEN"] = tok["access_token"]
    _write_env("X_OAUTH2_ACCESS_TOKEN", tok["access_token"])
    if tok.get("refresh_token"):
        e["X_OAUTH2_REFRESH_TOKEN"] = tok["refresh_token"]
        _write_env("X_OAUTH2_REFRESH_TOKEN", tok["refresh_token"])
    return e

def _auth_call(e, url, data, headers, retry=True):
    h = dict(headers); h["Authorization"] = f"Bearer {e['X_OAUTH2_ACCESS_TOKEN']}"
    req = urllib.request.Request(url, data, h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as ex:
        if ex.code == 401 and retry:
            refresh(e)
            return _auth_call(e, url, data, headers, retry=False)
        raise SystemExit(f"X API {ex.code}: {ex.read().decode()[:400]}")

def upload_media(e, png):
    """v2 media upload (simple, base64) — chunked not needed for a ~300KB PNG."""
    body = json.dumps({"media": base64.b64encode(png.read_bytes()).decode(),
                       "media_category": "tweet_image"}).encode()
    res = _auth_call(e, "https://api.x.com/2/media/upload", body, {"Content-Type": "application/json"})
    return (res.get("data") or res).get("id") or (res.get("data") or res).get("media_id_string")

def post(e, text, media_id):
    body = json.dumps({"text": text, "media": {"media_ids": [str(media_id)]}}).encode()
    return _auth_call(e, "https://api.x.com/2/tweets", body, {"Content-Type": "application/json"})


def main():
    gt = payload()
    if "--catchup" in sys.argv:
        hist = json.loads((HERE / "history.json").read_text())["checkpoints"]
        peer = ["Grand Vizier","Vizier","Necromancer","Wizard","Prime Magi","Magi","Conjurer","Evoker","Apprentice","Acolyte"]
        for i in range(len(hist) - 1, 0, -1):
            prev_peer = [r["wallet"] for r in hist[i-1]["rows"][:10]]
            mv = [{"title": peer[j], "rank": j+1, "wallet": r["wallet"], "kind": "NEW" if r["wallet"] not in prev_peer else "MOVED"}
                  for j, r in enumerate(hist[i]["rows"][:10]) if j >= len(prev_peer) or prev_peer[j] != r["wallet"]]
            if mv:
                gt["moves"] = mv; gt["checkpoint"] = hist[i-1]["taken_utc"]
                gt["top"] = [{"rank": r["rank"], "wallet": r["wallet"], "balance": r["balance"],
                              "was": r["prev_rank"], "delta": r["move"]} for r in hist[i]["rows"]]
                break
    # POLICY (Todd, 2026-08-18): 12-hour play-by-play posts at EVERY checkpoint —
    # amounts always move; Peerage changes + Top-100 entries/exits are highlighted.
    png = render_png(gt)
    text = caption(gt)
    log = OUT / "tweets.log"
    if DRY:
        print(f"[DRY] would post {png.name}:\n{text}"); return
    e = env()
    mid = upload_media(e, png)
    res = post(e, text, mid)
    with log.open("a") as f:
        f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(), "png": png.name, "res": res}) + "\n")
    print("posted:", res.get("data", {}).get("id"))


if __name__ == "__main__":
    main()
