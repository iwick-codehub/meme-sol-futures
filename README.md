# MTC Sim-2.0

Simulation of the $ACM / Meme Token Credit settlement system.
**Nothing here is real** — no chain writes, no funded wallets, no scanners.
Brands are test fixtures only.

    core/walmart_cal.py   the spine: Walmart weeks, Sat 00:00 - Fri 23:59 ET
    core/auth.py          HMAC-SHA256 — the standard for every channel
    core/ledger.py        append-only, hash-chained, Merkle-anchorable
    core/wallet.py        noob-path wallet minting (we custody the key)
    core/mtc.py           the pass: Apple Wallet + HMAC QR, never a coin
    core/engine.py        enrol / fund / issue / redeem / expire / anchor
    sim.py                end-to-end season run
    monitor.py            http://127.0.0.1:8901

    python3 sim.py --fresh      # run a season
    python3 monitor.py          # watch it

## Decisions locked
- Walmart week = Sat 00:00:00 → Fri 23:59:59 **America/New_York**
- Week 1 is Walmart week 1; no parallel numbering
- 53-week years: mirror Walmart, never compute our own length
- Offer duration 1–52 weeks, rolls into the next fiscal year if it must
- HMAC on every channel — key id, nonce, constant-time compare
- MTC is an Apple Wallet pass, **not** a token. Chain does one job: prove ≥1 $ACM
