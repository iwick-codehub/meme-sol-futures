import SwiftUI
import CryptoKit
import MTCKit

/// The moment at the counter.
///
/// Everything here is generated on the phone. No network call, no spinner, no
/// failure state that depends on a mall's cellular coverage. The code redraws
/// itself every 30 seconds so a photographed screen is worthless.
public struct RedeemView: View {
    let offer: Offer
    let secret: SymmetricKey

    @State private var code: RedemptionCode.Code
    @State private var remaining: Int = Int(RedemptionCode.stepSeconds)

    private let tick = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    public init(offer: Offer, secret: SymmetricKey) {
        self.offer = offer
        self.secret = secret
        _code = State(initialValue: RedemptionCode.generate(secret: secret, offerID: offer.id))
    }

    public var body: some View {
        ZStack {
            Theme.night.ignoresSafeArea()
            VStack(spacing: 20) {
                Text("Show this at the counter")
                    .font(Theme.display(21)).foregroundStyle(Theme.ink)

                // The QR stands in for a real generator; the payload is the truth.
                ZStack {
                    RoundedRectangle(cornerRadius: 16).fill(.white)
                        .frame(width: 232, height: 232)
                    QRPlaceholder(payload: code.qrPayload)
                        .frame(width: 196, height: 196)
                }
                .shadow(color: Theme.gold.opacity(0.3), radius: 20)

                // Human fallback for when a scanner is broken, which happens.
                Text(spaced(code.digits))
                    .font(Theme.mono(30)).tracking(5).foregroundStyle(Theme.goldBright)

                countdown

                Text("Works with no signal — the code is made right here on your phone.")
                    .font(Theme.body(11.5)).foregroundStyle(Theme.dim)
                    .multilineTextAlignment(.center).padding(.horizontal, 34)

                Spacer()
            }
            .padding(.top, 34)
        }
        .onReceive(tick) { _ in refresh() }
        .onAppear { refresh() }
    }

    private var countdown: some View {
        HStack(spacing: 9) {
            ZStack {
                Circle().stroke(Theme.dim.opacity(0.28), lineWidth: 3)
                Circle()
                    .trim(from: 0, to: CGFloat(remaining) / CGFloat(RedemptionCode.stepSeconds))
                    .stroke(Theme.gold, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                    .animation(.linear(duration: 0.9), value: remaining)
            }
            .frame(width: 19, height: 19)
            Text("code refreshes in 0:\(String(format: "%02d", remaining))")
                .font(Theme.body(12)).foregroundStyle(Theme.dim)
        }
    }

    /// Regenerating unconditionally each tick is deliberate: `generate` is pure
    /// on the clock, so it returns the identical code inside a window and rolls
    /// exactly on the boundary without any state machine to get wrong.
    private func refresh() {
        code = RedemptionCode.generate(secret: secret, offerID: offer.id)
        remaining = code.secondsRemaining()
    }

    private func spaced(_ s: String) -> String {
        let mid = s.index(s.startIndex, offsetBy: 3)
        return "\(s[s.startIndex..<mid]) \(s[mid...])"
    }
}

/// Deterministic block pattern derived from the payload. A real generator drops
/// in here; this keeps the layout honest and the target size correct meanwhile.
struct QRPlaceholder: View {
    let payload: String
    var body: some View {
        let cells = 21
        let bits = Array(payload.utf8)
        return GeometryReader { geo in
            let s = geo.size.width / CGFloat(cells)
            ForEach(0..<cells, id: \.self) { r in
                ForEach(0..<cells, id: \.self) { c in
                    if (Int(bits[(r * cells + c) % bits.count]) &+ r &* 7 &+ c &* 13) % 2 == 0 {
                        Rectangle().fill(.black)
                            .frame(width: s, height: s)
                            .position(x: (CGFloat(c) + 0.5) * s, y: (CGFloat(r) + 0.5) * s)
                    }
                }
            }
        }
    }
}
