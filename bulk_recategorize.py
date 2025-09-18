import pandas as pd
import os

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
KEYWORD_TO_FIND = "VENMO"
NEW_CATEGORY = "Venmo Unsorted"

def main():
    """
    Finds all transactions containing a specific keyword and changes
    their category to a new, specified category.
    """
    print("--- Bulk Re-categorizer ---")
    
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        
        # Create a 'mask' to find all rows where the 'Description' contains the keyword (case-insensitive)
        mask = df['Description'].str.contains(KEYWORD_TO_FIND, case=False, na=False)
        
        # Count how many transactions will be changed
        count = mask.sum()
        
        if count == 0:
            print(f"No transactions found containing the keyword '{KEYWORD_TO_FIND}'. No changes made.")
            return
            
        print(f"Found {count} transactions containing '{KEYWORD_TO_FIND}'.")
        
        # Update the 'Category' for all matching transactions
        df.loc[mask, 'Category'] = NEW_CATEGORY
        
        # Save the modified DataFrame back to the master file
        df.to_csv(MASTER_FILE_PATH, index=False)
        
        print(f"✅ Success! {count} transactions have been re-categorized to '{NEW_CATEGORY}'.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()