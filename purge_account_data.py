import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"

def purge_account_data():
    """
    A utility to completely remove all transactions for a specified account
    from the master transaction file. This is a destructive operation and
    should be used carefully to clean up corrupted data before a fresh import.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Account Data Purge Tool ---")
    print("⚠️ WARNING: This script will permanently delete data from your master file.")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"\nMaster file loaded. Contains {len(df)} total transactions.")
        
        print("\nAvailable accounts in master file:")
        # Convert account column to string to prevent sorting errors and handle 'nan'
        accounts = sorted(df['Account'].astype(str).unique())
        for name in accounts:
            print(f"- {name}")

        account_to_purge = input("\nEnter the EXACT account name to purge: ").strip()

        # Check if the entered name is in the list of string-converted account names
        if account_to_purge not in accounts:
            print(f"❌ ERROR: Account '{account_to_purge}' not found in the master file.")
            return

        # --- Confirmation Steps ---
        confirm1 = input(f"Are you sure you want to delete all transactions for '{account_to_purge}'? (y/n): ").lower()
        if confirm1 != 'y':
            print("Operation cancelled.")
            return
            
        confirm2 = input("This action cannot be undone. Please type 'DELETE' to confirm: ").strip()
        if confirm2 != 'DELETE':
            print("Confirmation failed. Operation cancelled.")
            return

        # --- Core Logic ---
        initial_rows = len(df)
        
        # --- UPDATED: Special handling for 'nan' values ---
        if account_to_purge == 'nan':
            # Create a mask for rows where the 'Account' is null/NaN
            purge_mask = df['Account'].isna()
        else:
            # Create a mask for regular account names
            purge_mask = df['Account'] == account_to_purge
            
        num_to_purge = df[purge_mask].shape[0]

        if num_to_purge > 0:
            print(f"\nFound {num_to_purge} transaction(s) for account '{account_to_purge}'. Purging now...")
            
            # Keep only the rows that DO NOT match the mask
            df_cleaned = df[~purge_mask]
            
            final_rows = len(df_cleaned)
            print(f" -> Purging complete. {initial_rows} -> {final_rows} rows.")

            # Save the cleaned DataFrame back to the master file
            df_cleaned.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print(f"✅ Success! The file '{MASTER_FILE_PATH}' has been cleaned.")
        else:
            print("✅ No transactions found for the specified account. No changes made.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    purge_account_data()
    input("\nPress Enter to exit...")
