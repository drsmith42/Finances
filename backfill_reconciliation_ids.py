import pandas as pd
import os
import sys
import uuid
from datetime import timedelta

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
DATE_MATCHING_WINDOW_DAYS = 5 # How many days apart can matching transfers be?

def backfill_reconciliation_ids():
    """
    A one-time utility to retroactively create explicit links between reconciled
    transfer transactions in the master file. It adds a 'ReconciliationID' column
    and populates it for matching debit/credit pairs.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Reconciliation ID Backfill Utility ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH, parse_dates=['Date'])
        print(f"✅ Master file loaded with {len(df)} transactions.")

        # --- Step 1: Add the new column if it doesn't exist ---
        if 'ReconciliationID' not in df.columns:
            print(" -> 'ReconciliationID' column not found. Adding it now.")
            df['ReconciliationID'] = pd.NA
        else:
            print(" -> 'ReconciliationID' column already exists.")

        # --- Step 2: Isolate and prepare transfer data ---
        transfers_df = df[df['Category'] == 'Transfer'].copy()
        unmatched_transfers = transfers_df[transfers_df['ReconciliationID'].isna()]

        if unmatched_transfers.empty:
            print("\n✅ No unreconciled transfers found. All transfers already have a ReconciliationID.")
            return

        print(f"\nFound {len(unmatched_transfers)} transfer transactions without a ReconciliationID.")
        
        credits = unmatched_transfers[unmatched_transfers['Amount'] > 0].copy().sort_values('Date').reset_index()
        debits = unmatched_transfers[unmatched_transfers['Amount'] < 0].copy().sort_values('Date').reset_index()

        print(f" -> Analyzing {len(credits)} credits and {len(debits)} debits.")

        # --- Step 3: Match pairs and assign IDs ---
        matched_count = 0
        
        # Iterate through the credits and look for a matching debit
        for credit_idx, credit_row in credits.iterrows():
            
            # Create a search window for dates
            min_date = credit_row['Date'] - timedelta(days=DATE_MATCHING_WINDOW_DAYS)
            max_date = credit_row['Date'] + timedelta(days=DATE_MATCHING_WINDOW_DAYS)
            
            # Find potential matches based on amount and date window
            potential_matches = debits[
                (debits['Amount'].round(2) == -round(credit_row['Amount'], 2)) &
                (debits['Date'].between(min_date, max_date))
            ]

            if not potential_matches.empty:
                # Get the first available match
                match_row = potential_matches.iloc[0]
                
                # Generate a unique Reconciliation ID
                rec_id = f"REC-{uuid.uuid4().hex[:12]}"
                
                # Get original DataFrame indices for the matched pair
                original_credit_idx = credit_row['index']
                original_debit_idx = match_row['index']
                
                # Update the main DataFrame with the new ID
                df.loc[original_credit_idx, 'ReconciliationID'] = rec_id
                df.loc[original_debit_idx, 'ReconciliationID'] = rec_id
                
                print(f" -> Matched credit of {credit_row['Amount']:.2f} on {credit_row['Date'].date()} with debit of {match_row['Amount']:.2f} on {match_row['Date'].date()}. ID: {rec_id}")
                
                # Remove the matched debit from the pool to prevent re-matching
                debits.drop(match_row.name, inplace=True)
                matched_count += 1
        
        # --- Step 4: Report and Save ---
        print(f"\n--- Summary ---")
        print(f"Matched {matched_count} pairs of transactions.")
        
        remaining_unmatched = len(unmatched_transfers) - (matched_count * 2)
        if remaining_unmatched > 0:
            print(f"⚠️ {remaining_unmatched} transfer transactions remain unmatched and may require manual review.")
        else:
            print("✅ All transfers were successfully paired.")
            
        df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"\nMaster file has been updated and saved to '{MASTER_FILE_PATH}'.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    backfill_reconciliation_ids()

