#!/usr/bin/env python3
"""Auto-post the Top 10 Peerage board to X at each checkpoint.

  tweet_top10.py [--dry] [--always]

Renders a Top-10-only PNG of the live leaderboard (headless Chrome), writes a
caption from the current checkpoint's movement, and posts image + caption to
@AladdinsCastleM via X API v2 (OAuth 1.0a user context). Credentials in
.x.env (gitignored). POLICY (Todd, 2026-08-12): post ONLY when the Top 10
Peerage changed since the previous checkpoint — every post is news. Runs at
:03 after each noon/midnight ET checkpoint. --always exists for manual use.
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
    peer = ["Grand Vizier", "Vizier", "Necromancer", "Wizard", "Prime Magi",
            "Magi", "Conjurer", "Evoker", "Apprentice", "Acolyte"]
    now = datetime.datetime.now(datetime.timezone.utc)
    days = max(0, (FREEZE - now).days)
    et = now.astimezone(datetime.timezone(datetime.timedelta(hours=-4)))
    when = "Noon" if et.hour == 12 else "Midnight" if et.hour == 0 else et.strftime("%-I %p")
    lines = [f"⚔️ $ACM Top 100 Golden Ticket — {when} ET standings"]
    if gt.get("moves"):
        for m in gt["moves"][:3]:
            lines.append(f"{'🆕 ' if m['kind']=='NEW' else '🔁 '}{m['title'].upper()}: {m['wallet'][:5]}…{m['wallet'][-4:]}")
    else:
        top = gt["top"][0]
        lines.append(f"👑 Grand Vizier holds: {top['wallet'][:5]}…{top['wallet'][-4:]}")
    lines.append(f"⏳ {days} days to the freeze — noon ET, Labor Day, Sept 7")
    lines.append(f"Peerage of the Castle: titles for all time.\n{LINK}")
    return "\n".join(lines)


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
    if not ALWAYS and not gt.get("moves"):
        print("no Peerage movement since last checkpoint — skipping (use --always to force)"); return
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
