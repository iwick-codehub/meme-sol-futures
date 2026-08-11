# Versions — meme-sol-futures

## 0.8.0 — 2026-08-11
- ORDER BOOK ratified: users make the market (house never takes a side); 5 standard rungs (10/50/100/250/500M, max 50% float); FDV basis incl. locks excl. true burns; ladders priced in SOL; dual minimums (1M lot AND 50 SOL notional, both binding); FIRM BOOK both sides (seller coins escrow at posting w/ 7-day expiry; buyer SOL locks at lift; counters escrow-backed); locked-token indicative rule + lock-recipient-as-escrow playbook
- Seller commission LOCKED: 10% of cleared strike, deducted at settlement (venue language, never dealer)
- Escrow engine Phase 2 committed: own Anchor program, atomic match, bulletproof discipline (upgrade authority burned, dual audits, TVL cap, zero hot keys); name candidates Deadbolt/Strongbox/SOLock (NOT SolStream)
- Open to ratify: max-ask rule (<=95% of live FDV), quote-expiry dial (7d), engine name

## 0.7.0 — 2026-08-11
- futures/THESIS.md filed — the founding argument: two prices (shelf vs pallet), the venue sells certainty, seller/buyer taxonomies, the dev-as-buyer signal trade ("insider buying without the pump"), the term-structure data asset, named risks (incl. selective-disclosure theater + wash-trade tell for screening)

## 0.6.0 — 2026-08-11
- TWO-ASSET LAW ratified and locked: every contract touches exactly SOL + the underlying coin, nothing else ever; USD-settled-via-USDC flavor KILLED (decision context recorded — do not re-litigate)
- Treasury policy locked: all fee revenue stays in SOL, never swept to dollars; directional views live only in treasury + float, never the instrument menu
- Canon page copy + preview render updated to SOL-only

## 0.5.0 — 2026-08-11
- All three dials RATIFIED ("yes to all"): 1.5 SOL flat writing fee, 50 SOL minimum notional, 90-95% FDV strike band — MARKET-SPEC + canon page copy updated
- Draft page renders built for testing: futures/shopify/preview/{crypto_landing,meme_futures}.html (what the hidden Shopify pages will be, pending the API token)

## 0.4.1 — 2026-08-11
- Seller-pays doctrine RATIFIED and locked in MARKET-SPEC: no premiums to sellers after Contract One; seller compensates the market via strike discount + flat SOL writing fee

## 0.4.0 — 2026-08-11
- futures/MARKET-SPEC.md — the market spec: fee doctrine LOCKED (one flat SOL writing fee covers ALL expenses + 2% of the coin in-kind as the house float, carried at zero); two settlement flavors (SOL-settled / USD-settled via USDC escrow); 2-week rotating term; listing criteria (freeze/mint authority = hard vetoes); per-contract Streamflow escrow architecture
- Proposed dials awaiting ratification: 1.5 SOL flat fee, 50 SOL minimum notional, 90-95% FDV strike band

## 0.3.0 — 2026-08-11
- Shopify crypto section drafted (canon-deposit pattern): futures/shopify/ = source of truth for /pages/crypto + /pages/meme-futures on the Instar Brands store
- Publication gates recorded: counsel review, Aug 31 settlement (name + escrow address non-public until then), Todd's final approval on live preview
- .gitignore: .shopify.env / *.env — API credentials never ride the auto-push

## 0.2.0 — 2026-08-11
- CONTRACT-001 escrow recorded + verified on-chain: wallet DsP3…2BNH holds exactly 1,000,000 ACM (Solscan + independent RPC read)
- futures/records/contract_001.json — canonical terms record, SHA-256 sealed (anchor f7de3b38…)
- futures/tools/anchor.py — seal/verify hash anchors, amendment history preserved
- futures/watcher.py — read-only escrow watcher (INTACT/BREACH/RELEASING/RELEASED), hash-chained observation log, state JSON for the dashboard; first live run: slot 438678202, balance 1,000,000, INTACT

## 0.1.0 — 2026-08-11
- Repo seeded from aladdins-castle (full ACM programs + MTC engine, history preserved)
- futures/ charter: SOL meme coin futures program, design laws (KRW, HMAC, auto-push, read-only)
- CONTRACT-001 recorded: 1M $ACM, settles 2026-08-31 noon EST, $500k valuation ($500 flat), $100 premium paid, Phantom "Futures Contract" escrow — executed in X DM with @derekdlc
