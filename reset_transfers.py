import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CHECKING_ACCOUNT_NAME = "US Bank Checking"
# Keywords that indicate a probable payment to another account
TRANSFER_KEYWORDS = [
    'CHASE', 'AMEX', 'WELLS FARGO', 'WF CREDIT', 'TARGET', 'DISCOVER'
]

def reset_miscategorized_transfers():
    """
    Scans the master file for transactions that look like inter-account
    transfers but are not categorized as such, and resets their 'Reviewed'
    status to False so they will appear in the review tool.
    """
    print("--- Miscategorized Transfer Reset Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...")

        if 'Reviewed' not in df.columns:
            df['Reviewed'] = True # Assume all are reviewed if column is missing
        df['Reviewed'] = df['Reviewed'].fillna(True).astype(bool)
        
        # Ensure description and category are strings for searching
        df['Description'] = df['Description'].astype(str)
        df['Category'] = df['Category'].astype(str)

    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    # --- Core Logic ---
    # Build a search pattern from our keywords. The `|` means OR.
    # `case=False` makes the search case-insensitive.
    search_pattern = '|'.join(TRANSFER_KEYWORDS)

    # Define the conditions for a transaction that needs to be reset:
    # 1. Must be from the specified checking account.
    # 2. Description must contain one of our keywords.
    # 3. Must NOT already be categorized as 'Transfer'.
    # 4. Must currently be marked as 'Reviewed' (True).
    condition = (
        (df['Account'] == CHECKING_ACCOUNT_NAME) &
        (df['Description'].str.contains(search_pattern, case=False, na=False)) &
        (df['Category'] != 'Transfer') &
        (df['Reviewed'] == True)
    )

    num_to_reset = df[condition].shape[0]

    if num_to_reset > 0:
        print(f"\nFound {num_to_reset} potential transfer(s) that need re-categorization.")
        
        # Set 'Reviewed' to False for all matching rows
        df.loc[condition, 'Reviewed'] = False
        
        df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"✅ Success! {num_to_reset} transaction(s) have been marked as unreviewed.")
        print("You can now run 'step4_review.py' to correct them.")
    else:
        print("\n✅ No miscategorized transfers found that need review.")

if __name__ == "__main__":
    reset_miscategorized_transfers()
