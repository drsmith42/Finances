import pandas as pd
import os

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
PROCESSED_VENMO_FILE_PATH = "" # User will provide this
MASTER_CHECKING_ACCOUNT_NAME = 'US Bank Checking'
# --- FIX: Using a more specific keyword to isolate payments from deposits ---
VENMO_PAYMENT_KEYWORD = 'WEB AUTHORIZED PMT VENMO'
VENMO_FUNDING_SOURCE_KEYWORD = 'US BANK NA Personal Checking'
ROW_LIMIT = 15 # Number of rows to display from each file

def inspect_data_side_by_side():
    """
    A diagnostic tool that first forces a correction on the 'Reviewed' status
    of Venmo bank PAYMENTS and then displays data from both files for comparison.
    """
    print("--- Reconciliation Data Inspector (with Auto-Fix) ---")

    # --- Load Master File and Auto-Fix ---
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df_master = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object'})
        
        # --- Auto-Fix Logic ---
        print("\nStep 1: Automatically correcting 'Reviewed' status for bank payments...")
        if 'Reviewed' not in df_master.columns:
            df_master['Reviewed'] = False
        df_master['Reviewed'] = df_master['Reviewed'].fillna(False).astype(bool)

        # --- FIX: Condition now specifically targets the payment description ---
        fix_condition = (
            (df_master['Account'].str.strip().str.lower() == MASTER_CHECKING_ACCOUNT_NAME.lower()) &
            (df_master['Description'].str.strip() == VENMO_PAYMENT_KEYWORD) &
            (df_master['Reviewed'] == True)
        )
        num_to_fix = df_master[fix_condition].shape[0]

        if num_to_fix > 0:
            df_master.loc[fix_condition, 'Reviewed'] = False
            print(f" -> ✅ Corrected {num_to_fix} payment transaction(s) from 'Reviewed = True' to 'False'.")
        else:
            print(" -> ✅ No corrections needed. All relevant bank payments are already marked for review.")
        
        # --- Filtering Logic (post-fix) ---
        master_matches = df_master[
            (df_master['Account'].str.strip().str.lower() == MASTER_CHECKING_ACCOUNT_NAME.lower()) &
            (df_master['Description'].str.strip() == VENMO_PAYMENT_KEYWORD) &
            (df_master['Reviewed'] == False)
        ].copy()
        
        master_matches['Date'] = pd.to_datetime(master_matches['Date']).dt.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Load Venmo File and Filter ---
    print("\nStep 2: Loading and filtering the processed Venmo file...")
    venmo_path = input("Please provide the path to your 'processed_venmo_combined.csv' file: ").strip().replace("'", "").replace('"', '')
    if not os.path.exists(venmo_path):
        print(f"❌ ERROR: Venmo file not found at '{venmo_path}'.")
        return
        
    try:
        df_venmo = pd.read_csv(venmo_path, dtype={'Category': 'object'})
        df_venmo['Funding_Source'] = df_venmo['Funding_Source'].astype(str).str.strip()
        
        venmo_matches = df_venmo[
            df_venmo['Funding_Source'].str.contains(VENMO_FUNDING_SOURCE_KEYWORD, na=False, case=False)
        ].copy()

        venmo_matches['Date'] = pd.to_datetime(venmo_matches['Date']).dt.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"❌ An error occurred while processing the Venmo file: {e}")
        return

    # --- Display Results ---
    print("\n" + "="*80)
    print(f"Displaying up to {ROW_LIMIT} potential matches from MASTER file...")
    print("="*80)
    if master_matches.empty:
        print(" -> No un-reviewed Venmo payments found in the master file after auto-fix.")
    else:
        print(master_matches[['Date', 'Description', 'Amount', 'Reviewed']].head(ROW_LIMIT).to_string())


    print("\n" + "="*80)
    print(f"Displaying up to {ROW_LIMIT} bank-funded transactions from VENMO file...")
    print("="*80)
    if venmo_matches.empty:
        print(" -> No transactions funded by the specified bank account found in the Venmo file.")
    else:
        print(venmo_matches[['Date', 'Description', 'Amount', 'Funding_Source']].head(ROW_LIMIT).to_string())
    
    print("\n" + "="*80)
    print("ACTION: Compare the 'Date' and 'Amount' columns above.")
    print("="*80)


if __name__ == "__main__":
    inspect_data_side_by_side()
