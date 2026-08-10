import Foundation
import CryptoKit

/// Proves the phone's wallet actually belongs to this user, without the app ever
/// touching a private key.
///
/// The wallet app signs a challenge we generated; we verify the ed25519 signature
/// against the claimed public key. A balance check alone is not proof of ownership
/// — anyone can type in someone else's address — so the signature is what stops a
/// person claiming a whale's wallet to collect arcade credits.
public enum Ownership {

    public struct Challenge: Equatable, Sendable {
        public let nonce: String
        public let issuedAt: Int
        public let wallet: String

        /// Human-readable on purpose: this string appears in the wallet's signing
        /// sheet, and a user should be able to read exactly what they are agreeing
        /// to. It also names the app, so a signature harvested here cannot be
        /// replayed against some other service's challenge.
        public var message: String {
            """
            Aladdin's Castle — prove wallet ownership
            wallet: \(wallet)
            nonce: \(nonce)
            issued: \(issuedAt)
            This signature authorises nothing and moves no funds.
            """
        }

        public init(wallet: String, nonce: String = UUID().uuidString,
                    at now: Date = Date()) {
            self.wallet = wallet
            self.nonce = nonce
            self.issuedAt = Int(now.timeIntervalSince1970)
        }
    }

    public enum Failure: Error, Equatable {
        case badAddress
        case badSignature
        case expired(ageSeconds: Int)
    }

    /// Verifies an ed25519 signature over `challenge.message`.
    public static func verify(challenge: Challenge,
                              signatureBase58: String,
                              maxAge: TimeInterval = 300,
                              at now: Date = Date()) throws {
        guard let keyBytes = Base58.decode(challenge.wallet), keyBytes.count == 32,
              let key = try? Curve25519.Signing.PublicKey(rawRepresentation: keyBytes) else {
            throw Failure.badAddress
        }
        guard let sig = Base58.decode(signatureBase58), sig.count == 64 else {
            throw Failure.badSignature
        }
        // Freshness first would leak nothing, but check the signature too — both
        // must hold, and neither short-circuits the other.
        let valid = key.isValidSignature(sig, for: Data(challenge.message.utf8))
        let age = Int(now.timeIntervalSince1970) - challenge.issuedAt
        guard valid else { throw Failure.badSignature }
        guard age <= Int(maxAge), age >= -60 else { throw Failure.expired(ageSeconds: age) }
    }
}
