#!/usr/bin/env python3
"""Build the Open Orders board (body_orders.html) from futures/orders.json,
then publish. Order entry happens upstream (Todd -> Claude -> orders.json);
this just renders truth. Run: python3 orders_build.py"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ORDERS = json.loads((HERE.parent / "orders.json").read_text())["orders"]

rows = ""
for o in ORDERS:
    if o["status"] not in ("OPEN", "PARTIAL"):
        continue
    remaining = o["cap_usd"] - o["filled_usd"]
    rows += f"""<tr>
      <td class="ibx-mono">{o['id']}</td>
      <td><strong>{o['side']}</strong></td>
      <td><strong>{o['coin']}</strong></td>
      <td>{o['pricing']}</td>
      <td>{o['lots']}</td>
      <td>${remaining:,.0f} of ${o['cap_usd']:,.0f}</td>
      <td>{o['status']}</td>
    </tr>\n"""

body = f"""<style>
  .ibx {{ max-width: 860px; margin: 0 auto; line-height: 1.65; }}
  .ibx .ibx-kicker {{ font-size: .75rem; font-weight: 700; letter-spacing: .22em; text-transform: uppercase; color: #a8842c; }}
  .ibx h2 {{ line-height: 1.12; margin: .3em 0 .4em; }}
  .ibx .ibx-lede {{ font-size: 1.1em; opacity: .75; font-style: italic; }}
  .ibx table {{ border-collapse: collapse; width: 100%; margin: 1.4em 0; }}
  .ibx td, .ibx th {{ border-bottom: 1px solid rgba(128,128,128,.35); padding: 10px; text-align: left; font-size: .95em; }}
  .ibx th {{ font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; opacity: .7; }}
  .ibx .ibx-mono {{ font-family: monospace; }}
  .ibx .ibx-cta {{ display: inline-block; margin-top: 1em; padding: 14px 30px; background: #0f4c3a; color: #fff; font-weight: 700; letter-spacing: .08em; text-decoration: none; }}
  .ibx .ibx-fine {{ font-size: .85em; opacity: .7; }}
</style>
<div class="ibx">
  <div class="ibx-kicker"><a href="/pages/crypto">Crypto</a> &middot; <a href="/pages/terminal">Terminal</a> &middot; <a href="/pages/acm-bid-board">ACM Bid Board</a></div>
  <h2>Open Orders &mdash; The Execution Board</h2>
  <p class="ibx-lede">Standing, funded orders anyone can fill. Every order is
  escrow-backed; every fill becomes a tickered, escrowed, 14-day contract.
  The flat 10% spread is the only fee that exists.</p>
  <table>
    <thead><tr><th>Order</th><th>Side</th><th>Coin</th><th>Pricing</th>
      <th>Lots</th><th>Remaining / Cap</th><th>Status</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
  <h3>Fill an order</h3>
  <p>Contact us with the order ID, your lot size, and the wallet holding the
  coins (to fill a BID) or your SOL (to fill an ASK). We verify on-chain,
  issue a dedicated escrow address, and the contract goes firm the moment
  your side lands in escrow. Settlement in exactly 14 days.</p>
  <a class="ibx-cta" href="/pages/contact">FILL AN ORDER</a>
  <p class="ibx-fine">Post your own standing order: same contact &mdash;
  declare side, coin, pricing, and cap; posted orders must fund their escrow.
  All contracts write and settle in SOL. All sales final.</p>
</div>
"""
(HERE / "body_orders.html").write_text(body)
print(f"built body_orders.html with {sum(1 for o in ORDERS if o['status'] in ('OPEN','PARTIAL'))} open orders")
subprocess.run([sys.executable, str(HERE / "publish.py")], check=True)
