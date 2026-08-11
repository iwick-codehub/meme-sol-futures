# InstarLock

The escrow engine for Instar meme coin futures. An Anchor (Solana) program
that enforces the MARKET-SPEC zero-risk law on-chain:

- **post** — firm quotes only: the seller's coins enter the program vault in
  the posting transaction. The two hard listing vetoes (freeze authority,
  mint authority) are checked ON-CHAIN — an unsafe mint cannot be posted.
- **lift** — the atomic match: buyer's full strike SOL locks and the listing
  becomes an irrevocable 14-day contract in ONE transaction. No default
  window exists on either side.
- **cancel** — unlifted quotes refund to the seller only after the 7-day
  quote life. Firm means firm.
- **settle** — permissionless crank at term end: 98% of coins → buyer,
  2% float → house, strike − 10% commission − 1.5 SOL flat fee → seller,
  fees → treasury. Anyone can crank; funds can only go where the contract
  says.

Economics baked as constants (no admin can change them): 14-day term,
7-day quote life, 10% commission, 2% float, 1.5 SOL flat fee, 1M-coin lot
minimum, 50 SOL notional minimum. Classic SPL Token only — Token-2022
transfer-tax coins are excluded by construction.

## Naming

Working brand: **InstarLock** (Instar Brands). Clear the mark with counsel
(Lori Krafte) before public use.

## Road to mainnet — non-negotiable gates (MARKET-SPEC discipline)

1. Build + localnet tests (all invariants).
2. Devnet deploy; full contract lifecycle exercised with test wallets
   (post → lift → settle, plus expiry-refund and every veto path).
3. TWO independent professional audits.
4. Deploy to mainnet, then **burn the upgrade authority** — after this, not
   even Instar can change the program. Set `house::ID` + replace
   `declare_id!` placeholders BEFORE this step; they are permanent.
5. Launch under a TVL cap that grows with track record; bug bounty live.

Until gate 4, Streamflow (proven twice on the ACM locks) carries all manual
contracts, including CONTRACT-001.

## Toolchain

Requires Rust, Solana CLI (agave), Anchor (via avm). See SETUP.md.
