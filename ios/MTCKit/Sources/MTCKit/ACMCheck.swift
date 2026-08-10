import Foundation

/// The single question the app is allowed to ask the chain:
/// **does this wallet hold at least 1 $ACM?**
///
/// Read-only, one direction. Nothing here signs a transaction, moves a token, or
/// writes anything on-chain — the app has no verb for it. The answer is a boolean
/// that gates MTC issuance; the MTC itself lives in our own ledger.
public enum ACMCheck {

    /// pump.fun mint, created Sept 2025.
    public static let mint = "4PRz3EwhbjrrX6YksMDuUzrXT51pr7CQtXNCravhpump"

    public struct Holding: Equatable, Sendable {
        public let rawAmount: UInt64     // integer base units, never a Double
        public let decimals: Int
        public let accountCount: Int

        /// Whole tokens, for display only. Never compare on this — see `holdsAtLeast`.
        public var uiAmount: Double {
            Double(rawAmount) / pow(10.0, Double(decimals))
        }

        /// Integer comparison in base units. Doing this in floating point is how a
        /// holder of exactly 1.0 gets told they hold 0.9999999 and is turned away.
        public func holdsAtLeast(_ whole: UInt64) -> Bool {
            var unit: UInt64 = 1
            for _ in 0..<decimals {
                let (m, overflow) = unit.multipliedReportingOverflow(by: 10)
                if overflow { return true }
                unit = m
            }
            let (need, overflow) = whole.multipliedReportingOverflow(by: unit)
            return overflow ? false : rawAmount >= need
        }
    }

    public enum ParseError: Error, Equatable {
        case rpcError(String)
        case malformed
    }

    /// The JSON-RPC body for `getTokenAccountsByOwner`, filtered to the ACM mint.
    public static func balanceRequest(owner: String, id: Int = 1) -> [String: Any] {
        [
            "jsonrpc": "2.0", "id": id,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner,
                ["mint": mint],
                ["encoding": "jsonParsed", "commitment": "confirmed"],
            ],
        ]
    }

    /// Parses the RPC reply.
    ///
    /// Amounts are SUMMED across accounts: one owner can hold the same mint in
    /// several token accounts, and reading only the first would under-report a
    /// legitimate holder. Amount is read as a string and kept integral throughout.
    public static func parse(_ data: Data) throws -> Holding {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ParseError.malformed
        }
        if let err = root["error"] as? [String: Any] {
            throw ParseError.rpcError(err["message"] as? String ?? "unknown RPC error")
        }
        guard let result = root["result"] as? [String: Any],
              let value = result["value"] as? [[String: Any]] else {
            throw ParseError.malformed
        }

        var total: UInt64 = 0
        var decimals = 6            // ACM's mint decimals; still read per-account below
        for entry in value {
            guard let account = entry["account"] as? [String: Any],
                  let dataField = account["data"] as? [String: Any],
                  let parsed = dataField["parsed"] as? [String: Any],
                  let info = parsed["info"] as? [String: Any],
                  let amt = info["tokenAmount"] as? [String: Any],
                  let raw = amt["amount"] as? String,
                  let n = UInt64(raw) else { throw ParseError.malformed }
            if let d = amt["decimals"] as? Int { decimals = d }
            let (sum, overflow) = total.addingReportingOverflow(n)
            total = overflow ? UInt64.max : sum
        }
        return Holding(rawAmount: total, decimals: decimals, accountCount: value.count)
    }

    /// No token account at all is a valid answer meaning zero, not an error — a
    /// wallet that has never held ACM simply has nothing to return.
    public static func holdsAtLeastOne(_ data: Data) throws -> Bool {
        try parse(data).holdsAtLeast(1)
    }
}
