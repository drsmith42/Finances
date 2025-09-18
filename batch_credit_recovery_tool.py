import pandas as pd
import os
import sys
import re

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"

# Define which accounts to target in this batch run. Venmo is excluded.
ACCOUNTS_TO_RECOVER_MAP = {
    'AMEX': 'Amex CC',
    'Discover CC': 'Discover CC',
    'Target RedCard': 'Target RedCard',
    'Wells Fargo CC': 'Wells Fargo CC'
}

def get_simple_description(description):
    """Simplifies complex bank descriptions into a clean destination name."""
    if not isinstance(description, str):
        return "Unknown"
    
    patterns = {
        r'AMEX EPAYMENT': 'AMEX',
        r'CHASE CREDIT CRD': 'Chase CC',
        r'WELLS FARGO CARD': 'Wells Fargo CC',
        r'DISCOVER': 'Discover CC',
        r'TARGET CARD SRVC': 'Target RedCard',
        r'VENMO': 'Venmo'
    }
    
    for pattern, name in patterns.items():
        if re.search(pattern, description, re.IGNORECASE):
            return name
            
    return description

def batch_recover_credits():
    """
    Finds missing credit transactions by prompting for each source file individually
    and appends them in a single batch operation after user confirmation.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Batch Missing Credit Recovery Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df_master = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object', 'ReconciliationID': 'object'})
        
        # --- Identify all unmatched debits for the target accounts ---
        df_master_copy = df_master.copy()
        df_master_copy['Destination'] = df_master_copy['Description'].apply(get_simple_description)
        
        unmatched_debits_mask = (
            (df_master_copy['Account'] == CHECKING_ACCOUNT_NAME) &
            (df_master_copy['Category'] == 'Transfer') &
            (df_master_copy['ReconciliationID'].isna()) &
            (df_master_copy['Destination'].isin(ACCOUNTS_TO_RECOVER_MAP.keys()))
        )
        target_debits = df_master_copy[unmatched_debits_mask]
        target_amounts = set(abs(target_debits['Amount']).round(2))

        if not target_amounts:
            print("\nNo unmatched debits found for target accounts. Nothing to do.")
            return
            
        print(f"\nSearching for {len(target_amounts)} unique payment amounts across all target accounts...")

        # --- Search Source Files for Missing Transactions by Prompting for Each ---
        found_transactions = []
        existing_ids = set(df_master['TransactionID'])

        for simple_name, account_name in ACCOUNTS_TO_RECOVER_MAP.items():
            prompt = f"\nPlease provide the path for the processed '{account_name}' file (or press Enter to skip): "
            file_path = input(prompt).strip().replace("'", "").replace('"', '')

            if not file_path:
                continue
            
            if not os.path.exists(file_path):
                print(f" -> Warning: File not found at '{file_path}'. Skipping.")
                continue

            try:
                df_source = pd.read_csv(file_path)
                
                # Verify the file content matches the expected account
                source_account = df_source['Account'].iloc[0] if not df_source.empty else None
                if source_account != account_name:
                    print(f" -> Warning: The file provided for '{account_name}' seems to contain data for '{source_account}'. Skipping this file to be safe.")
                    continue

                df_source['Amount'] = pd.to_numeric(df_source['Amount'], errors='coerce')
                potential_matches = df_source[abs(df_source['Amount']).round(2).isin(target_amounts)]
                
                for index, row in potential_matches.iterrows():
                    if row['TransactionID'] not in existing_ids:
                        found_transactions.append(row)
            except Exception as e:
                print(f" -> Warning: Could not process file {os.path.basename(file_path)}. Error: {e}")

        # --- Confirm and Append ---
        if not found_transactions:
            print("\n❌ No missing transactions were found in the specified source files.")
            return

        df_to_append = pd.DataFrame(found_transactions).drop_duplicates(subset=['TransactionID'])
        print(f"\n✅ Found {len(df_to_append)} potentially missing transactions across all accounts:")
        print(df_to_append.sort_values(by=['Account', 'Date'])[['Date', 'Account', 'Description', 'Amount']].to_string())

        confirm = input("\nDo you want to add these transactions to your master file? (y/n): ").lower()
        if confirm == 'y':
            df_final = pd.concat([df_master, df_to_append], ignore_index=True)
            df_final.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print(f"\n✅ Success! Added {len(df_to_append)} transactions. Master file now has {len(df_final)} total transactions.")
            print("It's highly recommended to run the 'backfill_reconciliation_ids.py' script now to link these new credits.")
        else:
            print("\nOperation cancelled. No changes were made.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    batch_recover_credits()

