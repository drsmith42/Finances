import pandas as pd
import os
from datetime import timedelta

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
DATE_WINDOW_DAYS = 5

def debug_unmatched_pairs():
    """
    Analyzes unmatched transfers to find potential pairs that failed automatic
    reconciliation and explains why (e.g., date window too large).
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Unmatched Transfer Pair Debugger ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'ReconciliationID': 'object'})
        df['Date'] = pd.to_datetime(df['Date'], format='mixed')

        if 'ReconciliationID' not in df.columns:
            print(" -> 'ReconciliationID' column not found. Nothing to debug.")
            return

        # --- Isolate all un-reconciled 'Transfer' transactions ---
        unmatched_mask = (df['Category'] == 'Transfer') & (df['ReconciliationID'].isna())
        unmatched_transfers = df[unmatched_mask].copy()

        if unmatched_transfers.empty:
            print("\n✅ No un-reconciled transfers found to debug.")
            return

        unmatched_debits = unmatched_transfers[unmatched_transfers['Amount'] < 0].copy()
        unmatched_credits = unmatched_transfers[unmatched_transfers['Amount'] > 0].copy()

        print(f"\nAnalyzing {len(unmatched_debits)} debits and {len(unmatched_credits)} credits...")
        print("-" * 30)

        found_issues = 0

        # --- Logic to find near-misses ---
        for _, debit in unmatched_debits.iterrows():
            debit_amount = debit['Amount']
            debit_date = debit['Date']
            target_credit_amount = -debit_amount

            # Search for credits with the exact opposite amount, regardless of date
            potential_matches = unmatched_credits[
                abs(unmatched_credits['Amount'] - target_credit_amount) < 0.01
            ]

            if not potential_matches.empty:
                for _, credit in potential_matches.iterrows():
                    credit_date = credit['Date']
                    day_diff = abs((debit_date - credit_date).days)
                    
                    # If the date difference is the reason for the failure, report it
                    if day_diff > DATE_WINDOW_DAYS:
                        found_issues += 1
                        print(f"INFO: Found an amount match for a debit on {debit_date.date()} ({debit_amount:.2f} in '{debit['Account']}').")
                        print(f"      -> Corresponding credit is on {credit_date.date()} ({credit['Amount']:.2f} in '{credit['Account']}').")
                        print(f"      ❗️ FAILED because dates are {day_diff} days apart (limit is {DATE_WINDOW_DAYS}).")
                        print("-" * 30)
            else:
                found_issues += 1
                print(f"INFO: No amount match found for debit on {debit_date.date()} ({debit_amount:.2f} in '{debit['Account']}').")
                print(f"      -> Looking for a credit of {target_credit_amount:.2f}.")
                print("-" * 30)

        if found_issues == 0:
            print("\n✅ All unmatched transfers appear to have no corresponding transaction.")
        else:
            print(f"\n--- Debug Complete: Found {found_issues} potential issue(s). ---")
            print("To fix date-related issues, you can manually edit the date of one of the transactions in `step4_review.py`.")


    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    debug_unmatched_pairs()
