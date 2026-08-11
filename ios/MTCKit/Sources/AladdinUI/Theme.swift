import SwiftUI

/// Pulled straight off the backglass art so the app and the marketing map read
/// as one world: night indigo, arcade gold spilling out of windows, and the
/// Aladdin's Castle red reserved for the marquee.
public enum Theme {
    public static let night      = Color(red: 0.047, green: 0.055, blue: 0.106)
    public static let nightSoft  = Color(red: 0.078, green: 0.090, blue: 0.176)
    public static let panel      = Color(red: 0.098, green: 0.114, blue: 0.212)
    public static let gold       = Color(red: 0.788, green: 0.659, blue: 0.298)
    public static let goldBright = Color(red: 1.000, green: 0.808, blue: 0.427)
    public static let marquee    = Color(red: 0.824, green: 0.290, blue: 0.204)
    public static let ink        = Color(red: 0.918, green: 0.875, blue: 0.769)
    public static let dim        = Color(red: 0.541, green: 0.573, blue: 0.706)
    public static let good       = Color(red: 0.373, green: 0.816, blue: 0.541)

    /// Never says "wallet", "token", "crypto", or "blockchain" anywhere a
    /// Simple-mode user can see it. That vocabulary is the failure mode.
    public static func display(_ size: CGFloat) -> Font { .system(size: size, weight: .bold, design: .serif) }
    public static func body(_ size: CGFloat) -> Font { .system(size: size, weight: .regular) }
    public static func mono(_ size: CGFloat) -> Font { .system(size: size, weight: .semibold, design: .monospaced) }
}

/// The lit panel used for every card, matching the backglass inset look.
public struct CabinetPanel: ViewModifier {
    var glow: Bool = false
    public func body(content: Content) -> some View {
        content
            .background(RoundedRectangle(cornerRadius: 14).fill(Theme.panel))
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(glow ? Theme.gold.opacity(0.85) : Color.white.opacity(0.08),
                            lineWidth: glow ? 1.5 : 1)
            )
            .shadow(color: glow ? Theme.gold.opacity(0.25) : .clear, radius: 12)
    }
}

public extension View {
    func cabinetPanel(glow: Bool = false) -> some View { modifier(CabinetPanel(glow: glow)) }
}
