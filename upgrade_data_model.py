import pandas as pd
import os
import re

MASTER_FILE_PATH = "master_transactions.csv"

def get_clean_payee(description):
    """A helper function to make a best guess at a clean payee name."""
    # This can be improved over time with more specific rules
    if not isinstance(description, str):
        return ""
    # Remove common extra details
    payee = re.split(r'\s{2,}|[*#@]| \d{3,}', description)[0].strip()
    return payee.title()

def main():
    """
    Upgrades the master file to the new, more powerful data model, adding
    Account, Payee, and flag columns.
    """
    print("--- Upgrading Master File to New Data Model ---")
    
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    df = pd.read_csv(MASTER_FILE_PATH)

    # --- 1. Add 'Account' Column (if it doesn't exist) ---
    if 'Account' not in df.columns:
        print("Adding 'Account' column...")
        account_mapping = {
            'US Bank Checking': ['Checking - 6055'],
            'Chase CC': ['chasecredit'],
            'Wells Fargo CC': ['WellsFargo', 'WF Credit Card'],
            'Amex CC': ['amex', 'activity'],
            'Discover CC': ['Discover']
        }
        df['Account'] = 'Unassigned'
        for account_name, keywords in account_mapping.items():
            for keyword in keywords:
                mask = df['Source'].str.contains(keyword, case=False, na=False)
                df.loc[mask, 'Account'] = account_name
    else:
        print("'Account' column already exists.")

    # --- 2. Add 'Payee' Column (if it doesn't exist) ---
    if 'Payee' not in df.columns:
        print("Adding 'Payee' column with best-guess names...")
        df['Payee'] = df['Description'].apply(get_clean_payee)
    else:
        print("'Payee' column already exists.")

    # --- 3. Add Flag Columns (if they don't exist) ---
    if 'Is_Tax_Deductible' not in df.columns:
        print("Adding 'Is_Tax_Deductible' column...")
        df['Is_Tax_Deductible'] = False
    if 'Is_Reimbursable' not in df.columns:
        print("Adding 'Is_Reimbursable' column...")
        df['Is_Reimbursable'] = False

    # --- Save the Upgraded File ---
    df.to_csv(MASTER_FILE_PATH, index=False)
    
    print("\n✅ Upgrade complete! Your master_transactions.csv is now using the new data model.")

if __name__ == "__main__":
    main()