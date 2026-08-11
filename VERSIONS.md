# Versions — meme-sol-futures

## 0.2.0 — 2026-08-11
- CONTRACT-001 escrow recorded + verified on-chain: wallet DsP3…2BNH holds exactly 1,000,000 ACM (Solscan + independent RPC read)
- futures/records/contract_001.json — canonical terms record, SHA-256 sealed (anchor f7de3b38…)
- futures/tools/anchor.py — seal/verify hash anchors, amendment history preserved
- futures/watcher.py — read-only escrow watcher (INTACT/BREACH/RELEASING/RELEASED), hash-chained observation log, state JSON for the dashboard; first live run: slot 438678202, balance 1,000,000, INTACT

## 0.1.0 — 2026-08-11
- Repo seeded from aladdins-castle (full ACM programs + MTC engine, history preserved)
- futures/ charter: SOL meme coin futures program, design laws (KRW, HMAC, auto-push, read-only)
- CONTRACT-001 recorded: 1M $ACM, settles 2026-08-31 noon EST, $500k valuation ($500 flat), $100 premium paid, Phantom "Futures Contract" escrow — executed in X DM with @derekdlc
