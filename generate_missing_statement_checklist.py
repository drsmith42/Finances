import pandas as pd
import os
import sys
import re

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"

def get_simple_description(description):
    """Simplifies complex bank descriptions into a clean destination name."""
    if not isinstance(description, str):
        return "Unknown"
    
    # Use regex to find common patterns and extract the key vendor
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
            
    return description # Return the original if no pattern matches

def generate_checklist():
    """
    Analyzes unmatched debits from the primary checking account and generates a
    checklist of potentially missing statements, grouped by destination and month.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Missing Statement Checklist Generator ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object', 'ReconciliationID': 'object'})
        
        # Ensure the Date column is in datetime format for monthly grouping
        df['Date'] = pd.to_datetime(df['Date'])

        # --- Isolate Unmatched Debits from Checking ---
        unmatched_debits_mask = (
            (df['Account'] == CHECKING_ACCOUNT_NAME) &
            (df['Category'] == 'Transfer') &
            (df['ReconciliationID'].isna()) &
            (df['Amount'] < 0)
        )
        df_unmatched = df[unmatched_debits_mask].copy()

        if df_unmatched.empty:
            print("\n✅ No unmatched checking account debits found. Nothing to report.")
            return

        print(f"\nAnalyzing {len(df_unmatched)} unmatched payments from '{CHECKING_ACCOUNT_NAME}'...\n")

        # --- Prepare Data for Reporting ---
        df_unmatched['Month'] = df_unmatched['Date'].dt.strftime('%Y-%m')
        df_unmatched['Destination'] = df_unmatched['Description'].apply(get_simple_description)

        # --- Generate the Checklist ---
        checklist = df_unmatched.groupby(['Destination', 'Month'])['Amount'].sum().reset_index()
        
        print("--- Missing Statement Checklist ---")
        print("Based on payments from US Bank Checking, you may be missing statements for:\n")

        current_destination = ""
        for index, row in checklist.sort_values(by=['Destination', 'Month']).iterrows():
            if row['Destination'] != current_destination:
                current_destination = row['Destination']
                print(f"\n{current_destination}:")
            
            print(f" - {row['Month']}: {row['Amount']:,.2f}")
        
        print("\n" + "="*40)
        print("Please locate the corresponding credit card or Venmo statements for these months")
        print("and process them to reconcile these payments.")


    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_checklist()
