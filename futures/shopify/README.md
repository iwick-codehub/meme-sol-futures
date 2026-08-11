# Shopify Crypto Section — Canon Deposit

Source-of-truth copy for the **Crypto** section of the Instar Brands Shopify site.
Same law as the D&DoD deposit in `doegard/product/shopify/`: this repo is canon,
Shopify renders it. Edits happen here first, then sync to the live pages via the
Admin API.

| File | Live page | Status |
|------|-----------|--------|
| crypto_landing.md | /pages/crypto | DRAFT — publish gated on Todd's go |
| meme_futures.md | /pages/meme-futures | DRAFT — public naming/wallet gated on Aug 31 settlement |

## Publication gates (do not lift silently)

1. **Counsel review** before the section invites the public to transact (the
   fully-collateralized physical-settlement structure is the friendly fact —
   but it goes past counsel first).
2. **Aug 31 settlement** — per the DM agreement, the counterparty's name and
   the escrow wallet address stay non-public until CONTRACT-001 settles clean.
   Until then the pages tell the story without the address, and the seller is
   "our first counterparty."
3. Todd approves final copy on the live-preview before publish.

## API access

Credentials live in `.shopify.env` at repo root — **gitignored, never committed,
never pushed** (this repo auto-pushes; secrets do not ride along).
