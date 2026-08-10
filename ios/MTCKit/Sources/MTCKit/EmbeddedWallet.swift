import Foundation
import CryptoKit

/// The invisible wallet behind "Get Started".
///
/// She taps one button. A key is generated on the device, an address exists, and
/// nothing in the interface ever says wallet, key, seed phrase, or crypto. There
/// is no setup screen, no 12 words to write down, no second app to install, and
/// no staff member involved. If the user ever has to understand this object, the
/// design has failed.
///
/// STORAGE NOTE: Solana signs with ed25519. The iOS Secure Enclave only holds
/// P-256 keys, so an ed25519 key CANNOT live inside it. The correct home is the
/// Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`, optionally
/// wrapped by a Secure-Enclave P-256 key for defence in depth. Storage is behind
/// a protocol here so the Keychain implementation is injected by the app and this
/// logic stays testable without entitlements.
public protocol KeyStore: AnyObject {
    func load(_ account: String) -> Data?
    func save(_ data: Data, account: String) throws
    func delete(_ account: String) throws
}

/// For tests and previews only. The app ships a Keychain-backed store.
public final class MemoryKeyStore: KeyStore {
    private var items: [String: Data] = [:]
    public init() {}
    public func load(_ account: String) -> Data? { items[account] }
    public func save(_ data: Data, account: String) throws { items[account] = data }
    public func delete(_ account: String) throws { items[account] = nil }
}

public struct EmbeddedWallet {

    public static let defaultAccount = "com.instarbrands.aladdinscastle.wallet"

    private let key: Curve25519.Signing.PrivateKey

    /// Base58 Solana address. This is the only part that ever leaves the device.
    public let address: String

    private init(key: Curve25519.Signing.PrivateKey) {
        self.key = key
        self.address = Base58.encode(key.publicKey.rawRepresentation)
    }

    /// Loads the existing wallet or creates one. Idempotent by design: calling it
    /// on every launch must never mint a second address, or a user would silently
    /// lose the token sitting in the first one.
    @discardableResult
    public static func loadOrCreate(in store: KeyStore,
                                    account: String = defaultAccount) throws -> EmbeddedWallet {
        if let raw = store.load(account),
           let existing = try? Curve25519.Signing.PrivateKey(rawRepresentation: raw) {
            return EmbeddedWallet(key: existing)
        }
        let fresh = Curve25519.Signing.PrivateKey()
        try store.save(fresh.rawRepresentation, account: account)
        return EmbeddedWallet(key: fresh)
    }

    public static func exists(in store: KeyStore, account: String = defaultAccount) -> Bool {
        store.load(account) != nil
    }

    /// Signs an ownership challenge. This is the ONLY signing verb on this type —
    /// there is deliberately no `signTransaction`, because the doctrine says
    /// nothing is ever written on-chain by the app. Adding one would be a
    /// decision, not an oversight.
    public func prove(_ challenge: Ownership.Challenge) throws -> String {
        Base58.encode(try key.signature(for: Data(challenge.message.utf8)))
    }

    /// A challenge already bound to this wallet's own address.
    public func challenge(at now: Date = Date()) -> Ownership.Challenge {
        Ownership.Challenge(wallet: address, at: now)
    }
}
