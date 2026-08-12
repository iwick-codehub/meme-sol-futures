# DESK RUNBOOK — Executing a Hit on the ACM Bid (Manual Rails)

*v1 · 2026-08-11. This is how a bid goes from quote to sealed contract TODAY,
on the rails proven by Contract One — no InstarLock required. Programs
record, verify, and watch; every transfer is made by a human in their own
wallet. Todd is the disclosed principal buyer on all ACM bids.*

## The zero-risk order of operations

1. **Seller reaches out** (bid board → contact): wallet address, lot size,
   tier. No commitment yet on either side.
2. **Desk verifies on-chain** (read-only): wallet holds the lot
   (`getTokenAccountsByOwner`), coin passes the screen (for ACM: already
   listed). Lot ≥ 1M coins.
3. **Desk issues the contract quote**: run `pricer.py` at that moment →
   strike, bid (seller's net), ticker (`ACM` + expiry DOY + year, expiry =
   today + 14 days). Quote held for a stated window (suggest 60 minutes).
4. **Fresh escrow wallet created** (Phantom, named for the ticker, one
   contract = one wallet = one Solscan link). Address goes to the seller.
5. **Seller's coins land in escrow.** Verify on-chain. THE QUOTE IS NOW
   FIRM — this is the moment "indicative" becomes "contract."
6. **Buyer's SOL lands in escrow** (Todd sends the full strike in SOL to the
   same escrow wallet) — both legs locked. Target: within the hour; the
   contract is not sealed until both legs sit in escrow.
7. **Seal the record**: `records/contract_NNN.json` (parties, ticker, mint,
   lot, strike SOL, bid/net SOL, escrow address, both funding txids,
   timestamps, expiry = seal time + exactly 14 days) → `anchor.py seal`.
   Point a watcher at the escrow (copy `watcher.py` pattern; INTACT =
   coins + SOL both present).
8. **Settlement day** (expiry timestamp, to the hour): from escrow —
   strike × 90% in SOL → seller · 98% of coins → buyer · strike × 10% →
   treasury · 2% of coins → float wallet. (ACM exemption: no 1.5 SOL flat
   fee.) Each transfer is a human-signed Phantom transaction, checked off
   against the sealed record.
9. **Publish the receipt**: escrow Solscan link + sealed record hash go on
   the public receipts trail. The ticker retires.

## What must exist before the first hit

- [ ] Buyer wallet funded with enough SOL to honor the standing bid
      (per 1M-lot hit: ~1.6 SOL at today's ACM strike; size the float for
      several simultaneous hits and state a max exposure)
- [ ] Escrow-wallet creation discipline per the ACM lock record (fund gas,
      label by ticker, record address before use)
- [ ] Treasury + float wallet addresses designated (also needed for
      InstarLock's build-time constants later)
- [ ] Counsel sign-off — the board is now a public solicitation to trade
      with a disclosed principal; this is the conversation, have it first

## Notes

- Quotes on the tape are indicative; ONLY step 5 makes a price firm.
- If the seller never funds escrow, nothing happened — no exposure.
- If the buyer leg fails after the seller funds (should never happen —
  Todd IS the buyer), coins return to the seller immediately and the
  incident goes in the log. The manual window between steps 5 and 6 is the
  one gap InstarLock's atomic match eliminates; keep it under an hour.
