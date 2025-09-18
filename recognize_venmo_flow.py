import pandas as pd
import os
import sys
import hashlib
from datetime import timedelta

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"
VENMO_ACCOUNT_NAME = "Venmo"
VENMO_FUNDING_CATEGORY = "Transfer: Venmo Funding"
VENMO_PAYMENT_DESCRIPTION = "WEB AUTHORIZED PMT VENMO"
VENMO_DEPOSIT_DESCRIPTION = "ELECTRONIC DEPOSIT VENMO"

def find_venmo_pass_through_matches(df_master):
    """Finds pass-through payments and links them to their funding source."""
    
    # 1. Isolate the two sets of transactions to match
    unmatched_funding = df_master[
        (df_master['Account'] == CHECKING_ACCOUNT_NAME) &
        (df_master['Description'] == VENMO_PAYMENT_DESCRIPTION) &
        (df_master['ReconciliationID'].isna()) &
        (df_master['Category'] == 'Transfer')
    ].copy()

    unlinked_expenses = df_master[
        (df_master['Account'] == VENMO_ACCOUNT_NAME) &
        (df_master['SourceTransactionID'].isna()) &
        (df_master['Amount'] < 0) &
        (df_master['Category'] != 'Transfer') # Exclude standard transfers
    ].copy()

    if unmatched_funding.empty or unlinked_expenses.empty:
        return df_master, 0

    # Ensure dates are in datetime format for comparison
    unmatched_funding['Date'] = pd.to_datetime(unmatched_funding['Date'])
    unlinked_expenses['Date'] = pd.to_datetime(unlinked_expenses['Date'])

    linked_count = 0
    
    # 2. Iterate through each funding transaction and look for a matching expense
    for fund_idx, fund_row in unmatched_funding.iterrows():
        fund_amount = fund_row['Amount']
        fund_date = fund_row['Date']
        
        # Look for a Venmo expense with the same amount within a 3-day window
        match = unlinked_expenses[
            (abs(unlinked_expenses['Amount'] - fund_amount) < 0.01) &
            (abs(unlinked_expenses['Date'] - fund_date).dt.days <= 3)
        ]
        
        if not match.empty:
            # Get the index of the first match
            expense_idx = match.index[0]
            
            # 3. Apply the link and update categories
            df_master.loc[expense_idx, 'SourceTransactionID'] = fund_row['TransactionID']
            df_master.loc[fund_idx, 'Category'] = VENMO_FUNDING_CATEGORY
            
            # Mark both as reviewed
            df_master.loc[expense_idx, 'Reviewed'] = True
            df_master.loc[fund_idx, 'Reviewed'] = True

            # Remove the matched expense so it can't be matched again
            unlinked_expenses.drop(expense_idx, inplace=True)
            linked_count += 1
            
    return df_master, linked_count


def reconcile_venmo_standard_transfers(df_master):
    """Reconciles standard transfers between Venmo and Checking using ReconciliationID."""
    
    venmo_withdrawals = df_master[
        (df_master['Account'] == VENMO_ACCOUNT_NAME) &
        (df_master['Description'] == "Venmo Withdrawal to Bank") &
        (df_master['ReconciliationID'].isna())
    ].copy()
    
    bank_deposits = df_master[
        (df_master['Account'] == CHECKING_ACCOUNT_NAME) &
        (df_master['Description'] == VENMO_DEPOSIT_DESCRIPTION) &
        (df_master['ReconciliationID'].isna())
    ].copy()

    if venmo_withdrawals.empty or bank_deposits.empty:
        return df_master, 0

    venmo_withdrawals['Date'] = pd.to_datetime(venmo_withdrawals['Date'])
    bank_deposits['Date'] = pd.to_datetime(bank_deposits['Date'])
    
    reconciled_count = 0

    for venmo_idx, venmo_row in venmo_withdrawals.iterrows():
        venmo_amount = venmo_row['Amount']
        venmo_date = venmo_row['Date']
        
        match = bank_deposits[
            (abs(bank_deposits['Amount'] + venmo_amount) < 0.01) &
            (abs(bank_deposits['Date'] - venmo_date).dt.days <= 3)
        ]
        
        if not match.empty:
            bank_idx = match.index[0]
            
            rec_id = f"REC-{hashlib.md5(str(venmo_row['TransactionID']).encode()).hexdigest()[:12]}"
            
            df_master.loc[venmo_idx, 'ReconciliationID'] = rec_id
            df_master.loc[bank_idx, 'ReconciliationID'] = rec_id
            
            df_master.loc[venmo_idx, 'Reviewed'] = True
            df_master.loc[bank_idx, 'Reviewed'] = True

            bank_deposits.drop(bank_idx, inplace=True)
            reconciled_count += 1

    return df_master, reconciled_count


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Venmo Reconciliation and Data Model Upgrade ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    df_master = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object', 'ReconciliationID': 'object'})

    # --- Step 1: Add new columns if they don't exist ---
    if 'SourceTransactionID' not in df_master.columns:
        df_master['SourceTransactionID'] = pd.NA
        print("\n-> Added 'SourceTransactionID' column to the master file.")
    
    # --- Step 2: Import any new Venmo transactions ---
    venmo_file_path = input("\nPlease provide the path to your 'processed_venmo...' file: ").strip().replace("'", "").replace('"', '')
    if os.path.exists(venmo_file_path):
        df_venmo = pd.read_csv(venmo_file_path)
        existing_ids = set(df_master['TransactionID'])
        new_venmo_tx = df_venmo[~df_venmo['TransactionID'].isin(existing_ids)]
        
        if not new_venmo_tx.empty:
            df_master = pd.concat([df_master, new_venmo_tx], ignore_index=True)
            print(f" -> Imported {len(new_venmo_tx)} new transactions from the Venmo file.")
    else:
        print(" -> Warning: Venmo file not found. Proceeding with existing data.")

    # --- Step 3: Link Pass-Through Payments ---
    print("\nAttempting to link pass-through Venmo payments to their funding source...")
    df_master, linked_count = find_venmo_pass_through_matches(df_master)
    if linked_count > 0:
        print(f"✅ Successfully linked {linked_count} pass-through payments and re-categorized their funding source.")
    else:
        print(" -> No new pass-through payments were linked.")

    # --- Step 4: Reconcile Standard Venmo Transfers ---
    print("\nAttempting to reconcile standard transfers (Venmo <-> Bank)...")
    df_master, reconciled_count = reconcile_venmo_standard_transfers(df_master)
    if reconciled_count > 0:
        print(f"✅ Successfully reconciled {reconciled_count} standard transfers.")
    else:
        print(" -> No new standard transfers were reconciled.")
        
    # --- Final Save ---
    try:
        df_master.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"\n✅ Success! Master file has been updated. It now contains {len(df_master)} transactions.")
    except Exception as e:
        print(f"\n❌ An error occurred while saving the master file: {e}")


if __name__ == "__main__":
    main()
