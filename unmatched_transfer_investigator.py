import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"

def investigate_unmatched_transfers():
    """
    A diagnostic tool to analyze 'Transfer' transactions that do not have a
    ReconciliationID. It provides a summary report and a detailed breakdown
    of unmatched debits from the primary checking account.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Unmatched Transfer Investigator ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)

        if 'ReconciliationID' not in df.columns:
            print("❌ ERROR: The 'ReconciliationID' column has not been created yet.")
            print("   Please run the 'backfill_reconciliation_ids.py' script first.")
            sys.exit(1)

        # --- Isolate Unmatched Transfers ---
        unmatched_mask = (df['Category'] == 'Transfer') & (df['ReconciliationID'].isna())
        unmatched_df = df[unmatched_mask].copy()

        if unmatched_df.empty:
            print("\n✅ Success! No unmatched transfer transactions were found.")
            return

        print(f"\nFound {len(unmatched_df)} unmatched 'Transfer' transactions. Analyzing by account...")

        # --- Create Summaries for Debits and Credits ---
        credits = unmatched_df[unmatched_df['Amount'] > 0]
        debits = unmatched_df[unmatched_df['Amount'] < 0]

        credit_summary = credits.groupby('Account')['Amount'].agg(
            Credit_Count='count',
            Unmatched_Credits='sum'
        ).reset_index()

        debit_summary = debits.groupby('Account')['Amount'].agg(
            Debit_Count='count',
            Unmatched_Debits='sum'
        ).reset_index()

        # --- Merge Summaries for a Final Report ---
        summary_df = pd.merge(credit_summary, debit_summary, on='Account', how='outer').fillna(0)
        summary_df[['Credit_Count', 'Debit_Count']] = summary_df[['Credit_Count', 'Debit_Count']].astype(int)
        summary_df['Net_Unreconciled'] = summary_df['Unmatched_Credits'] + summary_df['Unmatched_Debits']

        print("\n--- Unmatched Transfer Summary ---")
        print(summary_df.to_string(index=False))

        # --- ADDED: Detailed breakdown of US Bank Checking debits ---
        us_bank_debits = debits[debits['Account'] == 'US Bank Checking']
        if not us_bank_debits.empty:
            print("\n\n--- Breakdown of Unmatched Debits from US Bank Checking ---")
            
            # Use a copy to avoid SettingWithCopyWarning
            us_bank_debits_copy = us_bank_debits.copy()
            us_bank_debits_copy['Simple_Description'] = us_bank_debits_copy['Description'].str.extract(r'([A-Z\s]+)')[0].str.strip()

            debit_breakdown = us_bank_debits_copy.groupby('Simple_Description')['Amount'].agg(
                Count='count',
                Total_Amount='sum'
            ).sort_values(by='Total_Amount').reset_index()

            print(debit_breakdown.to_string(index=False))
        # --- END ADDED SECTION ---
        
        print("\n\n--- Analysis ---")
        print("This report shows the total value of transfer payments that could not be paired.")
        print(" - A large positive 'Net_Unreconciled' value suggests missing debit transactions (e.g., missing checking statements).")
        print(" - A large negative 'Net_Unreconciled' value suggests missing credit transactions (e.g., missing credit card statements or a polarity issue).")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    investigate_unmatched_transfers()

