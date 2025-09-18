import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
OUTPUT_FILE_PATH = "data_for_rules.csv"
COLUMNS_TO_EXPORT = ['Account', 'Description', 'Amount', 'Category']

def export_data_for_rule_generation():
    """
    Reads the master transaction file and exports a smaller, focused CSV
    containing only the columns needed for intelligent rule generation.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Rule Generation Data Exporter ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Found {len(df)} transactions.")

        # Check if all required columns exist in the master file
        missing_cols = [col for col in COLUMNS_TO_EXPORT if col not in df.columns]
        if missing_cols:
            print(f"❌ ERROR: The master file is missing the following required columns: {', '.join(missing_cols)}")
            return

        # --- Core Logic ---
        # Create a new DataFrame with only the specified columns
        df_export = df[COLUMNS_TO_EXPORT]
        
        # Save the new DataFrame to a CSV file
        df_export.to_csv(OUTPUT_FILE_PATH, index=False, encoding='utf-8-sig')

        print(f"\n✅ Success! Exported {len(df_export)} rows to '{OUTPUT_FILE_PATH}'.")
        print("   You can now upload this new file for analysis.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    export_data_for_rule_generation()
