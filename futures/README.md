# Meme SOL Futures

Futures contracts on Solana meme coins. First underlying: **$ACM** (Aladdin's Castle).

This repo is seeded from the full `aladdins-castle` codebase (history preserved) so the
MTC private-ledger engine, wallet architecture, and records conventions are available
as the basis for the futures program. New work lives under `futures/`.

## The idea (from the X discussion, 2026-08-11)

Spot markets are spot markets. The new instrument: a company states "I'll buy N tokens
from you on date D at valuation V" — a futures contract on an otherwise illiquid meme
coin position.

Mechanics of the v1 (test) structure:

1. Seller moves the tokens NOW into a dedicated escrow wallet (irrevocable sale —
   the coins leave the seller's wallet at signing).
2. Buyer pays the futures **premium** to the seller immediately (fully liquid,
   the seller's reason to do the deal).
3. On settlement day the escrow releases the tokens to the buyer and the buyer pays
   the strike (the agreed valuation price).

Seller gets certainty + immediate cash; buyer gets a locked forward price.
Premium pricing math: TBD (v1 premium is an admittedly-too-rich made-up number
to compensate the test counterparty).

## Contracts

| # | Underlying | Status | Spec |
|---|-----------|--------|------|
| 001 | $ACM | EXECUTED (test) — settles 2026-08-31 | [CONTRACT-001.md](CONTRACT-001.md) |

## Design laws

- KRW principles apply (spectroscope / read-only / rolling-average / temperature-gated).
- HMAC-SHA256 on every channel.
- Every build commits AND pushes to GitHub immediately (disaster-recovery law).
- No program in this repo ever executes a trade or moves funds; programs record,
  verify, and monitor. Transfers are made by the human parties in their own wallets.
