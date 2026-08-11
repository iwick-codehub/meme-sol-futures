import SwiftUI
import CryptoKit
import MTCKit

/// The one object the views read. Everything it does on launch is silent —
/// no wallet setup screen, no consent sheet, no spinner explaining tokens.
@MainActor
public final class AppState: ObservableObject {

    public enum Membership: Equatable {
        case unknown
        case member(address: String)      // holds ≥1 $ACM
        case pending(address: String)     // registered, waiting on a grant
        case offline(address: String)     // dead zone — NOT "holds none"
    }

    @Published public private(set) var membership: Membership = .unknown
    @Published public private(set) var offers: [Offer] = []
    @Published public private(set) var period: (fiscalYear: Int, week: Int) =
        WalmartCalendar.period()
    @Published public var showingRedeem: Offer?

    private let store: KeyStore
    private let apiKey: SymmetricKey
    private let kid: String
    private let fetch: LaunchSequence.BalanceFetch

    public init(store: KeyStore,
                kid: String = "app-01",
                apiKey: SymmetricKey = SymmetricKey(size: .bits256),
                fetch: @escaping LaunchSequence.BalanceFetch) {
        self.store = store; self.kid = kid; self.apiKey = apiKey; self.fetch = fetch
    }

    /// Runs on every launch. Idempotent — it must never mint a second address.
    public func start(at now: Date = Date()) {
        period = WalmartCalendar.period(for: now)
        do {
            switch try LaunchSequence.run(store: store, kid: kid, key: apiKey,
                                          fetch: fetch, at: now) {
            case .holder(let address, _):
                membership = .member(address: address)
            case .needsGrant(let address, _):
                // The envelope goes to the backend, which decides about a grant.
                // The app proposes nothing and grants nothing.
                membership = .pending(address: address)
            case .offline(let address):
                membership = .offline(address: address)
            }
        } catch {
            membership = .unknown
        }
    }

    public func load(_ offers: [Offer]) { self.offers = offers }

    public var live: [Offer] {
        offers.filter { $0.isRedeemable() }.sorted { $0.expiresAt < $1.expiresAt }
    }

    /// "expires in 3 days" reads as urgency; a date does not.
    public func expiryPhrase(for offer: Offer, at now: Date = Date()) -> String {
        let secs = offer.expiresAt.timeIntervalSince(now)
        if secs <= 0 { return "expired" }
        let days = Int(secs / 86_400)
        if days >= 2 { return "expires in \(days) days" }
        let hours = Int(secs / 3_600)
        if hours >= 2 { return "expires in \(hours) hours" }
        return "expires today"
    }
}
