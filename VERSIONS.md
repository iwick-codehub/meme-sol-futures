# Versions — meme-sol-futures

## 0.11.0 — 2026-08-11
- /pages/acm rebuilt as an owned-content mirror of aladdinscastle.xyz (hero, four tiles, contract address, mission, doxxed-dev/press/X/Telegram links, tokenomics) — LIVE; tokenomics corrected from the .xyz site's stale "40% dev allocation locked permanently" to the verified claim: 50.00% of total supply locked until July 4, 2027 (lock-record precision doctrine); added Bid Board cross-link
- Main menu: "Chipso" item renamed "Aladdin's Castle" -> /pages/acm (verified on live homepage, desktop+mobile); Chipso page unpublished (404s, content preserved)
- PRICING ENGINE drafted in MARKET-SPEC (Todd to ratify): corridor pricing — floor = on-chain simulated PoolExit%(lot), ceiling 95% FDV, strike = floor + k*(ceiling-floor), k~0.25 baseline adjusted by depth ratio / 14d vol / turnover / overhang / KRW temperature gate; flat 90% rejected (adverse selection); inputs public, weights proprietary; optimize flow*edge

## 0.10.1 — 2026-08-11
- ALL THREE PAGES PUBLISHED LIVE by Todd's explicit order (quiet launch, unlinked from nav): instarbrands.com/pages/crypto, /pages/meme-futures, /pages/acm-bid-board — all verified 200 with content rendering
- Publication gates: lifted by the author; counsel conversation REMAINS OPEN (upstairs-market/delayed-print framing); Derek's name + escrow address still absent from all pages (that gate holds)

## 0.10.0 — 2026-08-11
- SHOPIFY LIVE (hidden): claude-site-manager app installed on instar-brands.myshopify.com; token mint via client-credentials proven; publish.py upsert tool built; THREE pages created hidden — /pages/crypto, /pages/meme-futures, /pages/acm-bid-board
- $ACM Bid Board built: Standard tier (1M lots @ $500k valuation, net $450/lot) + Whale tier (10M+ lots @ $200k valuation, $200/million) — standing funded bids, 4-step hit-a-bid flow, dollars-for-readability/SOL-at-signing disclosure
- House-coin exemption RATIFIED: ACM exempt from 50 SOL floor, flat fee waived, 10% commission applies
- CONTRACT-001 AMENDMENT 1 sealed (prior anchor in history): settles under venue economics, seller nets $450; $100 pre-payment = sweetener (agreed by both parties)

## 0.9.1 — 2026-08-11
- Balance-gated menu RATIFIED: level menu is COMPUTED from the seller's verified on-chain balance (running sum as ladder builds; same level repeatable), capped by 500M/50% float, floored by 50 SOL notional; paste to browse, signature at escrow = the ownership proof. Notional-floor math flagged: at ACM's current FDV the first clearing level is ~50M coins (1M lot = dust); Contract One predates the spec

## 0.9.0 — 2026-08-11
- InstarLock BUILT (source complete, build pending toolchain): Anchor program at instarlock/ — post (firm quotes, coins vault at posting, freeze/mint-authority vetoes enforced ON-CHAIN) / lift (atomic match: strike SOL locks + contract goes irrevocable in one tx) / cancel (refund only after 7d quote life) / settle (permissionless crank: 98/2 coins, strike -10% -1.5 SOL to seller); economics baked as constants, no admin instructions, classic SPL only (transfer-tax coins excluded by construction)
- Name locked: InstarLock (Instar Brands) — clear with Lori; "SolStream" rejected (Streamflow conflict)
- Road-to-mainnet gates in instarlock/README.md: localnet tests -> devnet lifecycle -> 2 audits -> deploy + BURN upgrade authority -> TVL cap

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
