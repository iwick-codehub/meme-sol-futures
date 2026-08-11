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

All fee revenue stays in SOL. Never swept to dollars. The float (2% in-kind)
is carried at zero until sold; if sold, proceeds are SOL. The house's
directional views live ONLY in the treasury and the float — never in the
instrument menu.

## Fee schedule — LOCKED doctrine (dials proposed)

1. **Flat SOL writing fee, one number, covers ALL expenses** — escrow rent,
   gas, Streamflow's 0.5% skim, and margin. Denominated in SOL so it never
   drifts. Deducted from the seller's strike payout at settlement (the house
   fronts the on-chain costs at writing; the seller never needs SOL upfront).
2. **2% of the meme coin in-kind — the float.** Taken from the escrowed coins
   at settlement (buyer receives 98%). This is the house's home-run book:
   an aligned lottery-ticket portfolio across every coin we list. Carried at
   **zero value** on the cash basis until actually sold. Never counted on to
   pay bills.

**Seller commission — LOCKED (ratified 2026-08-11): 10% of the cleared
strike, deducted at settlement.** Venue language, never dealer language: the
house does not "pay 90%" — the buyer pays the full strike, the seller nets
90% after commission. First-in-kind pricing (auction-house tier), justified
against the seller's true alternative (30–80% pool slippage on size). Full
take stack = 10% commission + 1.5 SOL flat + 2% in-kind float ≈ 13% on a
minimum contract; monitor clear-rates, dial when competition arrives.

**Who pays — LOCKED (ratified by Todd, 2026-08-11): the SELLER pays.** The
seller is the one getting the miracle — a guaranteed full-size exit at locked
valuation that the pool could never absorb. So: no premiums to sellers after
Contract One (its $100 was deliberate first-mover overpayment); the seller
compensates the market through the strike discount and the flat writing fee.

Dials — RATIFIED by Todd, 2026-08-11 ("yes to all"):
- Flat writing fee: **1.5 SOL** (observed ~0.33 SOL per Streamflow lock ×
  up to 3 locks per contract, plus margin)
- Minimum notional: **50 SOL** (keeps the flat fee ≤3% of the strike)
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
notional floor keeps fixed costs (~1 SOL rent/gas + 1.5 SOL fee) under ~3%
of the deal and keeps dust off the receipts page.

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
page, and the house absorbs the writing costs as market-seeding expense (the
1.5 SOL flat fee is WAIVED on ACM contracts — on a ~3 SOL notional it would
be absurd). The 10% commission still applies (Contract One: $500 strike −
$50 = $450 net to seller). Non-ACM coins keep the full floor. If/as ACM's
FDV rises, lot notionals grow back toward the standard floor mechanically —
no prediction required, it's arithmetic either way.

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

## Listing criteria — LOCKED structure

Binary tells, all checkable on-chain, screened in listing order. Hard vetoes
first (either one breaks the escrow itself):

| # | Tell | Rule |
|---|------|------|
| V1 | Freeze authority | REVOKED or veto (creator could freeze our escrow) |
| V2 | Mint authority | REVOKED or veto (infinite mint voids the valuation) |
| S1 | Transfer tax / token extensions | none |
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
