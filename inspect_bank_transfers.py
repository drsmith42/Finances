import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"
# Keywords to find in the bank statement's description
SEARCH_KEYWORDS = ['VENMO', 'AMEX', 'DISCOVER', 'CHASE', 'WELLS FARGO', 'TARGET']

def inspect_bank_side_transfers():
    """
    A diagnostic tool to inspect the status of outgoing payments from the
    primary checking account to other accounts within the master file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Bank Transfer Status Inspector ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...\n")

        if 'Reviewed' not in df.columns:
            df['Reviewed'] = False
        df['Reviewed'] = df['Reviewed'].fillna(False).astype(bool)
        df['Description'] = df['Description'].astype(str)
        df['Account'] = df['Account'].astype(str)

    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Core Logic ---
    search_pattern = '|'.join(SEARCH_KEYWORDS)

    # Find all outgoing payments from the checking account that are directed
    # to one of the other accounts we reconcile.
    relevant_transfers = df[
        (df['Account'].str.lower() == CHECKING_ACCOUNT_NAME.lower()) &
        (df['Description'].str.contains(search_pattern, case=False, na=False)) &
        (df['Amount'] < 0)
    ].copy()

    if relevant_transfers.empty:
        print(" -> No potential bank-side transfers were found in the master file.")
        return

    print("--- Status of Outgoing Payments from US Bank Checking ---")
    
    # Display the relevant columns for analysis
    print(relevant_transfers[['Date', 'Description', 'Amount', 'Category', 'Reviewed']].to_string())

    print("\n" + "="*80)
    print("ACTION: Look at the 'Reviewed' column.")
    print("If 'True' for Venmo payments, it confirms why they are being ignored.")
    print("="*80)


if __name__ == "__main__":
    inspect_bank_side_transfers()
