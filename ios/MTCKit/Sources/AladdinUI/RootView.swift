import SwiftUI
import CryptoKit
import MTCKit

/// Two doors in, one hub, three spokes — the screen map from the design pack.
public struct RootView: View {
    @StateObject private var state: AppState
    @State private var entered = false
    private let offerSecret: SymmetricKey

    public init(state: AppState, offerSecret: SymmetricKey = SymmetricKey(size: .bits256)) {
        _state = StateObject(wrappedValue: state)
        self.offerSecret = offerSecret
    }

    public var body: some View {
        Group {
            if entered { hub } else { welcome }
        }
        .onAppear { state.start() }   // silent: wallet, balance, registration
    }

    private var welcome: some View {
        WelcomeView(
            onStart:   { entered = true },
            onConnect: { entered = true }
        )
        .environmentObject(state)
    }

    private var hub: some View {
        TabView {
            OffersView()
                .environmentObject(state)
                .tabItem { Label("Offers", systemImage: "ticket.fill") }
            ArcadesView()
                .environmentObject(state)
                .tabItem { Label("Arcades", systemImage: "mappin.and.ellipse") }
            AccountView()
                .environmentObject(state)
                .tabItem { Label("Account", systemImage: "person.crop.circle") }
        }
        .tint(Theme.gold)
        .sheet(item: $state.showingRedeem) { offer in
            RedeemView(offer: offer, secret: offerSecret)
        }
    }
}

/// Arcade finder. Deliberately plain: a list beats a map when the answer is
/// "which one is closest and is it still open".
public struct ArcadesView: View {
    public init() {}

    struct Site: Identifiable {
        let id = UUID()
        let name: String, town: String, note: String, open: Bool
    }

    private let sites = [
        Site(name: "Eastgate Mall", town: "Cincinnati", note: "0.8 mi · open til 9", open: true),
        Site(name: "Florence Mall", town: "Florence",   note: "11 mi · open til 9",  open: true),
        Site(name: "Kenwood Towne Centre", town: "Cincinnati", note: "coming this fall", open: false),
    ]

    public var body: some View {
        ZStack {
            Theme.night.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 13) {
                    Text("Arcades").font(Theme.display(28)).foregroundStyle(Theme.ink)
                    ForEach(sites) { s in
                        HStack {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(s.name).font(Theme.body(15)).foregroundStyle(Theme.ink)
                                Text("\(s.town) · \(s.note)")
                                    .font(Theme.body(11.5)).foregroundStyle(Theme.dim)
                            }
                            Spacer()
                            Circle()
                                .fill(s.open ? Theme.good : Theme.dim.opacity(0.4))
                                .frame(width: 8, height: 8)
                        }
                        .padding(13).cabinetPanel()
                    }
                }
                .padding(18)
            }
        }
    }
}

// Offer must be Identifiable for .sheet(item:) — it already is, via MTCKit.
