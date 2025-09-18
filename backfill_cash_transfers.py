import pandas as pd
import os
import sys
import hashlib
from datetime import datetime

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"
# --- FIX: Expanded keywords to find all types of cash withdrawals ---
WITHDRAWAL_KEYWORDS = ["CUSTOMER WITHDRAWAL", "ATM WITHDRAWAL"]

def backfill_cash_transfers():
    """
    A one-time utility to find all historical cash withdrawals, ensure they are
    categorized as transfers, and create any missing 'Cash' account deposits.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Cash Transfer Backfill Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...")

        # Prepare data for processing
        df['Description'] = df['Description'].astype(str)
        df['Category'] = df['Category'].astype(str)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')


    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Core Logic ---
    # Create a search pattern to find any of the withdrawal keywords
    search_pattern = '|'.join(WITHDRAWAL_KEYWORDS)
    condition = (
        (df['Account'] == CHECKING_ACCOUNT_NAME) &
        (df['Description'].str.contains(search_pattern, case=False, na=False))
    )
    # --- END FIX ---

    withdrawals_to_process = df[condition]
    
    if withdrawals_to_process.empty:
        print("\n✅ No historical cash withdrawals found.")
        return

    print(f"\nFound {len(withdrawals_to_process)} cash withdrawal(s) to process.")
    
    new_cash_transactions = []
    indices_to_update = []
    
    # Get a snapshot of existing cash deposits for checking against
    existing_cash_deposits = df[df['Account'] == 'Cash'].copy()
    if not existing_cash_deposits.empty:
        existing_cash_deposits['Amount'] = existing_cash_deposits['Amount'].abs()


    for index, row in withdrawals_to_process.iterrows():
        date = row['Date']
        amount = abs(row['Amount'])
        
        # Check if a corresponding cash deposit already exists
        match_exists = False
        if not existing_cash_deposits.empty:
            match_exists = not existing_cash_deposits[
                (existing_cash_deposits['Date'] == date) &
                (existing_cash_deposits['Amount'].round(2) == round(amount, 2))
            ].empty

        if match_exists:
            print(f" -> Skipping withdrawal on {date} for {amount:.2f}: Corresponding cash deposit already exists.")
            # Still ensure the original is marked as a transfer
            if row['Category'] != 'Transfer':
                indices_to_update.append(index)
            continue

        print(f" -> Processing withdrawal of {amount:.2f} on {date}...")
        
        # Mark the original withdrawal as a reviewed transfer
        indices_to_update.append(index)
        
        # Create the corresponding positive cash deposit
        description = "Cash Deposit from ATM"
        id_string = f"{date}{description}{amount}".encode()
        transaction_id = hashlib.md5(id_string).hexdigest()

        new_transaction = {
            'Date': date, 'Account': 'Cash', 'Description': description,
            'Payee': 'Cash', 'Amount': amount, 'Category': 'Transfer', 
            'Is_Tax_Deductible': False, 'Is_Reimbursable': False, 
            'Source': 'Automated Backfill', 'TransactionID': transaction_id, 
            'Reviewed': False # Mark as unreviewed so it appears in step4
        }
        new_cash_transactions.append(new_transaction)

    # Update the original withdrawal transactions
    if indices_to_update:
        df.loc[indices_to_update, 'Category'] = 'Transfer'
        df.loc[indices_to_update, 'Reviewed'] = True
        print(f"\nUpdated {len(indices_to_update)} withdrawal transaction(s) to 'Transfer'.")

    # Add the new cash deposit transactions
    if new_cash_transactions:
        new_df = pd.DataFrame(new_cash_transactions)
        df = pd.concat([df, new_df], ignore_index=True)
        print(f"Added {len(new_cash_transactions)} new 'Cash' deposit transaction(s).")

    # Save the updated master file
    if indices_to_update or new_cash_transactions:
        df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"\n✅ Success! Master file updated. It now contains {len(df)} transactions.")
        print("You can now run 'step4_review.py' to see the new unreviewed cash transfers.")
    else:
        print("\nNo changes were needed.")

if __name__ == "__main__":
    backfill_cash_transfers()
