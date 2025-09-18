import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CASH_KEYWORDS = ['ATM WITHDRAWAL', 'CUSTOMER WITHDRAWAL']
REWARD_KEYWORDS = ['CASH BACK', 'REDEMPTION', 'REWARD']
CREDIT_CARD_ACCOUNTS = [
    'Amex CC', 'Discover CC', 'Wells Fargo CC', 'Target RedCard', 'Chase CC', 'Etherfi CC'
]

def run_data_integrity_audit():
    """
    Performs a comprehensive, read-only audit of the master transaction file
    to identify common data integrity issues like miscategorized transfers,
    polarity errors, and truly unmatched payment transfers.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Data Integrity Audit Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object', 'ReconciliationID': 'object'})
        print(f"✅ Master file loaded. Auditing {len(df)} transactions...\n")

        # --- 1. Identify Miscategorized 'Transfer' Transactions ---
        print("--- Audit 1: Miscategorized 'Transfer' Transactions ---")
        cash_mask = df['Description'].str.contains('|'.join(CASH_KEYWORDS), case=False, na=False)
        reward_mask = df['Description'].str.contains('|'.join(REWARD_KEYWORDS), case=False, na=False)
        miscategorized_mask = (df['Category'] == 'Transfer') & (cash_mask | reward_mask)
        df_miscategorized = df[miscategorized_mask]

        if not df_miscategorized.empty:
            print(f"Found {len(df_miscategorized)} transactions categorized as 'Transfer' that should be reviewed:")
            print("These are likely cash withdrawals or rewards and should be re-categorized.\n")
            print(df_miscategorized[['Date', 'Account', 'Description', 'Amount']].to_string(index=False))
        else:
            print("✅ No obvious cash withdrawals or rewards found in the 'Transfer' category.")
        
        print("\n" + "="*50 + "\n")

        # --- 2. Identify Polarity Errors in Credit Card Payments ---
        print("--- Audit 2: Potential Polarity Errors in CC Payments ---")
        polarity_error_mask = (
            df['Account'].isin(CREDIT_CARD_ACCOUNTS) &
            (df['Category'] == 'Transfer') &
            (df['Amount'] < 0)
        )
        df_polarity_errors = df[polarity_error_mask]

        if not df_polarity_errors.empty:
            print(f"Found {len(df_polarity_errors)} credit card payments recorded with a negative value:")
            print("These amounts should likely be positive to reflect a credit to the account.\n")
            print(df_polarity_errors[['Date', 'Account', 'Description', 'Amount']].to_string(index=False))
        else:
            print("✅ No credit card payments with negative values found.")

        print("\n" + "="*50 + "\n")

        # --- 3. Identify Truly Unmatched Transfers ---
        print("--- Audit 3: Truly Unmatched Inter-Account Transfers ---")
        
        # Exclude items identified in the previous audits from this analysis
        unmatched_mask = (
            (df['Category'] == 'Transfer') &
            (df['ReconciliationID'].isna()) &
            (~miscategorized_mask) &
            (~polarity_error_mask)
        )
        df_unmatched = df[unmatched_mask]

        if not df_unmatched.empty:
            print(f"Found {len(df_unmatched)} true transfer transactions that remain unmatched:")
            # --- FIX: Corrected the syntax for the .agg() function ---
            summary = df_unmatched.groupby('Account')['Amount'].agg(
                Credit_Count=lambda x: (x > 0).sum(),
                Unmatched_Credits=lambda x: x[x > 0].sum(),
                Debit_Count=lambda x: (x < 0).sum(),
                Unmatched_Debits=lambda x: x[x < 0].sum()
            ).reset_index()
            # --- END FIX ---
            summary['Net_Unreconciled'] = summary['Unmatched_Credits'] + summary['Unmatched_Debits']
            print(summary.to_string(index=False))
        else:
            print("✅ No truly unmatched transfers found after accounting for miscategorizations.")

        print("\n\n--- Audit Complete ---")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_data_integrity_audit()

