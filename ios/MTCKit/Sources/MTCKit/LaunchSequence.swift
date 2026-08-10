import Foundation
import CryptoKit

/// What happens when she taps GET STARTED, and on every launch after.
///
/// All of it is silent. There is no wallet setup screen, no seed phrase, no
/// consent sheet, no spinner explaining what a token account is. She sees the
/// backglass, then she sees her offers.
///
/// The grant POLICY deliberately does not live here. The app only ever reports
/// "this address holds none" and lets the backend decide what to do about it —
/// so that decision can change server-side, after counsel answers, without
/// shipping a new build.
public enum LaunchSequence {

    public enum Outcome: Equatable, Sendable {
        case holder(address: String, holding: ACMCheck.Holding)
        case needsGrant(address: String, registration: Auth.Envelope)
        case offline(address: String)
    }

    /// One read-only RPC call, injected so this is testable without a network and
    /// so the app can swap in its own retry and caching policy.
    public typealias BalanceFetch = (String) throws -> Data

    public static func run(store: KeyStore,
                           kid: String,
                           key: SymmetricKey,
                           fetch: BalanceFetch,
                           at now: Date = Date()) throws -> Outcome {
        // 1. Same address every launch. A second address would strand her token.
        let wallet = try EmbeddedWallet.loadOrCreate(in: store)

        // 2. Ask the chain the one question the app is allowed to ask.
        let data: Data
        do { data = try fetch(wallet.address) }
        catch { return .offline(address: wallet.address) }   // dead zone: not an error

        let holding: ACMCheck.Holding
        do { holding = try ACMCheck.parse(data) }
        catch { return .offline(address: wallet.address) }   // a 429 is not "holds zero"

        if holding.holdsAtLeast(1) {
            return .holder(address: wallet.address, holding: holding)
        }

        // 3. Report the address, signed, and let the server decide. The app never
        //    grants anything and has no verb that could.
        let body = "register|\(wallet.address)|holds=0"
        let env = Auth.sign(body: body, kid: kid, key: key, at: now)
        return .needsGrant(address: wallet.address, registration: env)
    }
}
