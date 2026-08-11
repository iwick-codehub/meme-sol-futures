import SwiftUI
import MTCKit

/// The backglass. One tap in.
///
/// Simple mode never says wallet, token, crypto, or blockchain — not on this
/// screen and not anywhere behind it. The second door exists only for people
/// who already own a wallet and came looking for it.
public struct WelcomeView: View {
    @EnvironmentObject var state: AppState
    public var onStart: () -> Void = {}
    public var onConnect: () -> Void = {}

    public init(onStart: @escaping () -> Void = {}, onConnect: @escaping () -> Void = {}) {
        self.onStart = onStart; self.onConnect = onConnect
    }

    public var body: some View {
        ZStack {
            LinearGradient(colors: [Theme.nightSoft, Theme.night],
                           startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer(minLength: 24)

                // marquee
                VStack(spacing: 2) {
                    Text("ALADDIN'S")
                        .font(Theme.display(46)).foregroundStyle(Theme.marquee)
                    Text("CASTLE")
                        .font(Theme.display(46)).foregroundStyle(Theme.marquee)
                }
                .shadow(color: Theme.marquee.opacity(0.55), radius: 18)

                Text("BALL IN PLAY")
                    .font(Theme.body(12)).tracking(4)
                    .foregroundStyle(Theme.gold)
                    .padding(.top, 10)

                // 1UP / 2UP reels, the furniture the backglass already promises
                HStack(spacing: 26) {
                    Reel(label: "1UP", value: "9430")
                    Reel(label: "2UP", value: "00000")
                }
                .padding(.top, 14)

                Spacer()

                VStack(spacing: 12) {
                    CabinetButton(title: "1 PLAYER", subtitle: "PRESS START",
                                  tint: Theme.gold, action: onStart)
                    CabinetButton(title: "2 PLAYER", subtitle: "SAME MACHINE",
                                  tint: Theme.marquee, action: onStart)

                    Button(action: onConnect) {
                        Text("I already have a wallet")
                            .font(Theme.body(12)).foregroundStyle(Theme.dim)
                            .underline()
                    }
                    .buttonStyle(.plain)
                    .padding(.top, 6)
                }
                .padding(.horizontal, 28)

                Spacer(minLength: 28)
            }
        }
    }
}

struct Reel: View {
    let label: String, value: String
    var body: some View {
        VStack(spacing: 4) {
            Text(label).font(Theme.body(10)).tracking(2).foregroundStyle(Theme.dim)
            Text(value)
                .font(Theme.mono(19)).foregroundStyle(Theme.ink)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(RoundedRectangle(cornerRadius: 4).fill(Color.black.opacity(0.55)))
                .overlay(RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.white.opacity(0.12), lineWidth: 1))
        }
    }
}

/// A physical arcade button: chunky, high contrast, unmissable at arm's length.
struct CabinetButton: View {
    let title: String, subtitle: String, tint: Color
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            VStack(spacing: 3) {
                Text(title).font(Theme.display(21)).foregroundStyle(.white)
                Text(subtitle).font(Theme.body(10)).tracking(2)
                    .foregroundStyle(.white.opacity(0.75))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 15)
            .background(RoundedRectangle(cornerRadius: 10).fill(tint.opacity(0.92)))
            .overlay(RoundedRectangle(cornerRadius: 10)
                .stroke(.white.opacity(0.35), lineWidth: 1.5))
            .shadow(color: tint.opacity(0.45), radius: 14, y: 4)
        }
        .buttonStyle(.plain)
    }
}
