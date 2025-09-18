import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
ACCOUNT_TO_FIX = "Chase CC"
CATEGORY_TO_FIX = "Transfer"

def fix_payment_polarity():
    """
    A one-time utility to find specific transactions in the master file and
    correct their amount polarity from negative to positive. This is intended
    to fix credit card payments that were incorrectly recorded as debits.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Polarity Correction Utility ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded with {len(df)} transactions.")

        # --- Identify Transactions to Fix ---
        # Find transactions for the specific account and category that are incorrectly negative.
        fix_mask = (
            (df['Account'] == ACCOUNT_TO_FIX) &
            (df['Category'] == CATEGORY_TO_FIX) &
            (df['Amount'] < 0)
        )

        transactions_to_fix = df[fix_mask]

        if transactions_to_fix.empty:
            print("\n✅ No transactions matching the criteria were found. No changes needed.")
            return

        print(f"\nFound {len(transactions_to_fix)} transactions for '{ACCOUNT_TO_FIX}' that need their polarity flipped.")
        print("These appear to be payment credits that were recorded as negative values.")
        print("Example transaction to be fixed:")
        print(transactions_to_fix.head(1).to_string())

        confirm = input("\nDo you want to proceed with correcting these amounts? (y/n): ").lower()

        if confirm == 'y':
            # --- Apply the Correction ---
            # Use .loc with the mask to modify the original DataFrame safely.
            # .abs() ensures the amount becomes positive.
            df.loc[fix_mask, 'Amount'] = df.loc[fix_mask, 'Amount'].abs()

            # --- Save the Corrected File ---
            df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print(f"\n✅ Success! The polarity for {len(transactions_to_fix)} transaction(s) has been corrected in '{MASTER_FILE_PATH}'.")
        else:
            print("\nOperation cancelled. No changes were made.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    fix_payment_polarity()
