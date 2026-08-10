import Foundation
import CryptoKit

/// The code she shows at the counter.
///
/// Generated entirely on the phone from a secret delivered when the offer was
/// issued, so it works with **zero signal** — malls are cellular dead zones and
/// connectivity is an optimisation, never a dependency. The reader verifies it
/// offline too, from the same secret, with no round trip to anything.
///
/// Two separate defences, and they stop different attacks:
///
/// - **Rotation** kills the screenshot. A photo texted to a friend is worthless
///   in 30 seconds. It does NOT stop the person standing there from using it.
/// - **The burn** (see `BurnLedger`) kills the second use. Even a live, valid
///   code spends exactly once.
///
/// Rotation alone is not enough, and a burn alone is not enough. You need both.
public enum RedemptionCode {

    /// 30 seconds — long enough that a slow cashier does not fail a valid code,
    /// short enough that a shared screenshot is dead before it is opened.
    public static let stepSeconds: TimeInterval = 30

    public struct Code: Equatable, Sendable {
        public let digits: String      // 6-digit human fallback, if a scanner dies
        public let qrPayload: String   // what the scanner actually reads
        public let counter: UInt64
        public let expiresAt: Date

        /// Drives the "code refreshes in 0:30" ring without a second clock.
        public func secondsRemaining(at now: Date = Date()) -> Int {
            max(0, Int(expiresAt.timeIntervalSince(now).rounded(.up)))
        }
    }

    static func counter(at date: Date) -> UInt64 {
        UInt64(max(0, date.timeIntervalSince1970 / stepSeconds))
    }

    /// HOTP-style dynamic truncation over HMAC-SHA256.
    static func mac(secret: SymmetricKey, offerID: String, counter: UInt64) -> Data {
        var be = counter.bigEndian
        var msg = Data(offerID.utf8)
        msg.append(0x1F)                     // separator cannot occur in an offer id
        withUnsafeBytes(of: &be) { msg.append(contentsOf: $0) }
        return Data(HMAC<SHA256>.authenticationCode(for: msg, using: secret))
    }

    static func truncate(_ digest: Data) -> UInt32 {
        let offset = Int(digest[digest.count - 1] & 0x0f)
        let slice = digest[offset..<(offset + 4)]
        let n = slice.reduce(UInt32(0)) { ($0 << 8) | UInt32($1) }
        return n & 0x7fff_ffff              // strip the sign bit, per RFC 4226
    }

    public static func generate(secret: SymmetricKey, offerID: String,
                                at now: Date = Date()) -> Code {
        let c = counter(at: now)
        let digest = mac(secret: secret, offerID: offerID, counter: c)
        let digits = String(format: "%06u", truncate(digest) % 1_000_000)
        // The QR carries a 16-hex-char tag: far too wide to guess, still a small
        // enough payload for a low QR version that scans off a scratched screen.
        let tag = digest.prefix(8).map { String(format: "%02x", $0) }.joined()
        let expires = Date(timeIntervalSince1970: Double(c + 1) * stepSeconds)
        return Code(digits: digits,
                    qrPayload: "MTC1|\(offerID)|\(c)|\(tag)",
                    counter: c, expiresAt: expires)
    }

    public enum Failure: Error, Equatable {
        case malformed
        case wrongOffer
        case outsideWindow(driftSteps: Int)
        case badCode
    }

    /// Reader-side verification, fully offline.
    ///
    /// `skewSteps` tolerates clock drift between her phone and the kiosk — with no
    /// network neither device may have synced time in a while, and refusing a
    /// legitimate customer over two seconds of drift is a worse failure than the
    /// attack it would prevent. One step each way is the RFC 6238 convention.
    public static func verify(payload: String, secret: SymmetricKey, offerID: String,
                              at now: Date = Date(), skewSteps: Int = 1) throws {
        let parts = payload.split(separator: "|", omittingEmptySubsequences: false)
        guard parts.count == 4, parts[0] == "MTC1",
              let claimed = UInt64(parts[2]) else { throw Failure.malformed }
        guard String(parts[1]) == offerID else { throw Failure.wrongOffer }

        let nowCounter = counter(at: now)
        let drift = Int(claimed) - Int(nowCounter)
        guard abs(drift) <= skewSteps else { throw Failure.outsideWindow(driftSteps: drift) }

        let expected = mac(secret: secret, offerID: offerID, counter: claimed)
            .prefix(8).map { String(format: "%02x", $0) }.joined()
        // Constant-time: a byte-at-a-time early exit leaks the tag one nibble per
        // attempt to anyone who can time the reader.
        let got = Data(String(parts[3]).utf8), want = Data(expected.utf8)
        guard got.count == want.count,
              HMAC<SHA256>.isValidAuthenticationCode(
                Data(HMAC<SHA256>.authenticationCode(for: want, using: secret)),
                authenticating: got, using: secret) else { throw Failure.badCode }
    }
}
