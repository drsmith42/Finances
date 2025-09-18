import pandas as pd
import os

MASTER_FILE_PATH = "master_transactions.csv"

def view_data_samples():
    """
    Loads the master transaction file and displays the first 5 rows
    for each unique account.
    """
    print("--- Transaction Data Sampler ---")
    
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        
        if 'Account' not in df.columns:
            print("❌ ERROR: 'Account' column not found. Please run the data model upgrade script.")
            return

        # Find all unique accounts in the file
        accounts = df['Account'].unique()
        
        print(f"\nFound {len(accounts)} unique accounts. Displaying samples:\n")
        
        for account in accounts:
            print("="*60)
            print(f"ACCOUNT: {account}")
            print("="*60)
            
            # Filter for the current account and show the first 5 rows
            sample_df = df[df['Account'] == account].head(5)
            print(sample_df[['Date', 'Description', 'Amount', 'Category']].to_string())
            print("\n")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    view_data_samples()