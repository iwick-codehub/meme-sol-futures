# CONTRACT-001 — $ACM Futures (Test Contract)

**Status:** EXECUTED (agreed in X DM, 2026-08-11) · settles 2026-08-31
**Billed as:** the first-ever SOL meme coin futures contract.

## AMENDMENT 1 — 2026-08-11 (agreed by both parties)

Contract One now settles under venue economics: the 10% seller commission
applies at settlement — **seller nets $450** of the $500 strike. Todd
explained the math to Derek directly; Derek agreed. The $100 sent ahead of
signing stands as the sweetener that more than covers the commission (Derek's
all-in: $450 + $100 = $550 on a $500 position). ACM is the house coin: the
50 SOL notional floor and the 1.5 SOL flat fee are waived per the
house-coin exemption in MARKET-SPEC. Record re-sealed; prior anchor
preserved in history.

## Parties

| Role | Party |
|------|-------|
| Buyer (long) | Todd Wichmann (company vehicle TBD) |
| Seller (short) | Derek de la Cruz (@derekdlc) |

## Terms

| Term | Value |
|------|-------|
| Underlying | $ACM (SPL token, Solana) |
| Quantity | 1,000,000 ACM |
| Settlement date | August 31, 2026 — escrow release 11:59 AM EST, settlement noon EST |
| Strike valuation | $500,000 FDV → **$500 flat** for the 1M ACM (1B supply) |
| Premium | $100, paid to seller up front at signing (fully liquid immediately) |
| Escrow | Dedicated Phantom wallet named "Futures Contract" (seller-created, non-public): `DsP3zSSrHeEwSHUvjiZo3brqeXDMS6CZB3DeRxBk2BNH` |
| Underlying mint | `4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump` (per records/ACM_Lock_Record) |
| Escrow token account | `C8KGbEuVCvor5CjqcAaBwq2xsZLe5Gb5SsdCcMUUfhXc` |
| Sale character | Irrevocable — the ACM leaves the seller's wallet at signing and sits in escrow until release |

## Execution timeline (from the DMs, 2026-08-11)

1. ~3:11 PM — structure agreed: all through Phantom; seller to create the
   "Futures Contract" escrow wallet and DM the address (non-public until the
   test works, then take it public / wiki entry).
2. Premium plan was $100 USDT sent ahead of settlement ("so there is no risk on
   your part"); premium acknowledged as too expensive going forward — priced to
   make the test worth the counterparty's time.
3. 4:32 PM — **$100 of SOL sent and confirmed received** ("That is our
   'contract'"). Seller free to use it (buy $ACM or whatever).
4. Buyer restated the deal: "I agree to buy your 1 million ACM on August 31st
   at 500k valuation — $500 flat." Seller: **"Yes I agree."** 👍
5. Deal declared executed; programming to make it official (this repo).

## Open items

- [x] Escrow wallet address received (2026-08-11) and recorded above
- [x] 1,000,000 ACM verified in escrow, 2026-08-11 — Solscan (Todd) + independent RPC
      `getTokenAccountsByOwner` read (exactly 1000000 ACM in token account `C8KG…fhXc`)
- [ ] Settlement currency for the $500 strike (USDT? SOL at spot? — pin it before Aug 31)
- [ ] Premium accounting: plan said $100 USDT, execution was $100 SOL — confirm the
      SOL send IS the premium (not an extra), so the contract economics are clean
- [ ] Real premium-pricing math for future contracts (v1 number was made up)
- [ ] Wiki entry / public write-up after the test settles clean

## What the program must make official

- A signed, hash-anchored contract record (MTC-style ledger entry) of the terms above
- Escrow watcher: read-only monitor of the escrow wallet (balance = 1M ACM until release)
- Settlement checklist for Aug 31: release observed → strike paid → both confirmed
- HMAC-authenticated record trail; no program ever moves funds
