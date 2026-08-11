import Foundation
import CryptoKit

/// Deferred minting: a claim is a free row in our database, and the on-chain
/// write waits until someone proves they are real by turning up.
///
/// This is the anti-farming design and the largest cost saving in the 99¢ model
/// at the same time. A bot can claim a million tokens and it costs us nothing,
/// because nothing is written until first engagement at a reader — and a bot
/// cannot walk into a mall in Ohio. No phone number, no SMS, no PII, and no
/// friction whatsoever for a real customer.
///
/// ~$0.15 of Solana rent per wallet is never spent on a wallet that never shows.
public enum Claim {

    /// A claim's life. Only the last transition costs money.
    public enum State: String, Codable, Equatable, Sendable {
        case claimed      // a row. free. anyone, no purchase, no identity.
        case engaged      // seen at a reader — a person exists
        case minted       // token pushed on-chain. the ONLY paid step.
        case void         // expired or refused before it ever cost anything
    }

    public struct Record: Codable, Equatable, Sendable {
        public let address: String
        public let claimedAt: Date
        public var state: State
        public var engagedAt: Date?
        public var mintedAt: Date?
        /// Where they came from, so web and app claims can be told apart without
        /// treating either as more entitled than the other.
        public let source: String

        public init(address: String, claimedAt: Date, source: String,
                    state: State = .claimed) {
            self.address = address; self.claimedAt = claimedAt
            self.source = source; self.state = state
        }
    }

    public enum Failure: Error, Equatable {
        case badAddress
        case alreadyClaimed(address: String)
        case notEngaged(address: String)
        case alreadyMinted(address: String)
        case expired(address: String)
    }

    /// How long an unengaged claim is honoured before it is swept. Nothing was
    /// spent on it, so expiry costs the claimant nothing real — it only keeps the
    /// table from growing without bound.
    public static let unengagedTTL: TimeInterval = 365 * 24 * 3600

    /// Free, unauthenticated, open to anyone. No purchase, no phone number, no
    /// identity. Deliberately cheap: this is the step bots are welcome to abuse.
    public static func claim(address: String, source: String,
                             existing: Record?, at now: Date = Date()) throws -> Record {
        guard Base58.isValidPublicKey(address) else { throw Failure.badAddress }
        if let e = existing, e.state != .void { throw Failure.alreadyClaimed(address: address) }
        return Record(address: address, claimedAt: now, source: source)
    }

    /// First engagement at a reader. THIS is the bot filter — it requires a body
    /// in a building — and it is what authorises the mint.
    public static func engage(_ record: Record, at now: Date = Date()) throws -> Record {
        var r = record
        switch r.state {
        case .minted: throw Failure.alreadyMinted(address: r.address)
        case .void:   throw Failure.expired(address: r.address)
        case .claimed, .engaged: break
        }
        if now.timeIntervalSince(r.claimedAt) > unengagedTTL && r.state == .claimed {
            throw Failure.expired(address: r.address)
        }
        if r.engagedAt == nil { r.engagedAt = now }
        r.state = .engaged
        return r
    }

    /// The only step that touches the chain or costs a cent. Refuses anything
    /// that has not engaged, so a claim alone can never trigger a transfer.
    public static func mint(_ record: Record, at now: Date = Date()) throws -> Record {
        var r = record
        guard r.state != .minted else { throw Failure.alreadyMinted(address: r.address) }
        guard r.state == .engaged else { throw Failure.notEngaged(address: r.address) }
        r.state = .minted
        r.mintedAt = now
        return r
    }

    public static func sweep(_ records: [Record], at now: Date = Date()) -> [Record] {
        records.map {
            guard $0.state == .claimed,
                  now.timeIntervalSince($0.claimedAt) > unengagedTTL else { return $0 }
            var r = $0; r.state = .void; return r
        }
    }

    /// What the mint actually costs, and what deferring it saves. Rent is the only
    /// per-user cost that never comes back.
    public struct Economics: Equatable, Sendable {
        public let claims: Int
        public let engaged: Int
        public let rentPerWallet: Double

        public init(claims: Int, engaged: Int, rentPerWallet: Double) {
            self.claims = claims; self.engaged = engaged; self.rentPerWallet = rentPerWallet
        }

        public var mintCost: Double { Double(engaged) * rentPerWallet }
        /// What minting at claim time would have cost instead.
        public var naiveCost: Double { Double(claims) * rentPerWallet }
        public var saved: Double { naiveCost - mintCost }
    }
}
