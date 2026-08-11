import SwiftUI
import MTCKit

/// Account. Simple mode shows a membership; Crypto mode shows the plumbing.
///
/// The toggle changes vocabulary, never capability. A Simple-mode user is not
/// given less — they are given the same thing without the jargon.
public struct AccountView: View {
    @EnvironmentObject var state: AppState
    @State private var cryptoMode = false

    public init() {}

    public var body: some View {
        ZStack {
            Theme.night.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Account").font(Theme.display(28)).foregroundStyle(Theme.ink)

                    Picker("", selection: $cryptoMode) {
                        Text("Simple").tag(false)
                        Text("Crypto User").tag(true)
                    }
                    .pickerStyle(.segmented)

                    membershipCard
                    if cryptoMode { technicalCard }
                    weekCard
                    disclosure
                }
                .padding(18)
            }
        }
    }

    private var membershipCard: some View {
        VStack(alignment: .leading, spacing: 7) {
            Text("MEMBERSHIP").font(Theme.body(10)).tracking(2).foregroundStyle(Theme.dim)
            switch state.membership {
            case .member:
                Label("Active", systemImage: "checkmark.seal.fill")
                    .font(Theme.display(19)).foregroundStyle(Theme.good)
                Text("Your monthly arcade credits are waiting at any Castle.")
                    .font(Theme.body(12.5)).foregroundStyle(Theme.dim)
            case .pending:
                Text("Setting up").font(Theme.display(19)).foregroundStyle(Theme.gold)
                Text("Nothing for you to do. It finishes on its own.")
                    .font(Theme.body(12.5)).foregroundStyle(Theme.dim)
            case .offline:
                Text("No signal").font(Theme.display(19)).foregroundStyle(Theme.gold)
                Text("Your offers still work. We'll check again when you're back online.")
                    .font(Theme.body(12.5)).foregroundStyle(Theme.dim)
            case .unknown:
                Text("Starting up").font(Theme.display(19)).foregroundStyle(Theme.dim)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(15).cabinetPanel()
    }

    /// Crypto mode, and only here, names the chain. Note there is no Send, no
    /// Swap, and no Buy — the app has no verb that writes to the chain.
    private var technicalCard: some View {
        VStack(alignment: .leading, spacing: 9) {
            Text("ON CHAIN").font(Theme.body(10)).tracking(2).foregroundStyle(Theme.dim)
            row("Address", short(address))
            row("$ACM check", holds ? "holds ≥ 1  ✓" : "—")
            row("Reads", "balance only")
            row("Writes", "none, by design")
            Text("This app never signs a transaction and cannot move your tokens.")
                .font(Theme.body(11)).foregroundStyle(Theme.dim.opacity(0.8))
                .padding(.top, 2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(15).cabinetPanel()
    }

    private var weekCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("THIS WEEK").font(Theme.body(10)).tracking(2).foregroundStyle(Theme.dim)
            Text(WalmartCalendar.label(fiscalYear: state.period.fiscalYear,
                                       week: state.period.week))
                .font(Theme.mono(17)).foregroundStyle(Theme.goldBright)
            Text("Offers open Saturday and close Friday night.")
                .font(Theme.body(12)).foregroundStyle(Theme.dim)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(15).cabinetPanel()
    }

    private var disclosure: some View {
        Text("A Meme Token Credit (MTC) is a promotional credit issued by Instar Brands "
             + "LLC and recorded on its private ledger. It is not a cryptocurrency, not a "
             + "blockchain token, and has no cash value. It expires if unused.")
            .font(Theme.body(10.5)).foregroundStyle(Theme.dim.opacity(0.75))
    }

    private func row(_ k: String, _ v: String) -> some View {
        HStack {
            Text(k).font(Theme.body(12.5)).foregroundStyle(Theme.dim)
            Spacer()
            Text(v).font(Theme.mono(12)).foregroundStyle(Theme.ink)
        }
    }

    private var address: String {
        switch state.membership {
        case .member(let a), .pending(let a), .offline(let a): return a
        case .unknown: return ""
        }
    }
    private var holds: Bool { if case .member = state.membership { return true }; return false }

    /// Never show a full address. First and last six, because address-poisoning
    /// dust is built to match one end only.
    private func short(_ a: String) -> String {
        guard a.count > 14 else { return a.isEmpty ? "—" : a }
        return "\(a.prefix(6))…\(a.suffix(6))"
    }
}
