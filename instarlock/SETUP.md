# InstarLock toolchain setup (macOS)

Three installs, in order. Rust first (everything builds on it), then the
Solana CLI, then Anchor.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
```

```bash
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
```

```bash
cargo install --git https://github.com/coral-xyz/anchor avm --force && avm install latest && avm use latest
```

Then from `instarlock/`:

```bash
anchor build
```

Devnet keys + airdrop for testing:

```bash
solana-keygen new --no-bip39-passphrase -o ~/.config/solana/instarlock-dev.json && solana config set --keypair ~/.config/solana/instarlock-dev.json --url devnet && solana airdrop 2
```
