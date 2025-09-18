import pandas as pd
import os
import sys
from datetime import timedelta

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"

def audit_unbalanced_transfers():
    """
    Finds outgoing transfers from the main checking account that do not have a
    corresponding incoming transfer in another account, highlighting reconciliation failures.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Unbalanced Transfer Auditor ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...")

        # --- Data Preparation ---
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Category'] = df['Category'].fillna('Uncategorized')

    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Core Logic ---
    # Isolate all transfers
    transfers = df[df['Category'] == 'Transfer'].copy()

    # Separate into outgoing from checking and incoming to other accounts
    outgoing_from_checking = transfers[
        (transfers['Account'] == CHECKING_ACCOUNT_NAME) & (transfers['Amount'] < 0)
    ].copy()
    
    incoming_to_others = transfers[
        (transfers['Account'] != CHECKING_ACCOUNT_NAME) & (transfers['Amount'] > 0)
    ].copy()

    if outgoing_from_checking.empty:
        print("\nNo outgoing transfers found from the checking account to audit.")
        return

    print(f"\nFound {len(outgoing_from_checking)} outgoing transfers from '{CHECKING_ACCOUNT_NAME}'. Searching for matches...")

    unmatched_transfers = []

    for index, row in outgoing_from_checking.iterrows():
        date_min = row['Date'] - timedelta(days=5)
        date_max = row['Date'] + timedelta(days=5)
        amount_to_match = abs(row['Amount'])

        # Search for a matching incoming transfer
        match = incoming_to_others[
            (incoming_to_others['Amount'].round(2) == round(amount_to_match, 2)) &
            (incoming_to_others['Date'].between(date_min, date_max))
        ]

        if match.empty:
            unmatched_transfers.append(row)

    # --- Display the Report ---
    if not unmatched_transfers:
        print("\n✅ All outgoing transfers appear to be balanced with a corresponding incoming transfer.")
    else:
        print("\n" + "="*80)
        print("⚠️ WARNING: The following outgoing transfers could not be matched.")
        print("This is likely the cause of the imbalance in your summary report.")
        print("="*80)
        
        unmatched_df = pd.DataFrame(unmatched_transfers)
        unmatched_df['Date'] = unmatched_df['Date'].dt.strftime('%Y-%m-%d')
        print(unmatched_df[['Date', 'Account', 'Description', 'Amount']].to_string(index=False))

if __name__ == "__main__":
    audit_unbalanced_transfers()
