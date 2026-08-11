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

## Settlement flavors — LOCKED

The strike denomination is a product choice made at writing:

| Flavor | Strike fixed in | Escrowed as | Seller exits |
|--------|----------------|-------------|--------------|
| SOL-settled | SOL | SOL | the meme's own risk (keeps SOL exposure) |
| USD-settled | USD | **USDC** (never floating SOL) | meme risk AND SOL-complex beta — the full dollar exit |

USDC escrow is what kills FX drift on the USD flavor. All fees stay in SOL
regardless of flavor, because the house's costs are in SOL.

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

Proposed dials (Todd to ratify):
- Flat writing fee: **1.5 SOL** (observed ~0.33 SOL per Streamflow lock ×
  up to 3 locks per contract, plus margin)
- Minimum notional: **50 SOL** (keeps the flat fee ≤3% of the strike)
- Strike band: **90–95% of spot FDV** (the discount is the buyer's
  compensation; premiums to sellers trend to zero — Contract One's $100 was
  deliberate first-mover overpayment)

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
