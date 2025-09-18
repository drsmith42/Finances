import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"

def summarize_transaction_sources():
    """
    Reads the master transaction file and generates a summary report
    showing the count of transactions from each unique source file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Transaction Source Auditor ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...\n")

        if 'Source' not in df.columns:
            print("❌ ERROR: The master file does not have a 'Source' column.")
            return

    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Core Logic ---
    # Use value_counts() to get a series of unique sources and their counts
    source_counts = df['Source'].value_counts().reset_index()
    source_counts.columns = ['Source_File', 'Transaction_Count']

    print("--- Summary of Transactions by Source File ---")
    
    # Use to_string() for better formatting and to ensure all rows are shown
    print(source_counts.to_string())

    print("\n" + "="*80)
    print("ACTION: Review the list above. If you see any raw, unprocessed filenames")
    print("(e.g., filenames that do not start with 'processed_'), it confirms")
    print("that the master file was built with incorrect data.")
    print("="*80)


if __name__ == "__main__":
    summarize_transaction_sources()
