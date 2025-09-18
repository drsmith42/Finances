import pandas as pd
import os

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
# This keyword identifies the transactions that were incorrectly added.
# It should match the 'Source' column for those entries.
SOURCE_KEYWORD_TO_PURGE = "venmo" 

def purge_incorrect_venmo_entries():
    """
    A one-time utility to clean the master transaction file by removing
    all previously imported Venmo transactions. This is necessary to
    allow the reconciliation logic to run correctly on a clean slate.
    """
    print("--- Venmo Duplicate Purge Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded successfully. Contains {len(df)} total transactions.")

        # --- Core Logic ---
        # Ensure the 'Source' column exists and is of string type for matching
        if 'Source' not in df.columns:
            print("❌ ERROR: The master file does not have a 'Source' column. Cannot proceed.")
            return
        
        # Find all rows where the 'Source' column contains the keyword 'venmo'
        initial_rows = len(df)
        condition = df['Source'].str.contains(SOURCE_KEYWORD_TO_PURGE, case=False, na=False)
        
        num_to_purge = df[condition].shape[0]

        if num_to_purge > 0:
            print(f"Found {num_to_purge} incorrect Venmo transaction(s) to purge.")
            
            # Keep only the rows that DO NOT meet the condition
            df_cleaned = df[~condition]
            
            final_rows = len(df_cleaned)
            print(f" -> Purging transactions... {initial_rows} -> {final_rows} rows.")

            # Save the cleaned DataFrame back to the master file
            df_cleaned.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print(f"✅ Success! The file '{MASTER_FILE_PATH}' has been cleaned.")
            print("\nYou can now run the main 'step3_categorizer.py' script again.")
        else:
            print("✅ No incorrect Venmo transactions found to purge. Your file is already clean.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    purge_incorrect_venmo_entries()
