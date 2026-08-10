import Foundation

/// The reader kiosk's side of the counter: burn exactly once, then keep the line
/// moving whether or not the link is up.
///
/// The burn — not the rotating code — is what makes a credit single-use. A code
/// that is live and valid still spends only once, because the burn is keyed on
/// the offer, not on the code.
///
/// HONEST LIMIT, and it must be designed around rather than papered over: while a
/// reader is offline it can only see its OWN burns. Two kiosks both offline can
/// each accept the same offer, and the collision surfaces at sync. That is the
/// deliberate trade for "the counter never stops" — see `Conflict`. With one
/// reader per site it cannot happen at all; with several, the sync resolves it
/// and the second becomes a reversal, not a silent double-spend.
public final class BurnLedger {

    public enum Failure: Error, Equatable {
        case alreadyBurned(offerID: String, at: Date)
    }

    public struct Burn: Equatable, Sendable {
        public let offerID: String
        public let at: Date
        public let readerID: String
        public var synced: Bool

        public init(offerID: String, at: Date, readerID: String, synced: Bool = false) {
            self.offerID = offerID; self.at = at
            self.readerID = readerID; self.synced = synced
        }
    }

    /// Detected at sync: two offline readers burned the same offer. The earliest
    /// burn stands, the rest are reversals for the operator to settle.
    public struct Conflict: Equatable, Sendable {
        public let offerID: String
        public let kept: Date
        public let reversed: [Date]
    }

    private let readerID: String
    private var burns: [String: Burn] = [:]
    private let lock = NSLock()

    public init(readerID: String) { self.readerID = readerID }

    /// Atomic. The check and the write happen under one lock, or two taps landing
    /// together would both see "not burned" and both hand over the goods.
    @discardableResult
    public func burn(offerID: String, at now: Date = Date()) throws -> Burn {
        lock.lock(); defer { lock.unlock() }
        if let existing = burns[offerID] {
            throw Failure.alreadyBurned(offerID: offerID, at: existing.at)
        }
        let b = Burn(offerID: offerID, at: now, readerID: readerID, synced: false)
        burns[offerID] = b
        return b
    }

    public func isBurned(_ offerID: String) -> Bool {
        lock.lock(); defer { lock.unlock() }
        return burns[offerID] != nil
    }

    /// Queued burns awaiting the link. The kiosk shows "queued · will sync" and
    /// the cashier carries on; nothing here blocks the counter.
    public var pending: [Burn] {
        lock.lock(); defer { lock.unlock() }
        return burns.values.filter { !$0.synced }.sorted { $0.at < $1.at }
    }

    public func markSynced(_ offerIDs: [String]) {
        lock.lock(); defer { lock.unlock() }
        for id in offerIDs { burns[id]?.synced = true }
    }

    /// Server-side reconciliation across readers. Earliest burn wins — it is the
    /// one the customer actually experienced first.
    public static func reconcile(_ all: [Burn]) -> (accepted: [Burn], conflicts: [Conflict]) {
        var byOffer: [String: [Burn]] = [:]
        for b in all { byOffer[b.offerID, default: []].append(b) }

        var accepted: [Burn] = [], conflicts: [Conflict] = []
        for (offer, group) in byOffer.sorted(by: { $0.key < $1.key }) {
            let ordered = group.sorted { $0.at < $1.at }
            accepted.append(ordered[0])
            if ordered.count > 1 {
                conflicts.append(Conflict(offerID: offer, kept: ordered[0].at,
                                          reversed: ordered.dropFirst().map(\.at)))
            }
        }
        return (accepted.sorted { $0.at < $1.at }, conflicts)
    }
}
