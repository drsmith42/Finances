import pandas as pd
import os

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"

def verify_reconciliation_links():
    """
    Audits the master transaction file to verify the integrity of all
    ReconciliationID links.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Reconciliation Link Verifier ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'ReconciliationID': 'object'})

        if 'ReconciliationID' not in df.columns or df['ReconciliationID'].isna().all():
            print("\n✅ No reconciliation links found to verify.")
            return

        # Isolate only the transactions that have been linked
        linked_df = df.dropna(subset=['ReconciliationID'])
        
        print(f"\nAuditing {len(linked_df['ReconciliationID'].unique())} unique reconciliation groups...")

        # Group by the ID to check each linked set
        grouped = linked_df.groupby('ReconciliationID')
        
        errors_found = 0
        
        for rec_id, group in grouped:
            # Check 1: Ensure each group has exactly two transactions (one debit, one credit)
            if len(group) != 2:
                print(f"\n❌ ERROR: Group '{rec_id}' has {len(group)} transactions instead of 2.")
                print(group[['Date', 'Account', 'Description', 'Amount']].to_string())
                errors_found += 1
                continue

            # Check 2: Ensure the amounts in the group sum to zero
            if not abs(group['Amount'].sum()) < 0.01:
                print(f"\n❌ ERROR: Group '{rec_id}' does not sum to zero. Net amount is {group['Amount'].sum():.2f}.")
                print(group[['Date', 'Account', 'Description', 'Amount']].to_string())
                errors_found += 1
                continue

            # Check 3: Ensure there is one positive and one negative transaction
            if not (any(group['Amount'] > 0) and any(group['Amount'] < 0)):
                print(f"\n❌ ERROR: Group '{rec_id}' does not have one credit and one debit.")
                print(group[['Date', 'Account', 'Description', 'Amount']].to_string())
                errors_found += 1
                continue

        if errors_found == 0:
            print("\n✅ Success! All reconciliation links are correctly paired and balanced.")
        else:
            print(f"\n--- Audit Complete: Found {errors_found} issue(s). ---")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    verify_reconciliation_links()
