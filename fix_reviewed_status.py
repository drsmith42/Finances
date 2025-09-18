import pandas as pd
import os

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
DESCRIPTION_TO_FIX = "WEB AUTHORIZED PMT VENMO"

def fix_venmo_reviewed_status():
    """
    Finds specific Venmo bank transfers in the master transaction file
    that are marked as 'Reviewed' and resets their status to False.
    This allows the reconciliation script to process them correctly.
    """
    print("--- Venmo Reviewed Status Correction Tool ---")

    # Check if the master file exists
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        print("Please ensure the script is in the same directory as your master_transactions.csv.")
        return

    try:
        # Read the master CSV file into a pandas DataFrame
        df = pd.read_csv(MASTER_FILE_PATH)
        print("✅ Master file loaded successfully.")

        # --- Core Logic ---
        # Define the conditions for the rows we need to change:
        # 1. The 'Description' must exactly match our target string.
        # 2. The 'Reviewed' column must be True.
        condition = (df['Description'] == DESCRIPTION_TO_FIX) & (df['Reviewed'] == True)

        # Get the number of rows that will be changed
        num_to_fix = df[condition].shape[0]

        if num_to_fix > 0:
            print(f"Found {num_to_fix} transaction(s) with description '{DESCRIPTION_TO_FIX}' that need correction.")
            
            # Change the 'Reviewed' status from True to False for the matched rows
            df.loc[condition, 'Reviewed'] = False
            print(" -> Status successfully changed from True to False.")

            # Save the modified DataFrame back to the original CSV file
            # index=False prevents pandas from writing a new index column
            df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print(f"✅ Success! The file '{MASTER_FILE_PATH}' has been updated.")
            print("\nYou can now run the main 'step3_categorizer.py' script again.")
        else:
            print("✅ No corrections needed. All relevant Venmo transactions are already marked as not reviewed.")

    except KeyError as e:
        print(f"❌ ERROR: A required column is missing from the CSV file: {e}")
        print("Please ensure your master_transactions.csv has both 'Description' and 'Reviewed' columns.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    # --- THIS IS THE FIX ---
    # The function call now correctly matches the function definition above.
    fix_venmo_reviewed_status()
    # --- END OF FIX ---
