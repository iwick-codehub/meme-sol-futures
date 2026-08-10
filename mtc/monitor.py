#!/usr/bin/env python3
"""MTC Sim-2.0 monitor — port 8901. Read-only; it displays, it never writes.

Deliberately shows the Walmart week as the primary frame, because that is the
period every offer, every expiry and every anchor is denominated in. A brand
looking at this screen sees its own trade calendar.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "core"))
import walmart_cal as cal
from ledger import Ledger

PORT = 8901
LOGS = os.path.join(HERE, "logs")


def build():
    fy, wk = cal.current()
    st = {}
    p = os.path.join(LOGS, "sim_state.json")
    if os.path.exists(p):
        st = json.load(open(p))
    L = Ledger(os.path.join(LOGS, "sim_ledger.csv"))
    ok, broken, n = L.verify()
    rows = L.rows()[-40:][::-1]

    offers = []
    for o in st.get("offers", {}).values():
        cf, cw = cal.close_week(o["fy"], o["start_week"], o["weeks"])
        offers.append({**o, "close_fy": cf, "close_wk": cw,
                       "rate": round(100 * o["redeemed"] / max(o["issued"], 1), 1),
                       "settled": round(o["redeemed"] * o["value"], 2),
                       "live": o["start_week"] <= wk <= (cw if cf == fy else 99)})
    offers.sort(key=lambda x: -x["issued"])

    passes = st.get("passes", {})
    states = {}
    for x in passes.values():
        states[x["state"]] = states.get(x["state"], 0) + 1

    # a 12-week strip centred on now, so the operator sees what is closing
    strip = []
    for w in range(max(1, wk - 3), min(cal.fy_weeks(fy), wk + 8) + 1):
        s, e = cal.week_start(fy, w), cal.week_end(fy, w)
        strip.append({"wk": w, "now": w == wk,
                      "open": s.strftime("%d %b"), "close": e.strftime("%d %b"),
                      "closing": sum(1 for o in offers
                                     if o["close_fy"] == fy and o["close_wk"] == w)})
    return {
        "fy": fy, "week": wk, "label": cal.label(fy, wk),
        "fy_weeks": cal.fy_weeks(fy),
        "now": datetime.now(cal.TZ).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "week_opens": cal.week_start(fy, wk).strftime("%a %d %b %H:%M"),
        "week_closes": cal.week_end(fy, wk).strftime("%a %d %b %H:%M"),
        "strip": strip, "offers": offers,
        "members": len(st.get("members", {})),
        "acm_out": st.get("acm_pushed", 0),
        "passes": len(passes), "states": states,
        "readers": list(st.get("keyring", {})),
        "anchors": st.get("anchors", [])[-6:][::-1],
        "ledger_ok": ok, "ledger_broken": broken, "ledger_n": n,
        "events": rows,
    }


PAGE = r"""<meta name=viewport content="width=device-width,initial-scale=1">
<title>MTC SIM-2.0</title>
<style>
body{background:#0a0a0c;color:#d2d2d6;font:13px ui-monospace,Menlo,monospace;margin:0;padding:18px}
h1{font-size:15px;letter-spacing:2px;color:#c9a84c;margin:0 0 2px}
.sim{display:inline-block;background:#3a2f16;color:#c9a84c;font-size:10px;
     letter-spacing:1.5px;padding:2px 9px;margin-left:10px;vertical-align:2px}
.sub{color:#6b6b7a;font-size:11px;margin-bottom:16px}
.cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.c{border:1px solid #23232e;border-radius:6px;padding:9px 14px;background:#101018;min-width:118px}
.l{color:#6b6b7a;font-size:10px;letter-spacing:1px}
.v{font-size:19px;margin-top:3px;color:#e8e8ee}
.sect{color:#c9a84c;font-size:10px;letter-spacing:2px;margin:18px 0 7px;
      border-bottom:1px solid #23232e;padding-bottom:4px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:#6b6b7a;font-weight:400;font-size:10px;letter-spacing:1px;
   padding:5px 7px;border-bottom:1px solid #23232e}
td{padding:4px 7px;border-bottom:1px solid #16161d}
.g{color:#5fd08a}.r{color:#d08a8a}.d{color:#6b6b7a}.gold{color:#c9a84c}
.strip{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:6px}
.wk{border:1px solid #23232e;border-radius:5px;padding:6px 9px;min-width:74px;background:#101018}
.wk.now{border-color:#c9a84c;background:#1a1509}
.wk .n{font-size:14px;color:#e8e8ee}
.wk .dt{font-size:9px;color:#6b6b7a;margin-top:2px}
.wk .cl{font-size:9px;color:#d08a8a;margin-top:2px}
.mono{font-family:Menlo,monospace;font-size:10px}
</style>
<h1>MTC SIM-2.0<span class=sim>SIMULATION · NO CHAIN WRITES · NO REAL VALUE</span></h1>
<div class=sub id=sub>loading…</div>
<div class=cards id=cards></div>

<div class=sect>WALMART WEEK CALENDAR · offers and expiries are denominated here</div>
<div class=strip id=strip></div>
<div class=sub id=wkinfo></div>

<div class=sect>FUNDED OFFERS</div>
<table><thead><tr><th style="width:15%">OFFER</th><th style="width:20%">ITEM</th>
<th>WINDOW</th><th style="text-align:right">ISSUED</th><th style="text-align:right">REDEEMED</th>
<th style="text-align:right">RATE</th><th style="text-align:right">SETTLED</th></tr></thead>
<tbody id=offers></tbody></table>

<div class=sect>WEEK ANCHORS · merkle root committed per Walmart week</div>
<table><thead><tr><th style="width:14%">PERIOD</th><th style="width:16%">AT</th>
<th>ROOT</th><th style="width:12%">CHAIN</th></tr></thead><tbody id=anchors></tbody></table>

<div class=sect>SETTLEMENT LEDGER · append-only, hash-chained</div>
<table><thead><tr><th style="width:6%">SEQ</th><th style="width:13%">TIME</th>
<th style="width:9%">WEEK</th><th style="width:18%">EVENT</th>
<th style="width:22%">SUBJECT</th><th>DETAIL</th></tr></thead>
<tbody id=events></tbody></table>

<script>
async function tick(){
  const d = await (await fetch('/data.json')).json();
  document.getElementById('sub').textContent =
    `${d.label}  ·  ${d.now}  ·  fiscal year has ${d.fy_weeks} weeks`;
  document.getElementById('wkinfo').textContent =
    `week opens ${d.week_opens} · closes ${d.week_closes} — every offer expiry lands on that boundary`;
  document.getElementById('cards').innerHTML = [
    ['MEMBERS', d.members], ['$ACM OUT OF FLOAT', d.acm_out],
    ['MTC ISSUED', d.passes],
    ['REDEEMED', (d.states.REDEEMED||0)],
    ['EXPIRED', (d.states.EXPIRED||0)],
    ['READERS', d.readers.length],
    ['LEDGER', d.ledger_ok ? `${d.ledger_n} OK` : `BROKEN @${d.ledger_broken}`],
  ].map(([l,v])=>`<div class=c><div class=l>${l}</div><div class=v>${v}</div></div>`).join('');
  document.getElementById('strip').innerHTML = d.strip.map(w=>
    `<div class="wk${w.now?' now':''}"><div class=n>WK${w.wk}</div>
     <div class=dt>${w.open} – ${w.close}</div>
     ${w.closing?`<div class=cl>${w.closing} closing</div>`:''}</div>`).join('');
  document.getElementById('offers').innerHTML = d.offers.map(o=>
    `<tr><td class=gold>${o.id}</td><td>${o.item}</td>
     <td class=d>WK${o.start_week} + ${o.weeks}wk → FY${o.close_fy} WK${o.close_wk}
       <span class=mono>(${o.closes.slice(0,10)})</span></td>
     <td style="text-align:right">${o.issued}</td>
     <td style="text-align:right" class=g>${o.redeemed}</td>
     <td style="text-align:right">${o.rate}%</td>
     <td style="text-align:right">$${o.settled.toFixed(2)}</td></tr>`).join('');
  document.getElementById('anchors').innerHTML = d.anchors.map(a=>
    `<tr><td class=gold>FY${a.fy} WK${a.week}</td><td class=d>${a.at.slice(11,19)}</td>
     <td class=mono>${a.root}</td><td class=d>${a.chain}</td></tr>`).join('')
     || '<tr><td colspan=4 class=d>no anchors yet</td></tr>';
  document.getElementById('events').innerHTML = d.events.map(e=>{
    const bad = e.event.includes('REJECT');
    return `<tr><td class=d>${e.seq}</td><td class=d>${e.utc.slice(11,19)}</td>
     <td class=d>FY${e.fy} W${e.week}</td>
     <td class="${bad?'r':'g'}">${e.event}</td>
     <td class=mono>${e.subject}</td><td class="d mono">${e.detail.slice(0,90)}</td></tr>`;
  }).join('');
}
tick(); setInterval(tick, 4000);
</script>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/data.json"):
            body, ct = json.dumps(build()).encode(), "application/json"
        else:
            body, ct = PAGE.encode(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"MTC Sim-2.0 monitor: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
