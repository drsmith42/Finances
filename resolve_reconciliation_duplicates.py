import pandas as pd
import os
import sys

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"

def resolve_reconciliation_duplicates():
    """
    Finds and helps resolve duplicate transactions that share the same ReconciliationID.
    This is for cases where one debit might have been linked to multiple credits.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Reconciliation ID Duplicate Resolution Tool ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object', 'ReconciliationID': 'object'})
        if 'ReconciliationID' not in df.columns:
            print(" -> 'ReconciliationID' column not found. Nothing to audit.")
            return

        # --- Isolate transactions that have a ReconciliationID ---
        df_reconciled = df.dropna(subset=['ReconciliationID']).copy()

        if df_reconciled.empty:
            print("\n✅ No reconciled transactions found to audit.")
            return

        # Group by the ID and filter for any group that has more than two transactions.
        # A correct group should only ever have two (one debit, one credit).
        duplicate_groups = df_reconciled.groupby('ReconciliationID').filter(lambda x: len(x) > 2)

        if duplicate_groups.empty:
            print("\n✅ No duplicate groups found. All ReconciliationIDs are correctly paired.")
            return

        print(f"\nFound {len(duplicate_groups)} transactions in groups with more than 2 members. Please review.")
        
        unique_groups = duplicate_groups.groupby('ReconciliationID')
        indices_to_delete = []
        
        # --- Interactive Review Loop ---
        for i, (rec_id, group_df) in enumerate(unique_groups):
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"--- Reviewing Group {i+1}/{len(unique_groups)} ---")
            print(f"ReconciliationID: {rec_id}\n")
            
            # Separate the debits and credits for clarity
            debit_side = group_df[group_df['Amount'] < 0]
            credit_side = group_df[group_df['Amount'] > 0]

            print("--- DEBIT (Payment Source) ---")
            print(debit_side[['Date', 'Account', 'Description', 'Amount', 'Source']].to_string(index=False))
            
            print("\n--- CREDITS (Potential Duplicates) ---")
            display_credits = credit_side[['Date', 'Description', 'Source']].copy()
            display_credits['Option'] = range(1, len(display_credits) + 1)
            print(display_credits[['Option', 'Date', 'Description', 'Source']].to_string(index=False))

            while True:
                try:
                    keep_input = input("\nEnter the Option number for the single CREDIT to KEEP (or 's' to skip): ").strip().lower()
                    if keep_input == 's':
                        break

                    if not keep_input:
                        print(" -> Please enter one number.")
                        continue

                    keep_choice = int(keep_input)
                    
                    if 1 <= keep_choice <= len(display_credits):
                        index_to_keep = credit_side.index[keep_choice - 1]
                        
                        for idx in credit_side.index:
                            if idx != index_to_keep:
                                indices_to_delete.append(idx)
                        
                        print(f" -> Marked {len(credit_side) - 1} credit transaction(s) for deletion.")
                        break
                    else:
                        print(" -> Invalid number entered. Please try again.")

                except ValueError:
                    print(" -> Invalid input. Please enter a single number.")
        
        # --- Final Deletion Step ---
        if indices_to_delete:
            print("\n--- Summary ---")
            print(f"You have marked {len(indices_to_delete)} transaction(s) for deletion.")
            confirm = input("Type 'DELETE' to permanently remove these transactions: ").strip()
            
            if confirm == 'DELETE':
                df.drop(indices_to_delete, inplace=True)
                df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
                print(f"\n✅ Success! Removed {len(indices_to_delete)} duplicates. Master file updated.")
            else:
                print("\nOperation cancelled. No changes were made.")
        else:
            print("\nNo transactions were marked for deletion.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    resolve_reconciliation_duplicates()
