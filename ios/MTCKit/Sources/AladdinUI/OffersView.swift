import SwiftUI
import MTCKit

/// Home. What she came for: what have I got, and when does it die.
public struct OffersView: View {
    @EnvironmentObject var state: AppState

    public init() {}

    public var body: some View {
        ZStack {
            Theme.night.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    header
                    ForEach(state.live) { offer in
                        Button { state.showingRedeem = offer } label: {
                            OfferRow(offer: offer, expiry: state.expiryPhrase(for: offer))
                        }
                        .buttonStyle(.plain)
                    }
                    if state.live.isEmpty { emptyState }
                    footnote
                }
                .padding(18)
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("My offers").font(Theme.display(28)).foregroundStyle(Theme.ink)
            switch state.membership {
            case .member:
                Label("verified", systemImage: "checkmark.seal.fill")
                    .font(Theme.body(12)).foregroundStyle(Theme.good)
            case .pending:
                Text("setting up your membership")
                    .font(Theme.body(12)).foregroundStyle(Theme.dim)
            case .offline:
                // Never "you hold none" — she may simply be in a basement.
                Label("no signal — your offers still work",
                      systemImage: "wifi.slash")
                    .font(Theme.body(12)).foregroundStyle(Theme.gold)
            case .unknown:
                EmptyView()
            }
        }
        .padding(.bottom, 2)
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Text("Nothing waiting just now")
                .font(Theme.display(17)).foregroundStyle(Theme.ink)
            Text("New offers arrive most weeks.")
                .font(Theme.body(12.5)).foregroundStyle(Theme.dim)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 34)
        .cabinetPanel()
    }

    /// The MTC disclosure, in plain words, on the screen where offers live.
    private var footnote: some View {
        Text("Offers are promotional credits — not a cryptocurrency, and no cash value. "
             + "They expire if unused.")
            .font(Theme.body(10.5)).foregroundStyle(Theme.dim.opacity(0.75))
            .padding(.top, 6)
    }
}

struct OfferRow: View {
    let offer: Offer
    let expiry: String

    /// Under two days left, the expiry turns gold. Urgency is the whole point of
    /// a dated credit, and it should be legible without reading the words.
    private var urgent: Bool { offer.expiresAt.timeIntervalSinceNow < 172_800 }

    var body: some View {
        HStack(spacing: 14) {
            RoundedRectangle(cornerRadius: 9)
                .fill(Theme.gold.opacity(0.16))
                .frame(width: 46, height: 46)
                .overlay(Text("$\(offer.valueCents / 100)")
                    .font(Theme.display(17)).foregroundStyle(Theme.goldBright))
            VStack(alignment: .leading, spacing: 3) {
                Text(offer.item).font(Theme.body(15)).foregroundStyle(Theme.ink)
                Text(expiry).font(Theme.body(11.5))
                    .foregroundStyle(urgent ? Theme.goldBright : Theme.dim)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .semibold)).foregroundStyle(Theme.dim)
        }
        .padding(13)
        .cabinetPanel(glow: urgent)
    }
}
