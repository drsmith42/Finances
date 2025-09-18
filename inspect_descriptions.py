import pandas as pd

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
ACCOUNT_TO_INSPECT = "US Bank Checking"

def inspect_account_descriptions():
    """
    Reads the master transaction file and prints unique descriptions
    for a specific account to help identify search keywords.
    """
    print(f"--- Inspecting Unique Descriptions for Account: '{ACCOUNT_TO_INSPECT}' ---")

    try:
        df_master = pd.read_csv(MASTER_FILE_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'. Please ensure the file exists.")
        return
    except Exception as e:
        print(f"❌ An unexpected error occurred while reading the file: {e}")
        return

    # Clean the 'Account' column to remove potential leading/trailing spaces
    if 'Account' not in df_master.columns:
        print("❌ ERROR: The master file does not have an 'Account' column.")
        return
        
    df_master['Account'] = df_master['Account'].str.strip()
    
    # Filter for the specific account
    account_df = df_master[df_master['Account'].str.lower() == ACCOUNT_TO_INSPECT.lower()]

    if account_df.empty:
        print(f"\n❌ No transactions found for account '{ACCOUNT_TO_INSPECT}'.")
        print("\nPlease check if the account name is spelled correctly.")
        print("\nAvailable accounts in master file are:")
        for name in df_master['Account'].unique():
            print(f"- {name}")
    else:
        print("\nFound the following unique descriptions for this account:")
        
        if 'Description' not in account_df.columns:
            print("❌ ERROR: The filtered data does not have a 'Description' column.")
            return

        unique_descriptions = account_df['Description'].dropna().unique()
        
        if len(unique_descriptions) == 0:
            print(" -> No descriptions were found for this account.")
        else:
            for desc in sorted(unique_descriptions):
                print(f"- {desc}")
        
        print("\n--------------------------------------------------------------------")
        print("ACTION: Look through this list for the description your bank uses")
        print("for payments to Venmo, then report that keyword back to me.")
        print("--------------------------------------------------------------------")


if __name__ == "__main__":
    inspect_account_descriptions()