#!/usr/bin/env python3
"""The 99-cent question: when does "Bring Back the Castle" stop breaking even?

THE LOOP THAT CLOSES ON ITSELF
  1. A user pays $0.99. Apple keeps its cut. We keep the rest.
  2. We spend from that: Solana account rent, a transfer fee, and G tokens of
     $ACM granted to the user as their membership credential.
  3. Whatever is left is profit, and 100% of profit buys more $ACM.
  4. Buying $ACM through a constant-product pool RAISES ITS PRICE.
  5. A higher price makes step 2 more expensive for the NEXT user.

So the question is not whether it works today. It is at what point step 2 eats
step 1, and that depends almost entirely on G -- how much $ACM each user is
granted -- because rent and fees are fixed in dollars while the grant is not.

TREATED AS NON-RECOVERABLE: the ~$0.41 Solana account rent is refundable only by
closing the account, which means shutting the system down. For a going concern it
is a cash outlay, and it is modelled as one.

THE 99 CENTS IS A DONATION TO BRING BACK ALADDIN'S CASTLE. It is not an
investment in $ACM, is not solicited as one, and the token grant is a membership
credential with no cash value inside the system.
"""
from __future__ import annotations

import json

# ---------------------------------------------------------------- assumptions
PRICE          = 0.99
APPLE_SMALL    = 0.15      # Small Business Program, under $1M/yr proceeds
APPLE_STD      = 0.30      # above $1M
SMALL_BIZ_CAP  = 1_000_000

RENT_SOL       = 0.00204   # associated token account rent, per wallet
SOL_USD        = 200.0
FEE_USD        = 0.001     # transfer fee
RENT_USD       = RENT_SOL * SOL_USD

ACM_PRICE_0    = 0.00026505
ACM_POOL       = 10_000_000       # RELEASED as the funding pool. Wallet holds
                                  # 11,767,037; the balance (1,767,037) is held
                                  # back as R&D reserve and never granted.
POOL_QUOTE_0   = 11_373.0         # quote side of the AMM (~half of $22,746 liq)

APPLE_FEE_STORE = 0.0             # Apple charges no per-transaction fee on top


def apple_cut(cumulative_proceeds: float) -> float:
    return APPLE_SMALL if cumulative_proceeds < SMALL_BIZ_CAP else APPLE_STD


def net_per_download(cumulative: float) -> float:
    return PRICE * (1 - apple_cut(cumulative))


def max_affordable_grant(acm_price: float, cumulative: float = 0.0) -> float:
    """How many $ACM we can grant and still break even at this price.

    net revenue = rent + fee + (G x price)   ->   G = (net - rent - fee) / price
    """
    head = net_per_download(cumulative) - RENT_USD - FEE_USD
    return head / acm_price if acm_price > 0 else float("inf")


def buy_impact(usd_in: float, quote_reserve: float, price: float):
    """Constant product. Buying with `usd_in` moves price by (1 + C/R)^2.

    This is the relation from KRW-C-2026-001 and it is the whole reason the loop
    has a ceiling: the square term means each additional dollar buys a smaller
    slice at a higher price. Buying also DEEPENS the pool, which is why the
    ceiling is reached slowly rather than immediately.
    """
    ratio = (1 + usd_in / quote_reserve) ** 2
    return price * ratio, quote_reserve + usd_in


def run(grant: float, downloads: int, step: int = 1000):
    """Walk the download curve and report where break-even fails."""
    price = ACM_PRICE_0
    reserve = POOL_QUOTE_0
    pool_left = ACM_POOL
    cum_gross = 0.0
    cash = 0.0
    acm_bought = 0.0
    rows = []
    breakeven_at = None

    n = 0
    while n < downloads:
        b = min(step, downloads - n)
        cut = apple_cut(cum_gross)
        net = PRICE * (1 - cut) * b
        cum_gross += PRICE * b

        # cost side
        rent = (RENT_USD + FEE_USD) * b
        need = grant * b
        from_pool = min(pool_left, need)
        pool_left -= from_pool
        to_buy = need - from_pool
        buy_cost = to_buy * price

        margin = net - rent - buy_cost
        if margin <= 0 and breakeven_at is None:
            breakeven_at = n + b

        # 100% of profit buys $ACM, which moves the price
        if margin > 0:
            price, reserve = buy_impact(margin, reserve, price)
            acm_bought += margin / price
            cash += 0.0          # profit is fully redeployed, none retained
        else:
            cash += margin       # a loss is a cash outlay

        n += b
        rows.append({"n": n, "price": price, "pool_left": pool_left,
                     "margin_per_user": margin / b, "cut": cut,
                     "cum_gross": cum_gross, "cash": cash,
                     "max_grant": max_affordable_grant(price, cum_gross)})
    return {"grant": grant, "rows": rows, "breakeven_at": breakeven_at,
            "final_price": price, "pool_left": pool_left,
            "acm_bought": acm_bought}


if __name__ == "__main__":
    print("=" * 78)
    print("  THE 99-CENT MODEL — Bring Back the Castle")
    print("=" * 78)
    n15 = net_per_download(0)
    n30 = PRICE * (1 - APPLE_STD)
    print(f"\n  per download        ${PRICE:.2f}")
    print(f"  Apple 15% (<$1M)    -${PRICE*APPLE_SMALL:.4f}  ->  we keep ${n15:.4f}")
    print(f"  Apple 30% (>$1M)    -${PRICE*APPLE_STD:.4f}  ->  we keep ${n30:.4f}")
    print(f"\n  account rent        -${RENT_USD:.4f}   (NON-RECOVERABLE as modelled)")
    print(f"  transfer fee        -${FEE_USD:.4f}")
    print(f"  ------------------------------------------")
    print(f"  HEADROOM for $ACM    ${n15-RENT_USD-FEE_USD:.4f}  (15% tier)")
    print(f"                       ${n30-RENT_USD-FEE_USD:.4f}  (30% tier)")

    print(f"\n  $ACM today ${ACM_PRICE_0:.8f}")
    print(f"  -> max grant that breaks even TODAY: "
          f"{max_affordable_grant(ACM_PRICE_0):,.0f} $ACM at 15%, "
          f"{max_affordable_grant(ACM_PRICE_0, 2e6):,.0f} at 30%")

    print("\n" + "=" * 78)
    print("  SCENARIOS — 100% of profit buys $ACM, which raises its price")
    print("=" * 78)
    print(f"\n  {'grant/user':>11s} {'downloads':>10s} {'pool gone at':>13s} "
          f"{'final $ACM':>12s} {'break-even fails':>17s}")
    for grant in (1, 100, 1_000, 1_632, 5_000, 10_000):
        for dl in (1_000_000,):
            r = run(grant, dl)
            gone = next((x["n"] for x in r["rows"] if x["pool_left"] <= 0), None)
            be = r["breakeven_at"]
            print(f"  {grant:>11,} {dl:>10,} "
                  f"{(f'{gone:,}' if gone else 'never'):>13s} "
                  f"${r['final_price']:>11.8f} "
                  f"{(f'{be:,} dl' if be else 'holds'):>17s}")
    json.dump({"generated": True}, open("/dev/null", "w"))
