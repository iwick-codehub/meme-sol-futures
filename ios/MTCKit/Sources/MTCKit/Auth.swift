import Foundation
import CryptoKit

/// HMAC-SHA256 over every channel: QR payloads, reader calls, webhooks, internal
/// requests. There is no unauthenticated path, and no caller is trusted to
/// remember the hard parts — the nonce and issued-at are injected inside `sign`
/// so a call site physically cannot omit them.
public enum Auth {

    public struct Envelope: Codable, Equatable, Sendable {
        public let kid: String     // key id, so keys can rotate without a flag day
        public let iat: Int        // issued at, epoch seconds
        public let nonce: String   // single-use, defeats replay
        public let body: String
        public let mac: String

        public init(kid: String, iat: Int, nonce: String, body: String, mac: String) {
            self.kid = kid; self.iat = iat; self.nonce = nonce
            self.body = body; self.mac = mac
        }
    }

    public enum Failure: Error, Equatable {
        case unknownKey(String)
        case badSignature
        case expired(ageSeconds: Int)
        case replayed(nonce: String)
    }

    /// Canonical form. Field order is fixed and separators cannot appear in the
    /// fields, so two different envelopes can never produce the same string.
    static func canonical(kid: String, iat: Int, nonce: String, body: String) -> Data {
        Data("\(kid)\u{1F}\(iat)\u{1F}\(nonce)\u{1F}\(body)".utf8)
    }

    public static func sign(body: String, kid: String, key: SymmetricKey,
                            at now: Date = Date()) -> Envelope {
        let iat = Int(now.timeIntervalSince1970)
        let nonce = UUID().uuidString
        let mac = HMAC<SHA256>.authenticationCode(
            for: canonical(kid: kid, iat: iat, nonce: nonce, body: body), using: key)
        return Envelope(kid: kid, iat: iat, nonce: nonce, body: body,
                        mac: Data(mac).base64EncodedString())
    }

    /// Verifies signature, freshness and single-use in that order.
    ///
    /// `seen` carries the nonces already accepted; a reader that has been offline
    /// still refuses a replayed pass because the check is local, not a round trip.
    public static func verify(_ env: Envelope,
                              keyring: [String: SymmetricKey],
                              seen: inout Set<String>,
                              maxAge: TimeInterval = 300,
                              at now: Date = Date()) throws {
        guard let key = keyring[env.kid] else { throw Failure.unknownKey(env.kid) }
        guard let mac = Data(base64Encoded: env.mac) else { throw Failure.badSignature }

        // CryptoKit's comparison is constant-time. Never use == on a MAC.
        let ok = HMAC<SHA256>.isValidAuthenticationCode(
            mac,
            authenticating: canonical(kid: env.kid, iat: env.iat,
                                      nonce: env.nonce, body: env.body),
            using: key)
        guard ok else { throw Failure.badSignature }

        let age = Int(now.timeIntervalSince1970) - env.iat
        guard age <= Int(maxAge), age >= -60 else { throw Failure.expired(ageSeconds: age) }

        // Only record the nonce once everything else passed, or a forged envelope
        // could burn a legitimate nonce and lock the real pass out.
        guard !seen.contains(env.nonce) else { throw Failure.replayed(nonce: env.nonce) }
        seen.insert(env.nonce)
    }
}
