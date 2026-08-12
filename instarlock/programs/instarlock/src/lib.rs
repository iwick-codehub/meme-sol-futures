//! InstarLock — the escrow engine for Instar meme coin futures.
//!
//! Fully-collateralized, physically-settled 14-day forwards. The whole
//! MARKET-SPEC zero-risk law, enforced by chain:
//!
//!   post()   seller's coins move to a program vault at posting (firm book).
//!            The two hard listing vetoes run ON-CHAIN: a mint with a live
//!            freeze or mint authority cannot be posted, period.
//!   lift()   THE ATOMIC MATCH: buyer's full strike SOL locks and the
//!            listing flips to an irrevocable contract in one transaction.
//!            No gap, no default window, on either side.
//!   cancel() unlifted listings refund to the seller only after expiry
//!            (quotes are FIRM for their whole life — that's the product).
//!   settle() permissionless crank after the 14-day term: 100% of coins to
//!            the buyer, strike minus the all-in 10% spread to the seller,
//!            the 10% to treasury. One number, nothing else.
//!
//! Discipline (see MARKET-SPEC): minimal surface, no admin instructions,
//! no pause switch, no upgrade path once authority is burned at deploy.
//! The house cannot touch escrow. That is the point.

use anchor_lang::prelude::*;
use anchor_lang::system_program;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

declare_id!("Lock111111111111111111111111111111111111111"); // replaced at first deploy

pub const TERM_SECS: i64 = 14 * 24 * 60 * 60; // exactly 14 days
pub const LISTING_LIFE_SECS: i64 = 7 * 24 * 60 * 60; // firm-quote life
pub const COMMISSION_BPS: u128 = 1_000; // the flat ALL-IN 10% spread (rev 2026-08-12: float + writing fee retired)
pub const MIN_NOTIONAL_LAMPORTS: u64 = 50_000_000_000; // 50 SOL
pub const MIN_LOT_WHOLE_TOKENS: u64 = 1_000_000; // 1M coins

/// House treasury (the all-in 10%) is fixed at build time — no instruction
/// can change it.
pub mod house {
    use anchor_lang::prelude::declare_id;
    // PLACEHOLDER: set to FUT TREASURY before deploy.
    declare_id!("11111111111111111111111111111111");
}

#[program]
pub mod instarlock {
    use super::*;

    /// Seller posts a firm rung: `lot` (base units) at `price_lamports`
    /// (strike in SOL lamports for the whole lot). Coins move to the vault
    /// in this same transaction — no coins, no quote.
    pub fn post(ctx: Context<Post>, lot: u64, price_lamports: u64) -> Result<()> {
        let mint = &ctx.accounts.mint;

        // The two hard vetoes, enforced by chain, not by policy.
        require!(mint.freeze_authority.is_none(), LockErr::FreezeAuthorityLive);
        require!(mint.mint_authority.is_none(), LockErr::MintAuthorityLive);

        // Dual minimums, both binding.
        let min_lot = MIN_LOT_WHOLE_TOKENS
            .checked_mul(10u64.pow(mint.decimals as u32))
            .ok_or(LockErr::MathOverflow)?;
        require!(lot >= min_lot, LockErr::LotBelowMinimum);
        require!(price_lamports >= MIN_NOTIONAL_LAMPORTS, LockErr::NotionalBelowMinimum);

        let now = Clock::get()?.unix_timestamp;
        let c = &mut ctx.accounts.contract;
        c.seller = ctx.accounts.seller.key();
        c.mint = mint.key();
        c.lot = lot;
        c.price_lamports = price_lamports;
        c.posted_ts = now;
        c.expiry_ts = now + LISTING_LIFE_SECS;
        c.state = ContractState::Open;
        c.buyer = Pubkey::default();
        c.settle_ts = 0;
        c.bump = ctx.bumps.contract;

        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.seller_ata.to_account_info(),
                    to: ctx.accounts.vault.to_account_info(),
                    authority: ctx.accounts.seller.to_account_info(),
                },
            ),
            lot,
        )
    }

    /// THE ATOMIC MATCH. Buyer locks the full strike into the contract
    /// account and the listing becomes an irrevocable 14-day contract,
    /// all in one transaction.
    pub fn lift(ctx: Context<Lift>) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        {
            let c = &ctx.accounts.contract;
            require!(c.state == ContractState::Open, LockErr::NotOpen);
            require!(now < c.expiry_ts, LockErr::ListingExpired);
            require!(ctx.accounts.buyer.key() != c.seller, LockErr::SelfDeal);
        }

        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.buyer.to_account_info(),
                    to: ctx.accounts.contract.to_account_info(),
                },
            ),
            ctx.accounts.contract.price_lamports,
        )?;

        let c = &mut ctx.accounts.contract;
        c.buyer = ctx.accounts.buyer.key();
        c.state = ContractState::Matched;
        c.settle_ts = now + TERM_SECS;
        Ok(())
    }

    /// Refund an unlifted listing — seller only, and only AFTER expiry.
    /// Firm means firm.
    pub fn cancel(ctx: Context<Cancel>) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        {
            let c = &ctx.accounts.contract;
            require!(c.state == ContractState::Open, LockErr::NotOpen);
            require!(now >= c.expiry_ts, LockErr::QuoteStillFirm);
        }
        let lot = ctx.accounts.contract.lot;
        transfer_from_vault(&ctx.accounts.contract, TransferFromVault {
            vault: ctx.accounts.vault.to_account_info(),
            to: ctx.accounts.seller_ata.to_account_info(),
            token_program: ctx.accounts.token_program.to_account_info(),
        }, lot)?;
        ctx.accounts.contract.state = ContractState::Cancelled;
        Ok(())
    }

    /// Permissionless settlement crank, valid the second the term ends.
    /// Anyone may call it; funds can only go where the contract says.
    pub fn settle(ctx: Context<Settle>) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        {
            let c = &ctx.accounts.contract;
            require!(c.state == ContractState::Matched, LockErr::NotMatched);
            require!(now >= c.settle_ts, LockErr::TermStillRunning);
        }

        let lot = ctx.accounts.contract.lot;
        let price = ctx.accounts.contract.price_lamports;

        // Coin leg: 100% of the lot to the buyer.
        transfer_from_vault(&ctx.accounts.contract, TransferFromVault {
            vault: ctx.accounts.vault.to_account_info(),
            to: ctx.accounts.buyer_ata.to_account_info(),
            token_program: ctx.accounts.token_program.to_account_info(),
        }, lot)?;

        // SOL leg: the all-in 10% to treasury, 90% to the seller.
        let house_take = (price as u128 * COMMISSION_BPS / 10_000) as u64;
        require!(house_take < price, LockErr::FeesExceedStrike);
        let seller_take = price - house_take;

        pay_from_contract(&ctx.accounts.contract.to_account_info(),
                          &ctx.accounts.house_treasury.to_account_info(), house_take)?;
        pay_from_contract(&ctx.accounts.contract.to_account_info(),
                          &ctx.accounts.seller.to_account_info(), seller_take)?;

        ctx.accounts.contract.state = ContractState::Settled;
        Ok(())
    }
}

/// Vault transfers are signed by the contract PDA itself.
struct TransferFromVault<'info> {
    vault: AccountInfo<'info>,
    to: AccountInfo<'info>,
    token_program: AccountInfo<'info>,
}

fn transfer_from_vault(contract: &Account<FuturesContract>, t: TransferFromVault, amount: u64) -> Result<()> {
    if amount == 0 { return Ok(()); }
    let seeds: &[&[u8]] = &[b"contract", contract.seller.as_ref(), contract.mint.as_ref(),
                            &contract.posted_ts.to_le_bytes(), &[contract.bump]];
    token::transfer(
        CpiContext::new_with_signer(
            t.token_program,
            Transfer { from: t.vault, to: t.to, authority: contract.to_account_info() },
            &[seeds],
        ),
        amount,
    )
}

fn pay_from_contract<'info>(contract: &AccountInfo<'info>, to: &AccountInfo<'info>, lamports: u64) -> Result<()> {
    **contract.try_borrow_mut_lamports()? -= lamports;
    **to.try_borrow_mut_lamports()? += lamports;
    Ok(())
}

#[account]
pub struct FuturesContract {
    pub seller: Pubkey,
    pub mint: Pubkey,
    pub buyer: Pubkey,
    pub lot: u64,
    pub price_lamports: u64,
    pub posted_ts: i64,
    pub expiry_ts: i64,
    pub settle_ts: i64,
    pub state: ContractState,
    pub bump: u8,
}
impl FuturesContract { pub const SPACE: usize = 8 + 32*3 + 8*5 + 1 + 1; }

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq)]
pub enum ContractState { Open, Matched, Settled, Cancelled }

#[derive(Accounts)]
#[instruction(lot: u64, price_lamports: u64)]
pub struct Post<'info> {
    #[account(mut)]
    pub seller: Signer<'info>,
    pub mint: Account<'info, Mint>,
    #[account(mut, associated_token::mint = mint, associated_token::authority = seller)]
    pub seller_ata: Account<'info, TokenAccount>,
    #[account(init, payer = seller, space = FuturesContract::SPACE,
              seeds = [b"contract", seller.key().as_ref(), mint.key().as_ref(),
                       &Clock::get()?.unix_timestamp.to_le_bytes()],
              bump)]
    pub contract: Account<'info, FuturesContract>,
    #[account(init, payer = seller, associated_token::mint = mint,
              associated_token::authority = contract)]
    pub vault: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Lift<'info> {
    #[account(mut)]
    pub buyer: Signer<'info>,
    #[account(mut)]
    pub contract: Account<'info, FuturesContract>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Cancel<'info> {
    #[account(mut, address = contract.seller)]
    pub seller: Signer<'info>,
    #[account(mut)]
    pub contract: Account<'info, FuturesContract>,
    #[account(mut, associated_token::mint = contract.mint, associated_token::authority = contract)]
    pub vault: Account<'info, TokenAccount>,
    #[account(mut, associated_token::mint = contract.mint, associated_token::authority = seller)]
    pub seller_ata: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Settle<'info> {
    /// Anyone may crank settlement; they pay gas, funds go only where
    /// the contract says.
    pub cranker: Signer<'info>,
    #[account(mut)]
    pub contract: Account<'info, FuturesContract>,
    #[account(mut, associated_token::mint = contract.mint, associated_token::authority = contract)]
    pub vault: Account<'info, TokenAccount>,
    /// CHECK: validated against the contract record.
    #[account(mut, address = contract.seller)]
    pub seller: AccountInfo<'info>,
    #[account(mut, associated_token::mint = contract.mint, associated_token::authority = contract.buyer)]
    pub buyer_ata: Account<'info, TokenAccount>,
    /// CHECK: fixed house treasury, baked at build time.
    #[account(mut, address = house::ID)]
    pub house_treasury: AccountInfo<'info>,
    pub token_program: Program<'info, Token>,
}

#[error_code]
pub enum LockErr {
    #[msg("mint has a live freeze authority — hard veto")] FreezeAuthorityLive,
    #[msg("mint has a live mint authority — hard veto")] MintAuthorityLive,
    #[msg("lot below the 1M-coin minimum")] LotBelowMinimum,
    #[msg("notional below the 50 SOL minimum")] NotionalBelowMinimum,
    #[msg("listing is not open")] NotOpen,
    #[msg("listing expired — refund via cancel()")] ListingExpired,
    #[msg("seller cannot lift their own listing")] SelfDeal,
    #[msg("firm quotes cannot be cancelled before expiry")] QuoteStillFirm,
    #[msg("contract is not matched")] NotMatched,
    #[msg("14-day term still running")] TermStillRunning,
    #[msg("fees exceed strike")] FeesExceedStrike,
    #[msg("math overflow")] MathOverflow,
}
