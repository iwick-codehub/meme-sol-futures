# Aladdin's Castle iOS — locked doctrine

Decision record for the v1 app. Supersedes conflicting notes in
`design/design_pack_v1.html` where marked. Written 7 Aug 2026.

The design pack's four original rules still stand and are not restated here:
MTC lives in our ledger · the chain is read-only · QR now, NFC later ·
network is optional.

---

## 1 · The app is a paid game, not a donation and not an IAP

**$0.99 storefront price.** Not an in-app purchase. The earlier "$0.99 IAP
Founder's Badge" plan is dead.

The app is a **retro pinball-style game**, and that is deliberate: guideline
**4.2 minimum functionality** is what sinks thin paid apps, and a real game
answers it outright. The loyalty layer is the reason people keep the app; the
game is the reason they can be charged for it.

"Donation" framing was rejected — donations through Apple are reserved for
registered nonprofits, and Instar Brands is an LLC.

## 2 · The one rule everything else follows from

> **Never let a payment and a token arrive in the same motion.**

This is the whole compliance question, reduced. Not "no crypto in the app" —
that was an over-correction. The app may read the chain, hold a key, and prove
ownership. What it must not do is make a token appear *because* money went to
Apple.

In a paid app every holder is a buyer, so an automatic grant on install — even
delivered out-of-band, even hourly, even disclosed — is still pay-Apple-receive-
token on a delay. Disclosure does not fix it. Only breaking the causation does.

**How it is broken:** the free $ACM is claimable **by anyone at
instarbrands.com with no purchase**. The token is then not consideration for the
99¢; a non-buyer gets the identical thing for free, and the app merely automates
a claim anyone could make by hand.

## 3 · What the app does and does not do

| | |
|---|---|
| Creates an embedded wallet, silently | **yes** — Noob mode |
| Connects an existing wallet | **yes** — Crypto mode |
| Reads "does this hold ≥1 $ACM?" | **yes** — the only chain question |
| Signs an ownership challenge | **yes** |
| Writes anything on-chain | **never** — no transfer verb exists |
| Buy / sell / swap / fiat on-ramp | **never** — exchange functions, 3.1.5(b)(iii) |
| Grants a token itself | **never** — the server decides |

`EmbeddedWallet` has `prove()` and no `signTransaction()`. That absence is a
decision. Adding one later must also be a decision, not a drift.

**Grant policy lives server-side.** The app only reports "this address holds
none". The policy can change after counsel answers without shipping a build.

## 4 · Grandma is the design target

No seed phrase. No second app to install. No staff member. No consent sheet.
If a user ever has to understand the wallet, the design has failed.

She taps GET STARTED. A key is generated on the device. She has an address. She
sees none of it, and that is not concealment — a feature hidden from App Review
is a 2.3.1 problem; not narrating your plumbing to a customer is just design.
Nobody explains TLS on a checkout screen.

**Rejected:** staff-assisted Phantom install. Nobody will do this, and a flow
that needs a human is not a flow.

## 5 · iCloud Keychain sync is on

Lose the phone, lose the key, lose the token. Sync fixes most of it — the
address survives a phone upgrade.

Two platform incompatibilities, both forced, both accepted:

- A synchronizable item **cannot** be `ThisDeviceOnly`. Uses
  `AfterFirstUnlock`, the strongest accessibility that still syncs.
- A synchronizable item **cannot** carry a biometric access control. The wallet
  is not Face ID gated. For a credential whose only power is "show me arcade
  tokens", recoverability beats a biometric prompt. For real money it would not.

Two implementation traps, both handled in `KeychainStore`:

- `kSecAttrSynchronizable` must appear in the **lookup**, not just the write.
  Omit it and synced items silently fail to match — presenting to the user as
  *"my wallet vanished after I restored my phone."*
- **Update in place, never delete-then-add.** A crash between the two destroys
  the only copy of the key and strands the token permanently.

**Why this matters more than buying more tokens:** replacement grants cannot be
purchased at scale. At 33% device churn the program needs ~116.7M tokens; the
pool holds 91.6M *total*. There is no price that supplies them. Churn is an
engineering problem, and sync is the fix.

## 6 · The arcade is the CAPTCHA

Free tokens invite farming. The answer is not SMS verification:

- It protects a benefit worth ~$120/yr with a gate that costs a farmer ~$0.05.
- It drags in phone numbers — TCPA, breach exposure, privacy labels, PII.
- It costs $1,700–$8,500 in messages at target volumes.

**A bot cannot walk into Eastgate Mall.** Give the token away with zero
friction and no PII; gate the *value* on physical presence at a reader. A farmed
token is worthless to someone who will not show up, and a real customer meets no
friction at all.

**Defer the mint.** Claiming is a free row in our database. The on-chain write
happens at **first real engagement**, not at claim — so bot claims cost nothing
and need no gate. This is also the largest cost saving available in the 99¢
model: ~$0.15 of Solana rent per wallet, never spent on a wallet that never
shows up.

## 7 · Redemption needs rotation *and* a burn

They stop different attacks and neither is sufficient alone.

- **Rotation (30s)** kills the screenshot texted to a friend.
- **The burn** kills the second use of a live code by the person standing there.

Verification is fully offline on both sides, from a secret delivered when the
offer was issued. ±1 step of clock skew is tolerated: with no network neither
device may have synced time recently, and refusing a real customer over two
seconds of drift is a worse failure than the attack it prevents.

**Acknowledged limit:** two offline readers can each accept the same offer. The
collision surfaces at sync, where the earliest burn stands and the rest become
reversals. With one reader per site it cannot happen. This is the deliberate
price of "the counter never stops."

## 8 · A dead zone is not a zero balance

An RPC failure or a 429 must never be read as "holds nothing". That mistake
would fire a duplicate grant every time she opened the app underground.
`LaunchSequence` returns `.offline` for both.

## 9 · Still open — for counsel, not for engineering

Securities counsel is still needed; Lori Krafte is IP only, get the referral.
Put these in the same opinion:

1. Is a token freely available to non-purchasers still consideration when
   auto-granted to purchasers?
2. Does a **paid app price** count the way IAP does under the crypto rules?
3. Does distributing a self-created token to users read as an offering under
   **3.1.5(b)(iv)**, which requires the issuer be an established financial
   institution?
4. Custody exposure if we hold claimable addresses on someone's behalf.

Never market upside. "Could be worth a lot" is Howey verbatim.

## 10 · Numbers of record

| | |
|---|---|
| $ACM mint | `4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump` |
| Supply (live, verified) | 999,957,146.033052 · 6 decimals |
| Pool | 91,578,851 ACM / $20,833 |
| Tokens to reach $0.01 | **77,766,399** for **$117,293** |
| 80M instead | $143,938, overshoots to $0.0142 |
| Locked | 500,000,000 (50.00%), Streamflow |
| Contribution per download | $0.8415 (99¢ less Apple 15%) |

Buying past ~85M is not viable: the last tokens price toward infinity.

## 11 · Environment

`ios/MTCKit` is UI-free and builds with **command line tools only** — no Xcode,
no simulator. `swift run mtckit-verify` runs 88 checks and exits non-zero on
failure. XCTest is deliberately not used because it ships inside Xcode.

**Blocker:** the dev Mac is Intel (i5-8500B, macOS 15.7.7) with no Xcode
installed. Verify current Xcode's hardware requirement before buying — plan on
needing Apple Silicon to submit.

**Enrollment:** Instar Brands LLC, D-U-N-S 118663873, **Organization** tier.
Todd performs enrollment; account creation and financial details are not
Claude's to enter.
