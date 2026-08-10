import Foundation

/// Solana addresses and signatures are base58. Bitcoin alphabet — no 0, O, I or l,
/// because those are the characters people misread when checking an address by eye.
public enum Base58 {
    static let alphabet = Array("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    static let index: [Character: UInt8] = {
        var m = [Character: UInt8]()
        for (i, c) in alphabet.enumerated() { m[c] = UInt8(i) }
        return m
    }()

    public static func decode(_ s: String) -> Data? {
        var bytes = [UInt8]()
        for ch in s {
            guard let v = index[ch] else { return nil }   // reject typos, never guess
            var carry = Int(v)
            for i in 0..<bytes.count {
                carry += Int(bytes[i]) * 58
                bytes[i] = UInt8(carry & 0xff)
                carry >>= 8
            }
            while carry > 0 { bytes.append(UInt8(carry & 0xff)); carry >>= 8 }
        }
        // Each leading '1' is a leading zero byte, which base58 cannot encode positionally.
        for ch in s { if ch == "1" { bytes.append(0) } else { break } }
        return Data(bytes.reversed())
    }

    public static func encode(_ data: Data) -> String {
        var digits = [UInt8]()
        for byte in data {
            var carry = Int(byte)
            for i in 0..<digits.count {
                carry += Int(digits[i]) << 8
                digits[i] = UInt8(carry % 58)
                carry /= 58
            }
            while carry > 0 { digits.append(UInt8(carry % 58)); carry /= 58 }
        }
        var out = ""
        for byte in data { if byte == 0 { out.append("1") } else { break } }
        for d in digits.reversed() { out.append(alphabet[Int(d)]) }
        return out.isEmpty ? "1" : out
    }

    /// A Solana public key is exactly 32 bytes. Anything else is not an address,
    /// and checking here stops a malformed string reaching an RPC call.
    public static func isValidPublicKey(_ s: String) -> Bool {
        guard let d = decode(s) else { return false }
        return d.count == 32
    }
}
