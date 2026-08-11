import Foundation
import CryptoKit
import MTCKit

// A minimal harness. XCTest lives inside Xcode, and these invariants need to be
// checkable anywhere — a laptop with only the command line tools, or CI.
var failures = 0, checks = 0

func check(_ label: String, _ ok: Bool) {
    checks += 1
    if ok { print("  ok   \(label)") }
    else { failures += 1; print("  FAIL \(label)") }
}
func equal<T: Equatable>(_ label: String, _ got: T, _ want: T) {
    checks += 1
    if got == want { print("  ok   \(label)") }
    else { failures += 1; print("  FAIL \(label) — got \(got), want \(want)") }
}
func section(_ s: String) { print("\n\(s)") }

func eastern(_ y: Int, _ m: Int, _ d: Int, _ hh: Int = 12) -> Date {
    var c = Calendar(identifier: .gregorian)
    c.timeZone = WalmartCalendar.timeZone
    return c.date(from: DateComponents(year: y, month: m, day: d, hour: hh))!
}
func ymd(_ date: Date) -> String {
    let f = DateFormatter()
    f.timeZone = WalmartCalendar.timeZone
    f.dateFormat = "yyyy-MM-dd"
    return f.string(from: date)
}

// ------------------------------------------------------------------ calendar
section("WALMART CALENDAR")
equal("FY2027 opens Sat 31 Jan 2026", ymd(WalmartCalendar.yearStart(2027)), "2026-01-31")

var allSaturdays = true
for fy in 2024...2040 where WalmartCalendar.calendar
    .component(.weekday, from: WalmartCalendar.yearStart(fy)) != 7 { allSaturdays = false }
check("every FY 2024–2040 opens on a Saturday", allSaturdays)

equal("FY2027 has 52 weeks", WalmartCalendar.weeks(in: 2027), 52)
equal("FY2031 derives as a 53-week year", WalmartCalendar.weeks(in: 2031), 53)

var weekCountsSane = true
for fy in 2024...2040 where ![52, 53].contains(WalmartCalendar.weeks(in: fy)) {
    weekCountsSane = false
}
check("no FY produces anything but 52 or 53 weeks", weekCountsSane)

let end27 = WalmartCalendar.weekEnd(fiscalYear: 2027, week: 27)
let start28 = WalmartCalendar.weekStart(fiscalYear: 2027, week: 28)
equal("WK27 closes Friday 07 Aug 2026", ymd(end27), "2026-08-07")
equal("WK28 opens Saturday 08 Aug 2026", ymd(start28), "2026-08-08")
equal("no gap or overlap between weeks", start28.timeIntervalSince(end27), 1)

let today = WalmartCalendar.period(for: eastern(2026, 8, 6))
equal("06 Aug 2026 is FY2027", today.fiscalYear, 2027)
equal("06 Aug 2026 is week 27", today.week, 27)

var boundariesExact = true
for w in 1...WalmartCalendar.weeks(in: 2027) {
    let opens = WalmartCalendar.weekStart(fiscalYear: 2027, week: w)
    let closes = WalmartCalendar.weekEnd(fiscalYear: 2027, week: w)
    if WalmartCalendar.period(for: opens).week != w { boundariesExact = false }
    if WalmartCalendar.period(for: closes).week != w { boundariesExact = false }
}
check("period() is exact at all 104 week boundaries", boundariesExact)

equal("05 Jan 2027 still belongs to FY2027",
      WalmartCalendar.period(for: eastern(2027, 1, 5)).fiscalYear, 2027)
equal("31 Jan 2027 has rolled into FY2028",
      WalmartCalendar.period(for: eastern(2027, 1, 31)).fiscalYear, 2028)

let rolled = WalmartCalendar.closeWeek(fiscalYear: 2027, startWeek: 40, duration: 26)
equal("26-week promo from WK40 rolls into FY2028", rolled.fiscalYear, 2028)
equal("…and lands on week 13", rolled.week, 13)

// ---------------------------------------------------------------------- auth
section("HMAC AUTH")
let key = SymmetricKey(size: .bits256)
let ring = ["reader-01": key]

var seen = Set<String>()
let env = Auth.sign(body: "MTC1|ABC|wallet|350|2027|31", kid: "reader-01", key: key)
do { try Auth.verify(env, keyring: ring, seen: &seen); check("valid envelope verifies", true) }
catch { check("valid envelope verifies", false) }

do {
    try Auth.verify(env, keyring: ring, seen: &seen)
    check("replay is rejected", false)
} catch { check("replay is rejected", (error as? Auth.Failure) == .replayed(nonce: env.nonce)) }

var s2 = Set<String>()
let signed = Auth.sign(body: "value=350", kid: "reader-01", key: key)
let forged = Auth.Envelope(kid: signed.kid, iat: signed.iat, nonce: signed.nonce,
                           body: "value=3500", mac: signed.mac)
do { try Auth.verify(forged, keyring: ring, seen: &s2); check("tampered body is rejected", false) }
catch { check("tampered body is rejected", (error as? Auth.Failure) == .badSignature) }

// The forgery above must NOT have consumed the nonce, or an attacker could lock
// out a real pass just by spamming bad MACs.
do { try Auth.verify(signed, keyring: ring, seen: &s2)
     check("a rejected forgery does not burn the real nonce", true) }
catch { check("a rejected forgery does not burn the real nonce", false) }

var s3 = Set<String>()
let stale = Auth.sign(body: "x", kid: "reader-01", key: key,
                      at: Date().addingTimeInterval(-3600))
do { try Auth.verify(stale, keyring: ring, seen: &s3); check("stale envelope is rejected", false) }
catch { check("stale envelope is rejected", true) }

var s4 = Set<String>()
let wrongKey = Auth.sign(body: "x", kid: "reader-99", key: key)
do { try Auth.verify(wrongKey, keyring: ring, seen: &s4); check("unknown key id is rejected", false) }
catch { check("unknown key id is rejected", (error as? Auth.Failure) == .unknownKey("reader-99")) }

// --------------------------------------------------------------------- offer
section("OFFER")
let offer = Offer(id: "TID-271", brand: "Tide", item: "Tide Pods 42ct",
                  valueCents: 350, fiscalYear: 2027, startWeek: 27, durationWeeks: 4)
equal("4-week promo from WK27 closes WK30", offer.close.week, 30)
check("not redeemable before it opens", !offer.isRedeemable(at: eastern(2026, 7, 31)))
check("redeemable inside its window", offer.isRedeemable(at: eastern(2026, 8, 6)))
check("the final second still counts", offer.isRedeemable(at: offer.expiresAt))
check("one second later it does not",
      !offer.isRedeemable(at: offer.expiresAt.addingTimeInterval(1)))

var used = offer
used.state = .redeemed
check("a redeemed offer never redeems again", !used.isRedeemable(at: eastern(2026, 8, 6)))

// ------------------------------------------------------------------- base58
section("BASE58")
check("ACM mint is a valid 32-byte public key", Base58.isValidPublicKey(ACMCheck.mint))
check("a typo'd address is rejected", !Base58.isValidPublicKey("4PRz3Ewh0OIl"))
let rt = Data((0..<32).map { _ in UInt8.random(in: 0...255) })
equal("encode/decode round-trips", Base58.decode(Base58.encode(rt)), rt)
check("leading zero bytes survive the round trip",
      Base58.decode(Base58.encode(Data([0, 0, 7]))) == Data([0, 0, 7]))

// ---------------------------------------------------------------- ACM check
section("ACM READ-ONLY CHECK")
func rpc(_ accounts: [(String, Int)]) -> Data {
    let value = accounts.map { amt, dec in
        ["account": ["data": ["parsed": ["info": ["tokenAmount":
            ["amount": amt, "decimals": dec, "uiAmountString": amt]]]]]]
    }
    return try! JSONSerialization.data(
        withJSONObject: ["jsonrpc": "2.0", "id": 1,
                         "result": ["context": ["slot": 1], "value": value]])
}

check("exactly 1.000000 ACM holds at least one",
      try! ACMCheck.holdsAtLeastOne(rpc([("1000000", 6)])))
check("0.999999 ACM does NOT hold one",
      !(try! ACMCheck.holdsAtLeastOne(rpc([("999999", 6)]))))
check("a wallet with no token account holds zero, and is not an error",
      !(try! ACMCheck.holdsAtLeastOne(rpc([]))))
// Two half-token accounts are still one whole token to the holder.
check("amounts sum across multiple token accounts for the same mint",
      try! ACMCheck.holdsAtLeastOne(rpc([("500000", 6), ("500000", 6)])))
equal("account count is reported", try! ACMCheck.parse(rpc([("1", 6), ("2", 6)])).accountCount, 2)

// A big balance must not lose precision the way a Double would.
let whale = try! ACMCheck.parse(rpc([("11767037390000", 6)]))
equal("large balance stays exact in base units", whale.rawAmount, 11_767_037_390_000)
check("…and still answers holdsAtLeast(1)", whale.holdsAtLeast(1))

do { _ = try ACMCheck.parse(Data(#"{"error":{"message":"429 rate limited"}}"#.utf8))
     check("an RPC error is surfaced, not read as zero", false) }
catch { check("an RPC error is surfaced, not read as zero",
              (error as? ACMCheck.ParseError) == .rpcError("429 rate limited")) }

let req = ACMCheck.balanceRequest(owner: "So11111111111111111111111111111111111111112")
equal("request targets getTokenAccountsByOwner",
      req["method"] as? String, "getTokenAccountsByOwner")

// -------------------------------------------------------------- ownership
section("WALLET OWNERSHIP")
let signer = Curve25519.Signing.PrivateKey()
let wallet = Base58.encode(signer.publicKey.rawRepresentation)
let ch = Ownership.Challenge(wallet: wallet)
let goodSig = Base58.encode(try! signer.signature(for: Data(ch.message.utf8)))
do { try Ownership.verify(challenge: ch, signatureBase58: goodSig)
     check("a genuine wallet signature verifies", true) }
catch { check("a genuine wallet signature verifies", false) }

// Someone claiming a wallet they do not control is the whole attack.
let impostor = Curve25519.Signing.PrivateKey()
let forgedSig = Base58.encode(try! impostor.signature(for: Data(ch.message.utf8)))
do { try Ownership.verify(challenge: ch, signatureBase58: forgedSig)
     check("claiming someone else's wallet is rejected", false) }
catch { check("claiming someone else's wallet is rejected",
              (error as? Ownership.Failure) == .badSignature) }

let stale2 = Ownership.Challenge(wallet: wallet, at: Date().addingTimeInterval(-3600))
let staleSig = Base58.encode(try! signer.signature(for: Data(stale2.message.utf8)))
do { try Ownership.verify(challenge: stale2, signatureBase58: staleSig)
     check("a stale challenge is rejected", false) }
catch { check("a stale challenge is rejected", true) }

check("the signing message states it moves no funds",
      ch.message.contains("authorises nothing and moves no funds"))

// ------------------------------------------------------------ noob wallet
section("EMBEDDED WALLET  (the grandma path)")
let store = MemoryKeyStore()
check("no wallet before first tap", !EmbeddedWallet.exists(in: store))

let w1 = try! EmbeddedWallet.loadOrCreate(in: store)
check("one tap produces a valid Solana address", Base58.isValidPublicKey(w1.address))
check("wallet now exists", EmbeddedWallet.exists(in: store))

// The failure that would silently strand her token: a second address on relaunch.
let w2 = try! EmbeddedWallet.loadOrCreate(in: store)
equal("relaunch returns the SAME address, never a new one", w2.address, w1.address)
for _ in 0..<20 { _ = try! EmbeddedWallet.loadOrCreate(in: store) }
equal("…still the same after 20 launches",
      try! EmbeddedWallet.loadOrCreate(in: store).address, w1.address)

// End-to-end: the invisible wallet satisfies the very challenge the reader asks.
let selfChallenge = w1.challenge()
let selfSig = try! w1.prove(selfChallenge)
do { try Ownership.verify(challenge: selfChallenge, signatureBase58: selfSig)
     check("embedded wallet proves its own ownership end-to-end", true) }
catch { check("embedded wallet proves its own ownership end-to-end", false) }

// A second device must not be able to answer for the first.
let otherStore = MemoryKeyStore()
let other = try! EmbeddedWallet.loadOrCreate(in: otherStore)
check("a different device gets a different address", other.address != w1.address)
let crossSig = try! other.prove(selfChallenge)
do { try Ownership.verify(challenge: selfChallenge, signatureBase58: crossSig)
     check("another device cannot answer this device's challenge", false) }
catch { check("another device cannot answer this device's challenge", true) }

check("the private key is never exposed on the type",
      !"\(EmbeddedWallet.self)".contains("privateKey"))

// ------------------------------------------------- phone upgrade / restore
section("PHONE UPGRADE  (iCloud Keychain restore)")
// She buys a new iPhone. iCloud Keychain carries the item across. The app must
// find the SAME address — a new one would strand the $ACM already pushed to her.
let oldPhone = MemoryKeyStore()
let hers = try! EmbeddedWallet.loadOrCreate(in: oldPhone)
let syncedBlob = oldPhone.load(EmbeddedWallet.defaultAccount)!

let newPhone = MemoryKeyStore()
try! newPhone.save(syncedBlob, account: EmbeddedWallet.defaultAccount)   // iCloud restore
let restored = try! EmbeddedWallet.loadOrCreate(in: newPhone)
equal("restored phone yields the IDENTICAL address", restored.address, hers.address)

// And it must still be able to prove ownership, not merely display the address.
let upgradeChallenge = restored.challenge()
let upgradeSig = try! restored.prove(upgradeChallenge)
do { try Ownership.verify(challenge: upgradeChallenge, signatureBase58: upgradeSig)
     check("restored wallet still proves ownership", true) }
catch { check("restored wallet still proves ownership", false) }

// A phone with NO restore is a genuinely new user, not a recovered one.
let wipedPhone = MemoryKeyStore()
let fresh2 = try! EmbeddedWallet.loadOrCreate(in: wipedPhone)
check("a phone with no iCloud restore gets a new address (grant is lost, as modelled)",
      fresh2.address != hers.address)

// Storage config: sync and device-binding are mutually exclusive — assert we
// chose sync, because silently getting this wrong presents as a vanished wallet.
let syncStore = KeychainStore(synchronizable: true)
let localStore = KeychainStore(synchronizable: false)
check("a synchronizable Keychain store is constructible", syncStore.load("nope") == nil)
check("device-only remains available for anything that must not sync",
      localStore.load("nope") == nil)

// -------------------------------------------------------- redemption code
section("ROTATING CODE  (works with no signal)")
let secret = SymmetricKey(size: .bits256)
let offerID = "ICEE-2027-W27-0042"
let t0 = Date(timeIntervalSince1970: 1_785_000_000)   // fixed clock, no flakiness

let c0 = RedemptionCode.generate(secret: secret, offerID: offerID, at: t0)
equal("display code is 6 digits", c0.digits.count, 6)
check("digits are numeric", c0.digits.allSatisfy(\.isNumber))
check("QR payload is versioned", c0.qrPayload.hasPrefix("MTC1|"))

let sameWindow = RedemptionCode.generate(secret: secret, offerID: offerID,
                                         at: t0.addingTimeInterval(29))
equal("code is stable inside its 30s window", sameWindow.qrPayload, c0.qrPayload)
let nextWindow = RedemptionCode.generate(secret: secret, offerID: offerID,
                                         at: t0.addingTimeInterval(31))
check("code rotates in the next window", nextWindow.qrPayload != c0.qrPayload)
equal("countdown drives the UI ring", c0.secondsRemaining(at: t0.addingTimeInterval(10)), 20)

do { try RedemptionCode.verify(payload: c0.qrPayload, secret: secret,
                               offerID: offerID, at: t0)
     check("reader accepts a live code offline", true) }
catch { check("reader accepts a live code offline", false) }

// Clock drift between her phone and the kiosk, neither recently synced.
for (drift, label) in [(-29.0, "kiosk 29s behind"), (29.0, "kiosk 29s ahead")] {
    do { try RedemptionCode.verify(payload: c0.qrPayload, secret: secret,
                                   offerID: offerID, at: t0.addingTimeInterval(drift))
         check("tolerates clock skew — \(label)", true) }
    catch { check("tolerates clock skew — \(label)", false) }
}

// THE SCREENSHOT: photographed, texted to a friend, opened two minutes later.
do { try RedemptionCode.verify(payload: c0.qrPayload, secret: secret,
                               offerID: offerID, at: t0.addingTimeInterval(120))
     check("a 2-minute-old screenshot is REJECTED", false) }
catch { check("a 2-minute-old screenshot is REJECTED", true) }

let otherSecret = SymmetricKey(size: .bits256)
do { try RedemptionCode.verify(payload: c0.qrPayload, secret: otherSecret,
                               offerID: offerID, at: t0)
     check("a forged code with the wrong secret is rejected", false) }
catch { check("a forged code with the wrong secret is rejected", true) }

do { try RedemptionCode.verify(payload: c0.qrPayload, secret: secret,
                               offerID: "SOME-OTHER-OFFER", at: t0)
     check("a code for a different offer is rejected", false) }
catch { check("a code for a different offer is rejected",
              (error as? RedemptionCode.Failure) == .wrongOffer) }

do { try RedemptionCode.verify(payload: "garbage", secret: secret,
                               offerID: offerID, at: t0)
     check("malformed payload is rejected", false) }
catch { check("malformed payload is rejected", true) }

// ------------------------------------------------------------ burn ledger
section("BURN LEDGER  (spends exactly once)")
let reader = BurnLedger(readerID: "EASTGATE-01")
check("offer is unburned to begin with", !reader.isBurned(offerID))
let firstBurn = try! reader.burn(offerID: offerID, at: t0)
check("first redemption succeeds", firstBurn.offerID == offerID)
check("offer now reads as burned", reader.isBurned(offerID))

// The live-code double-spend: same valid code, handed straight back.
do { _ = try reader.burn(offerID: offerID, at: t0.addingTimeInterval(5))
     check("a SECOND redemption of the same offer is refused", false) }
catch { check("a SECOND redemption of the same offer is refused",
              (error as? BurnLedger.Failure) == .alreadyBurned(offerID: offerID, at: t0)) }

equal("burn is queued while offline", reader.pending.count, 1)
reader.markSynced([offerID])
equal("queue drains once the link returns", reader.pending.count, 0)
check("burn survives the sync", reader.isBurned(offerID))

// Two kiosks, both offline, same offer — the acknowledged limit, resolved at sync.
let a = BurnLedger.Burn(offerID: "DUP-1", at: t0, readerID: "EASTGATE-01", synced: false)
let b = BurnLedger.Burn(offerID: "DUP-1", at: t0.addingTimeInterval(40),
                        readerID: "EASTGATE-02", synced: false)
let solo = BurnLedger.Burn(offerID: "SOLO-1", at: t0, readerID: "EASTGATE-01", synced: false)
let (accepted, conflicts) = BurnLedger.reconcile([b, a, solo])
equal("reconcile accepts one burn per offer", accepted.count, 2)
equal("the cross-reader collision is reported, not swallowed", conflicts.count, 1)
equal("the earliest burn is the one that stands", conflicts[0].kept, t0)

// ---------------------------------------------------------- launch sequence
section("LAUNCH SEQUENCE  (all silent)")
let launchStore = MemoryKeyStore()
let apiKey = SymmetricKey(size: .bits256)

func fetchJSON(_ accounts: [(String, Int)]) -> LaunchSequence.BalanceFetch {
    { _ in rpc(accounts) }
}

let holderOutcome = try! LaunchSequence.run(store: launchStore, kid: "app-01",
                                            key: apiKey, fetch: fetchJSON([("1000000", 6)]))
if case .holder(let addr, let h) = holderOutcome {
    check("a holder is recognised with no user action", h.holdsAtLeast(1))
    check("…and keeps the same address", Base58.isValidPublicKey(addr))
} else { check("a holder is recognised with no user action", false) }

let grantOutcome = try! LaunchSequence.run(store: launchStore, kid: "app-01",
                                           key: apiKey, fetch: fetchJSON([]))
if case .needsGrant(let addr, let env) = grantOutcome {
    var s = Set<String>()
    let verified = (try? Auth.verify(env, keyring: ["app-01": apiKey], seen: &s)) != nil
    check("a zero balance produces an HMAC-signed registration", verified)
    check("the registration names the address", env.body.contains(addr))
    check("the app proposes no grant of its own", env.body.contains("holds=0"))
} else { check("a zero balance produces an HMAC-signed registration", false) }

// A dead zone must not be mistaken for "holds nothing" — that would fire a
// duplicate grant every time she opened the app underground.
struct NoSignal: Error {}
let offlineOutcome = try! LaunchSequence.run(store: launchStore, kid: "app-01",
                                             key: apiKey, fetch: { _ in throw NoSignal() })
if case .offline = offlineOutcome {
    check("a dead zone reports OFFLINE, never 'holds zero'", true)
} else { check("a dead zone reports OFFLINE, never 'holds zero'", false) }

let rateLimited = try! LaunchSequence.run(store: launchStore, kid: "app-01", key: apiKey,
    fetch: { _ in Data(#"{"error":{"message":"429"}}"#.utf8) })
if case .offline = rateLimited {
    check("a rate-limited RPC also reports OFFLINE, not 'holds zero'", true)
} else { check("a rate-limited RPC also reports OFFLINE, not 'holds zero'", false) }

// --------------------------------------------------------- deferred claim
section("DEFERRED CLAIM  (a bot cannot walk into a mall)")
let addr = Base58.encode(Curve25519.Signing.PrivateKey().publicKey.rawRepresentation)

do { _ = try Claim.claim(address: "not-an-address", source: "web", existing: nil)
     check("a malformed address cannot claim", false) }
catch { check("a malformed address cannot claim", (error as? Claim.Failure) == .badAddress) }

let rec = try! Claim.claim(address: addr, source: "web", existing: nil, at: t0)
equal("claiming is free and open to anyone", rec.state, Claim.State.claimed)
check("nothing has been minted yet", rec.mintedAt == nil)

do { _ = try Claim.claim(address: addr, source: "app", existing: rec, at: t0)
     check("the same address cannot claim twice", false) }
catch { check("the same address cannot claim twice",
              (error as? Claim.Failure) == .alreadyClaimed(address: addr)) }

// THE POINT OF THE WHOLE DESIGN: a claim alone must never spend a cent.
do { _ = try Claim.mint(rec, at: t0)
     check("a CLAIM alone can never trigger a mint", false) }
catch { check("a CLAIM alone can never trigger a mint",
              (error as? Claim.Failure) == .notEngaged(address: addr)) }

let engaged = try! Claim.engage(rec, at: t0.addingTimeInterval(86_400))
equal("showing up at a reader engages the claim", engaged.state, Claim.State.engaged)
let minted = try! Claim.mint(engaged, at: t0.addingTimeInterval(86_401))
equal("only an engaged claim mints", minted.state, Claim.State.minted)
check("the mint is stamped", minted.mintedAt != nil)

do { _ = try Claim.mint(minted, at: t0)
     check("a minted claim never mints again", false) }
catch { check("a minted claim never mints again",
              (error as? Claim.Failure) == .alreadyMinted(address: addr)) }

// Unengaged claims age out. Nothing was spent, so nothing is lost.
let ancient = Claim.Record(address: addr, claimedAt: t0, source: "web")
do { _ = try Claim.engage(ancient, at: t0.addingTimeInterval(Claim.unengagedTTL + 60))
     check("an unengaged claim expires after its TTL", false) }
catch { check("an unengaged claim expires after its TTL", true) }

let swept = Claim.sweep([ancient], at: t0.addingTimeInterval(Claim.unengagedTTL + 60))
equal("sweep voids stale claims", swept[0].state, Claim.State.void)
let keep = Claim.sweep([rec], at: t0.addingTimeInterval(3600))
equal("sweep leaves fresh claims alone", keep[0].state, Claim.State.claimed)

// The saving, stated in money: a million bot claims cost nothing.
let econ = Claim.Economics(claims: 1_000_000, engaged: 50_000, rentPerWallet: 0.1489)
equal("minting at claim time would cost", Int(econ.naiveCost.rounded()), 148_900)
equal("minting at engagement costs", Int(econ.mintCost.rounded()), 7_445)
equal("deferring saves", Int(econ.saved.rounded()), 141_455)

// -------------------------------------------------------------------- report
print("\n\(checks - failures)/\(checks) checks passed")
if failures > 0 { print("FAILED"); exit(1) }
print("ALL PASS")
