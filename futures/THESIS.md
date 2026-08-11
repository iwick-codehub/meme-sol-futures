# THESIS — Why This Market Exists

*Filed 2026-08-11, from the founding discussion. The argument beneath
MARKET-SPEC.md.*

## The two prices

Every meme coin has two prices and only one is quoted. The pool quotes the
**shelf price** — what the next $50 costs. But nobody with size trades at the
shelf price. A dev, an early whale, an airdrop farmer holding 1M tokens of a
$500k-FDV coin owns paper worth $500 that would fetch a fraction of that if
actually sold, because selling it IS the crash. The **pallet price** — what
size actually clears for — has never had a venue. Every meme "portfolio" on
Solana is marked at a shelf price its owner can never realize.

That gap is the market. We are the first wholesale desk for meme coins.

## What the venue sells

**Certainty.** A fully-collateralized, physically-settled 14-day forward:
seller's coins escrowed at signing, buyer's SOL escrowed at signing, chain
releases both at expiry. No margin, no leverage, no default. The seller gets
a guaranteed exit at 90–95% of quoted FDV — a price the pool could never pay
them — and the buyer gets size at a discount that the pool would charge a
massive premium (slippage) to accumulate. Both sides get something the spot
market structurally cannot produce.

## Who sells, and why

- **Devs who need operating money without killing their coin.** A market-dump
  by the dev is the death of a meme coin's credibility. A forward sale is
  invisible to the pool: no sell pressure, no red candle, and the receipt is
  public — "sold forward at fair value, escrowed, no dump." Funding runway
  without betraying the chart.
- **Early whales who want out clean.** The overhang everyone fears exits
  through escrow instead of through the order book.
- **De-riskers who want to stay diamond-handed in public.** Coins in escrow
  produce zero sell pressure; the exit is real but the pool never feels it.

## Who buys, and why

- **Believers who want size.** Accumulating 1M tokens through a thin pool
  costs far MORE than FDV (slippage up). A forward is the only instrument
  that delivers size at a DISCOUNT to the quoted price.
- **The dev as buyer — the signal trade.** (Todd's insight, founding day.)
  A dev who market-buys their own coin pumps the price, makes followers pay
  more, and looks like exit-bait. A dev who buys a FORWARD on their own coin
  moves the price zero — followers still buy cheap on spot — while locking
  real SOL in escrow today to take delivery at today's valuation. It is a
  **costly signal**, the only kind that matters: insider buying without the
  pump. And it does a second job in the same stroke: the seller side of that
  contract is usually the whale overhang, so the dev absorbs the known
  future dump privately. One contract = faith shown + price untouched +
  overhang cleared.

## The data asset

Every strike that clears is the first honest print of a meme coin's pallet
price. The book, over time, is a term structure of meme confidence that
exists nowhere else — which coins clear at 95%, which only at 90%, which
can't find a buyer at any discount. The receipts are the product; the data
is the moat.

## What the house earns

Flow, not direction: 1.5 SOL flat per contract (covers all costs) + 2% of
the coins as the float — a zero-carried, house-aligned lottery book across
every coin we list. The venue's directional views live in the treasury (all
fees held in SOL) and the float, never in the instrument menu.

## Honest risks — named, not hidden

- The buyer carries full meme risk for 14 days. The coin can die in escrow.
  The discount is the pay for exactly that.
- The signal trade can be theater if disclosure is selective (forward-buy
  with one hand, spot-dump with the other). Venue answer: per-contract public
  receipts; a dev's self-buy should be publishable as a net position, and a
  counterparty-distinctness check belongs in screening (wash-trade tell).
- Listing screens are the venue's immune system. Freeze/mint authority vetoes
  are non-negotiable; a bad listing can break an escrow.
- Regulatory gate stands: counsel before the public transacts.

## Why us, why now

Thousands of coins launch daily; everyone builds launch ramps, nobody builds
exit ramps. We already hold the working parts: a live coin ($ACM) with 50% of
supply provably locked, a tested escrow procedure (Streamflow, run twice), a
receipts culture (hash-anchored records, read-only watchers), and Contract
One already executed and monitored on-chain. The first print settles
August 31. The venue opens on its receipt.
