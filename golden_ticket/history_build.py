#!/usr/bin/env python3
"""Render golden_ticket/history.json -> the public Movement Log page
(futures/shopify/body_golden_log.html) and publish. Called after each
checkpoint. Newest checkpoint first; each shows its Peerage + full 100 rows
with PRV movement vs the checkpoint before it."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
REPO = HERE.parent
hist = json.loads((HERE / "history.json").read_text())["checkpoints"]

def short(w): return w[:6] + "…" + w[-4:]
def mv(r):
    if r["prev_rank"] is None: return "<span class='new'>NEW</span>"
    if r["move"] > 0: return f"<span class='up'>▲{r['move']}</span>"
    if r["move"] < 0: return f"<span class='dn'>▼{-r['move']}</span>"
    return "<span class='flat'>–</span>"

blocks = ""
for cp in reversed(hist):
    changes = [r for r in cp["rows"] if r["prev_rank"] is None or r["move"]]
    peer = "".join(f"<li><b>{r['title']}</b> — {short(r['wallet'])} {mv(r)}</li>" for r in cp["rows"][:10])
    body = "".join(
        f"<tr><td class='rk'>{r['rank']}</td><td class='mvc'>{mv(r)}</td>"
        f"<td class='ti'>{r['title'] or ''}</td>"
        f"<td class='w'><a href='https://solscan.io/account/{r['wallet']}' target='_blank' rel='noopener'>{short(r['wallet'])}</a></td>"
        f"<td class='b'>{(r['balance'] or 0):,.0f}</td></tr>" for r in cp["rows"])
    blocks += f"""
  <details {'open' if cp is hist[-1] else ''}>
    <summary><span class="px">{cp['label'].upper()}</span> &middot; {cp['taken_utc'][:16].replace('T',' ')} UTC &middot; slot {cp['slot']} &middot; {len(changes)} moved</summary>
    <div class="peer"><div class="px lbl">PEERAGE AT THIS CHECKPOINT</div><ul>{peer}</ul></div>
    <table><thead><tr><th>#</th><th>PRV</th><th>TITLE</th><th>WALLET</th><th>$ACM</th></tr></thead><tbody>{body}</tbody></table>
  </details>"""

html = f"""<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
  h1.main-page-title {{ display:none; }} main, #MainContent, body {{ background:#07050b; }}
  .gl {{ color:#e4d9e8; font-family:"Menlo","SF Mono",monospace; width:min(960px,94vw); margin:0 auto; padding:30px 0 60px; line-height:1.6; }}
  .gl .px {{ font-family:"Press Start 2P",monospace; }}
  .gl h2 {{ color:#ffd84a; font-size:clamp(.9rem,2vw,1.4rem); text-align:center; margin:.4em 0; }}
  .gl .sub {{ text-align:center; color:#d5cde0; font-size:.9em; max-width:48em; margin:0 auto 20px; }}
  .gl details {{ border:1px solid #8a520f; margin:14px 0; background:#100811; }}
  .gl summary {{ cursor:pointer; padding:12px 16px; color:#ffd84a; font-size:.85em; }}
  .gl summary .px {{ font-size:.6rem; letter-spacing:.15em; }}
  .gl .peer {{ padding:6px 16px 0; }} .gl .peer .lbl {{ color:#8a520f; font-size:.5rem; letter-spacing:.2em; margin-bottom:6px; }}
  .gl .peer ul {{ columns:2; margin:0 0 10px; padding-left:1.2em; font-size:.85em; }} .gl .peer li {{ margin:2px 0; }}
  .gl table {{ width:100%; border-collapse:collapse; font-size:.8em; }}
  .gl th {{ color:#ffd84a; font-size:.45rem; letter-spacing:.15em; padding:8px 10px; border-bottom:1px solid #8a520f; text-align:center; font-family:"Press Start 2P",monospace; }}
  .gl td {{ padding:6px 10px; border-bottom:1px solid #1a1020; text-align:center; white-space:nowrap; }}
  .gl td.rk {{ color:#ffd84a; font-weight:700; }} .gl td.ti {{ color:#ffd84a; font-size:.85em; }} .gl td.w a {{ color:#e4d9e8; text-decoration:none; }}
  .gl .up {{ color:#4ade80; }} .gl .dn {{ color:#f87171; }} .gl .new {{ color:#ffd84a; font-weight:700; }} .gl .flat {{ color:#3a2a44; }}
  .gl a.back {{ color:#ffd84a; }}
</style>
<div class="gl">
  <h2 class="px">GOLDEN TICKET — MOVEMENT LOG</h2>
  <p class="sub">Every checkpoint on the road to the freeze: the 5 PM ET start on Aug 12,
  then midnight and noon ET daily through Labor Day. Each entry records all 100
  positions and their movement (PRV) versus the checkpoint before it.
  <a class="back" href="/pages/golden-ticket">&larr; Live leaderboard</a></p>
  {blocks}
</div>"""
(REPO / "futures/shopify/body_golden_log.html").write_text(html)
print(f"movement log: {len(hist)} checkpoints rendered")
subprocess.run([sys.executable, str(REPO / "futures/shopify/publish.py")], check=True)
