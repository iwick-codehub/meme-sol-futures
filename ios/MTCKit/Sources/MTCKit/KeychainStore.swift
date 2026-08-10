import Foundation
import Security

/// Keychain-backed key storage with iCloud Keychain sync enabled, so the wallet
/// survives a phone upgrade.
///
/// The user buys a new iPhone, restores it, opens the app, and her address is the
/// same one her $ACM was pushed to. No support call, no replacement grant, no
/// stranded token. That is the whole reason this class exists: replacement grants
/// cannot be bought at scale — the pool physically cannot supply them — so the
/// only workable answer is not losing the key in the first place.
///
/// TWO INCOMPATIBILITIES, both deliberate and both forced by the platform:
///
/// 1. A synchronizable item CANNOT be `...ThisDeviceOnly`. Sync and device-binding
///    are mutually exclusive by definition. `AfterFirstUnlock` is the strongest
///    accessibility that still syncs, and it lets a background refresh read the
///    key after a reboot before the user has unlocked.
///
/// 2. A synchronizable item CANNOT carry a biometric `SecAccessControl`. Face ID
///    gating and iCloud sync do not combine. For a credential whose only power is
///    "show me arcade tokens", recoverability is worth more than a biometric
///    prompt. For a wallet holding real money the trade would go the other way.
public final class KeychainStore: KeyStore {

    public enum Failure: Error, Equatable {
        case status(OSStatus)
    }

    private let service: String
    private let synchronizable: Bool

    public init(service: String = "com.instarbrands.aladdinscastle",
                synchronizable: Bool = true) {
        self.service = service
        self.synchronizable = synchronizable
    }

    /// Base query. `kSecAttrSynchronizable` MUST appear on lookups as well as
    /// writes — a query that omits it silently fails to match synced items, which
    /// presents as "the wallet vanished after restore".
    private func query(_ account: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrSynchronizable as String: synchronizable
                ? kCFBooleanTrue! : kCFBooleanFalse!,
        ]
    }

    public func load(_ account: String) -> Data? {
        var q = query(account)
        q[kSecReturnData as String] = kCFBooleanTrue!
        q[kSecMatchLimit as String] = kSecMatchLimitOne
        var out: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess else { return nil }
        return out as? Data
    }

    public func save(_ data: Data, account: String) throws {
        var add = query(account)
        add[kSecValueData as String] = data
        // Sync forces AfterFirstUnlock; ThisDeviceOnly would silently disable sync.
        add[kSecAttrAccessible as String] = synchronizable
            ? kSecAttrAccessibleAfterFirstUnlock
            : kSecAttrAccessibleWhenUnlockedThisDeviceOnly

        let status = SecItemAdd(add as CFDictionary, nil)
        if status == errSecDuplicateItem {
            // Never delete-then-add: a crash between the two would destroy the only
            // copy of the key. Update in place instead.
            let update = SecItemUpdate(query(account) as CFDictionary,
                                       [kSecValueData as String: data] as CFDictionary)
            guard update == errSecSuccess else { throw Failure.status(update) }
            return
        }
        guard status == errSecSuccess else { throw Failure.status(status) }
    }

    public func delete(_ account: String) throws {
        let status = SecItemDelete(query(account) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw Failure.status(status)
        }
    }
}
