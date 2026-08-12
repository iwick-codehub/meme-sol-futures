# Meme SOL Futures — Market Spec

**v0.4.0 · 2026-08-11.** Locked decisions vs proposed dials are marked. Contract
One (CONTRACT-001) predates this spec and keeps its test economics.

## Instrument — LOCKED

A **fully-collateralized, physically-settled forward** on a Solana meme coin.
Both legs escrow at signing; neither side can default; market risk stays with
the buyer, which is what the buyer is paid for. No margin, no leverage.

## Term — LOCKED (for now)

Every contract runs **exactly 2 weeks** (rotating 24-hour clock) from writing.
Variable terms later. Term is written into the sealed contract record.

## The Two-Asset Law — LOCKED (ratified by Todd, 2026-08-11)

**Every contract touches exactly two assets: SOL and the underlying meme
coin.** Nothing else, ever. Strike fixed in SOL, escrowed in SOL. All fees in
SOL. No stablecoins anywhere in the system.

The USD-settled-via-USDC flavor was considered and KILLED (2026-08-11): a
seller who wants dollars swaps their SOL after settlement — their trade,
outside the venue. What the law buys: one escrow procedure, one watcher path,
no stablecoin custody, and the public house rule ("everything is denominated
and paid in SOL") is literally true. Decision context, should it resurface:
the dollar-exit flavor was the SOL-hedge feature; Todd chose venue simplicity
and SOL denomination over offering it. Do not re-litigate — remind.

## Treasury policy — LOCKED

All fee revenue stays in SOL. Never swept to dollars. The house's
directional views live ONLY in the disclosed principal book — never in the
instrument menu. (2% float retired 2026-08-12.)

## Fee schedule — LOCKED doctrine (dials proposed)

**ONE NUMBER — RATIFIED 2026-08-12: the flat 10% spread is ALL-IN.**
The 2% in-kind float is RETIRED (dust liability dressed as a lottery; house
directional bets live ONLY in the principal book, deliberately) and the
1.5 SOL writing fee is FOLDED INTO the spread (the 10% covers rent, gas,
ops, everything). Buyer receives 100% of the coins at exactly the quoted
strike; seller nets exactly 90%. Marketing sentence and fee schedule are
the same sentence: "10%. That's everything." Decision context if it
resurfaces: simplicity compounds trust, cleans HCP cash-basis books
(SOL-only revenue), and shrinks InstarLock's audit surface — remind,
don't re-litigate.

**Seller commission — LOCKED (ratified 2026-08-11): 10% of the cleared
strike, deducted at settlement.** Venue language, never dealer language: the
house does not "pay 90%" — the buyer pays the full strike, the seller nets
90% after commission. First-in-kind pricing (auction-house tier), justified
against the seller's true alternative (30–80% pool slippage on size). Take = the flat all-in 10% spread; monitor clear-rates, dial when
competition arrives.

**Who pays — LOCKED (ratified by Todd, 2026-08-11): the SELLER pays.** The
seller is the one getting the miracle — a guaranteed full-size exit at locked
valuation that the pool could never absorb. So: no premiums to sellers after
Contract One (its $100 was deliberate first-mover overpayment); the seller
compensates the market through the strike discount and the flat 10% spread.

Dials — RATIFIED by Todd, 2026-08-11 ("yes to all"; fee dial superseded
2026-08-12 by the all-in 10%):
- Minimum notional: **50 SOL** (keeps fixed on-chain costs ≪ the spread)
- Strike band: **90–95% of spot FDV** (the discount is the buyer's
  compensation for two weeks of meme risk)

## The Order Book — RATIFIED 2026-08-11

Users make the market; the house never takes a side.

**Flow:** type the coin symbol → select from the screened list (criteria
checked live, on-chain) → declare side → build a ladder.

**Valuation basis — LOCKED:** fully-diluted market cap **including locked
tokens** (locks are still supply — they come home), excluding only **true
burns** (provably destroyed: burn address / supply reduced on the mint).
Computed on-chain, never claimed.

**The five rungs — LOCKED:** 10M · 50M · 100M · 250M · 500M coins.
500M / 50% of float is the absolute max per contract (beyond that it's a
change of control, not a trade). Standard rungs = standardized contracts =
comparable prints = the term-structure data asset.

**Ladders:** a seller posts prices per rung ("X at this price, X more at
this price"); the math derives break points. **All prices entered in SOL**
(Two-Asset Law; a dollar shadow may be displayed, the contract number is
SOL).

**Dual minimums — LOCKED, both binding:** lot ≥ 1,000,000 coins AND
notional ≥ 50 SOL. Notional = lot × price = what the buyer pays. The
notional floor keeps fixed on-chain costs (~1 SOL rent/gas) far below the
spread and keeps dust off the receipts page.

**Balance-gated menu — RATIFIED 2026-08-11:** the seller's wallet (pasted to
browse; connected + signed to post) is read on-chain, and the level menu is
COMPUTED, never chosen: show every level L where
(1) L ≤ remaining verified balance (a running sum — each posted rung
subtracts; the same level may repeat while balance covers it, e.g. a 2M
wallet can take the 1M option twice),
(2) L ≤ the 500M / 50%-of-float cap, and
(3) L × price ≥ 50 SOL notional.
Gate (3) means micro-FDV coins start at bigger rungs (at ACM's current
~2,800 SOL FDV the first clearing level is ~50M; a 1M lot ≈ 2.8 SOL = dust).
This is by design — every print is a real trade. Ownership is ultimately
proven by the escrow signature at posting, not the pasted address.

**House-coin exemption — RATIFIED 2026-08-11:** **$ACM contracts are exempt
from the 50 SOL notional floor** — 1M-lot ACM contracts post at ANY SOL
value. The house coin seeds the book: small ACM prints populate the receipts
page, and the house absorbs on-chain writing costs as market-seeding
expense. The all-in 10% still applies (Contract One: $500 strike −
$50 = $450 net to seller). Non-ACM coins keep the full floor. If/as ACM's
FDV rises, lot notionals grow back toward the standard floor mechanically —
no prediction required, it's arithmetic either way.

**Open orders, both sides — RATIFIED 2026-08-12:** anyone may DECLARE a
standing order on either side and let the market fill it: a posted ASK
escrows the coins (already law); a posted BID escrows its SOL up to the
declared cap ("I will buy up to $10K of ACM at a $500k-valuation strike").
Partial fills lot by lot; every fill mints a real tickered contract.
Physical delivery on every fill — no all-SOL coinless variant exists (that
is cash settlement, retired; the coins moving is the fortress). Venue
economics: on matched third-party flow the house earns 10% of strike in
SOL + the 2% float, zero inventory, zero directional risk. HOUSE-PRINCIPAL
orders are NOT revenue events — a house bid above market is deliberate,
capped, disclosed SPEND (support/signal), booked to the principal wallet,
never confused with commission income.

**Firm book, both sides — LOCKED (zero-risk law):**
- Seller: posting a rung REQUIRES the coins in listing escrow at posting.
  Quotes carry an expiry (7 days, dial) — auto-returned if unlifted.
- Buyer: browsing locks nothing; a LIFT locks the full strike SOL at the
  instant of execution; a COUNTER-OFFER locks the buyer's SOL when posted,
  auto-refunded on expiry/decline.
- Contract goes irrevocable at match; runs exactly 14 days from execution
  timestamp.

**Locked-token rule:** tokens inside a third-party time-lock may be quoted
INDICATIVE ONLY; the quote goes firm the moment coins land in escrow.
Playbook upgrade (the beautiful version): at coin creation, set the supply
lock's recipient to a venue-issued escrow address, so lock → listing escrow
with no human in the gap. ("Create, lock 50%, forward-sell the unlock" is
the flagship lifecycle.)

**Max-ask rule (PROPOSED, ratify):** no rung may be posted above 95% of
live FDV — keeps delusional asks from cluttering the book.

## Escrow engine — Phase 2 commitment (ratified direction, 2026-08-11)

Own Anchor program replacing Streamflow for the book — BUILD ORDERED 2026-08-11, source at instarlock/. Name: **InstarLock** (Instar Brands; clear mark with Lori). Rejected candidates:
**Deadbolt** [recommended], Strongbox, SOLock — clear with counsel; NOT
"SolStream," one letter from Streamflow's brand). The killer feature is the
**atomic match**: one transaction locks buyer SOL + flips listing escrow to
contract escrow + writes terms — no gap, no default window, on either side.

Bulletproof discipline (the honest version of "100% hack proof" — absolutes
don't exist; this is the standard): minimal program (escrow in, timed
release out, nothing else) · **upgrade authority burned** · two independent
audits before real funds · invariant tests in CI · launch TVL cap that
grows with track record · bug bounty · zero hot admin keys — the house
physically cannot touch escrow, so neither can anyone who hacks the house.
Until Deadbolt is audited and live, Streamflow (proven twice) carries
manual contracts.

## The Pricing Engine — the house edge (RATIFIED 2026-08-11)

Two pricing regimes coexist:
1. **Marketplace (order book):** users set asks, buyers lift — no model
   needed; the house earns the commission either way.
2. **House bid board (disclosed principal):** WE set the strike. This is
   where the secret sauce lives.

**Corridor pricing — never one flat number.** A flat 90% would be picked
off by adverse selection: the only sellers eager to hit a flat bid are the
ones whose lots are worth far less than 90% (the trash finds you). Each bid
is computed inside a corridor:

- **Floor = PoolExit%(L):** the simulated proceeds of actually market-selling
  lot L into the live AMM reserves right now (computable exactly on-chain —
  walk the curve). This is the seller's true alternative; bidding below it
  is pointless, bidding at it is the whole pitch ("we beat your only exit").
- **Ceiling = 95% of FDV** (symmetric with the max-ask rule).
- **Strike% = PoolExit% + k × (95% − PoolExit%)** — k is the seller's share
  of the illiquidity surplus. Baseline k ≈ 0.25, adjusted per coin by
  measured, on-chain, KRW-style spectroscope metrics:
  · **Depth ratio** (lot notional ÷ pool depth) — the dominant term. Todd's
    two ACM tiers already sample this curve: 1M lots near-market, 10M+ deep.
  · **Realized 14-day volatility** (rolling average) — hotter coin, deeper cut.
  · **Turnover** — how fast size recycles into organic demand.
  · **Overhang** — holder concentration behind THIS seller (who exits next?).
  · **Temperature gate** (KRW law) — cold markets: widen or stand down.
    Never chase.
- **Inputs are public; the weights are ours.** Credit-score economics: the
  data is on-chain for anyone, the model is the moat. Bids shown are funded
  and honored; sellers can always decline. That is legitimate dealer pricing,
  not information asymmetry about the asset.
- **Optimization target: flow × edge, never edge alone.** A too-greedy book
  starves the clear-rate, and the commission side of the house eats flow.

## Contract tickers + two-sided quotes — RATIFIED 2026-08-11

**Ticker convention:** `SYMBOL5 + DOY + YYYY` — first 5 letters of the coin
symbol (non-alphanumerics stripped, uppercased) + expiry as 3-digit
day-of-year + 4-digit year. Example: `TRUMP2372026` = TRUMP, expiring day
237 of 2026 (Aug 25). Day-of-year kills US/EU date ambiguity. Every contract
written today expires exactly 14 days out, so all of a day's tickers share
one expiry code.

**Two-sided quote on every standard 1M-coin contract:**
- **ASK** = the full strike (what a buyer pays to own the contract).
- **BID** = strike × 90% (what the desk pays a seller right now).
- **The bid/ask spread IS the 10% commission.** The size/illiquidity
  discount lives in the ask's distance below spot (≥5%, deeper per the
  corridor); the spread is the house take. One number system, two-sided
  market, no hidden components.

## Phase roadmap — the speculative market (direction set 2026-08-12)

Todd's market-structure call: like all real futures markets, scale comes
from traders taking naked longs/shorts without owning the coin — hedgers
seed the market, speculators ARE the market, and a healthy two-sided
trader base also dissolves the launch-day adverse-selection problem (the
informed seller trades against the market's judgment, not the house).

- **Phase 1 (LIVE):** covered, physically-settled, fully-escrowed forwards.
  Covered-only BY CONSTRUCTION — the zero-risk law forbids naked positions
  in this instrument. The trust layer and the receipts tape.
- **Phase 2 (REVISED 2026-08-12 — Todd's forced-cover insight):** the
  fully-covered OPTIONS market. No cash settlement, no oracle, no margin,
  no liquidation — ever. Two instruments, both 100% collateralized at the
  atomic write:
  · **Covered calls:** a writer without coins is FORCE-COVERED — the write
    transaction buys the lot via the router and escrows it in the same
    atomic tx that mints the contract ("uncovered" in feel, covered in
    fact — the thing you cannot do with corn). Contract cost includes the
    purchase, slippage honestly priced.
  · **Cash-secured puts:** the true short = BUYING a put (premium-only,
    capped loss, profits on decline); the put writer escrows the full
    strike in SOL at signing.
  Settlement is physical exercise/expiry — kills the paint-the-index
  problem entirely (prior capped-cash-settled design OBSOLETE, do not
  revive). Known reflexive dynamic: call-writing force-buys the underlying
  at write time (structural buy pressure; also a gaming surface — listing
  rules must address). The hero paper book is the empirical premium study
  for 2x-strike launch-day calls. REGULATORY STEP-CHANGE stands: public
  options venue = CFTC territory; counsel BEFORE first outside position.
- **Phase 3:** the basis between the futures curve and spot publishes as
  the market's forecast of every coin's 2-week fate — a data product
  unique to the venue.

## Listing criteria — LOCKED structure

Binary tells, all checkable on-chain, screened in listing order. Hard vetoes
first (either one breaks the escrow itself):

| # | Tell | Rule |
|---|------|------|
| V1 | Freeze authority | REVOKED or veto (creator could freeze our escrow) |
| V2 | Mint authority | REVOKED or veto (infinite mint voids the valuation) |
| S1 | Transfer tax / fee extensions | none (NOTE 2026-08-11: pump.fun now mints on Token-2022 — the program itself is NOT a veto, only fee/hook extensions are; InstarLock must support Token-2022-without-extensions via token_interface before mainnet) |
| S2 | Liquidity | LP locked or burned; minimum pool depth (dial TBD) |
| S3 | Volume | minimum daily volume (dial TBD) |
| S4 | Age | minimum token age (dial TBD) |
| S5 | Concentration | top-10 holder cap (dial TBD) |

## Escrow architecture — LOCKED

- **One contract = one dedicated escrow wallet = one public Solscan link.**
  Never pooled (per the ACM lock record's forward policy).
- Phase 1 releases via **Streamflow time-locks** (proven procedure from the
  ACM locks): coin leg = two non-cancelable locks from the seller's deposit
  (98% → buyer, 2% → house float wallet), strike leg = SOL/USDC locked to the
  seller, all unlocking at expiry. Release is enforced by chain, not by keys.
- Phase 2: custom Anchor program with escrow PDAs.
- House programs are read-only observers (watcher per contract, hash-chained
  logs). No program ever moves funds.

## Publication gates

Counsel review before the public can transact; Contract One's counterparty
name + escrow address stay non-public until Aug 31 settles clean; Todd
approves live copy. (Mirrored in futures/shopify/README.md.)
