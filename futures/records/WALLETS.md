# Futures Desk Wallet Register

*Created 2026-08-11. Public addresses only — this file must NEVER contain a
seed phrase or private key (lock-record security law). The desk runs on a
dedicated fresh seed (paper only), isolated from personal, ACM, and hcp-arb
wallets. One contract = one additional escrow wallet, created per ticker at
hit time and recorded in its contract file.*

| Role | Phantom label | Address | Funded |
|------|--------------|---------|--------|
| Buyer (principal bids) | FUT BUYER — INSTAR BID | `PENDING` | exposure + gas |
| Treasury (10% commissions + fees, stays in SOL) | FUT TREASURY — COMMISSIONS | `PENDING` | gas only |
| Float (2% in-kind coins, carried at zero) | FUT FLOAT — 2% COINS | `PENDING` | gas only |

## Standing rules

- Buyer wallet holds ONLY the declared bid exposure — never more.
- Treasury/float addresses become InstarLock build-time constants at deploy.
- Labels never change without updating this register (naming discipline).
- Gas floor per wallet: 0.35 SOL (observed: 0.1 fails, 0.33 works).
- Verify first + last characters of any address before every transfer
  (address-poisoning defense).

## Existing wallets — NOT part of the desk

- `GNkKQWa4XHdvgF1x4edV3qF54xdz3LykWyd8cgWnVsHQ` — COINBASE+LOCKS (ACM lock
  recipient; 500M ACM returns Jul 4, 2027). Untouched.
- `Fc8T5MKEsqkK24JpQv8VNmk7cNehTN1RuixTtr1RUyho` — PUMP CREATE ACM (creator,
  custody, pump.fun rewards). Untouched.
- hcp-arb executor wallets — arb program only; keys live in a bot process
  and must never touch desk funds.
