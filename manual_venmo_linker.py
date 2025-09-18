import pandas as pd
import os
import sys
from datetime import timedelta
import hashlib

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
CATEGORIES = [
    "Home: Rent", "Home: Utilities", "Home: Phone Bill", "Home: Laundry",
    "Auto & Transport: Car Loan", "Auto & Transport: Gasoline", "Auto & Transport: Insurance", "Auto & Transport: Fees & Registration", "Auto & Transport: Misc",
    "Food: Groceries", "Food: Restaurants", "Food: Booze",
    "Health & Wellness: Premiums", "Health & Wellness: Therapy", "Health & Wellness: Co-pays", "Health & Wellness: Prescriptions", "Health & Wellness: Other",
    "Child-Related: Afterschool", "Child-Related: Nanny", "Child-Related: Support", "Child-Related: Misc Expenses",
    "Fees & Subscriptions: Credit Card", "Fees & Subscriptions: Union Dues", "Fees & Subscriptions: Bank Fees", "Fees & Subscriptions: General", "Fees & Subscriptions: Work Subscriptions",
    "Shopping: Amazon (Unsorted)", "Shopping: Target (Unsorted)", "Shopping: General", "Shopping: Amazon Return",
    "Financial: Taxes", "Financial: Interest Paid",
    "Expenses: Office", "Expenses: Work",
    "Entertainment & Travel: Vacation", "Entertainment & Travel: Entertainment",
    "Income: Paycheck", "Income: 1099", "Income: Disability", "Income: Investment", "Income: Reimbursement",
    "Misc Income: Ed's Dead", "Misc Income: Tax Man", "Misc Income: Misc Income",
    "Transfer", "Venmo Unsorted", "NEEDS RECONCILIATION", "NEEDS REVIEW",
    "Cash Spending", "Non-Taxable Income: Rewards"
]

def get_clean_payee(description):
    if not isinstance(description, str): return ""
    return description.split('*')[0].strip().title()

def create_transaction_id(row):
    data_string = f"{row['Date']}{row['Description']}{row['Amount']:.2f}{row['Account']}"
    return hashlib.md5(data_string.encode()).hexdigest()

def manual_venmo_linker():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Manual Venmo Pass-Through Payment Linker ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    df_master = pd.read_csv(MASTER_FILE_PATH)
    
    venmo_path = input("Please provide the path to your 'processed_venmo...' file: ").strip().replace("'", "").replace('"', '')
    if not os.path.exists(venmo_path):
        print(f"❌ ERROR: Venmo file not found at '{venmo_path}'.")
        return

    df_venmo = pd.read_csv(venmo_path)
    df_venmo['Date'] = pd.to_datetime(df_venmo['Date'])

    # --- Isolate unmatched Venmo payments from the bank ---
    unmatched_mask = (df_master['Account'] == 'US Bank Checking') & \
                     (df_master['Description'].str.contains("VENMO", na=False)) & \
                     (df_master['Category'] == 'Transfer') & \
                     (df_master['ReconciliationID'].isna())
    
    unmatched_debits = df_master[unmatched_mask].copy()
    unmatched_debits['Date'] = pd.to_datetime(unmatched_debits['Date'])

    if unmatched_debits.empty:
        print("\n✅ No unmatched Venmo payments found in the master file.")
        return

    new_venmo_transactions = []
    indices_to_update = {}

    for index, debit in unmatched_debits.iterrows():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"--- Reviewing Bank Debit ({unmatched_debits.index.get_loc(index) + 1}/{len(unmatched_debits)}) ---")
        print(f"Date: {debit['Date'].date()} | Amount: {debit['Amount']:.2f} | Description: {debit['Description']}")
        
        # --- FIX: Widened the date range to +/- 5 days ---
        start_date = debit['Date'] - timedelta(days=5)
        end_date = debit['Date'] + timedelta(days=5)
        
        potential_matches = df_venmo[
            (df_venmo['Date'] >= start_date) & 
            (df_venmo['Date'] <= end_date) & 
            (df_venmo['Amount'] < 0)
        ].copy()

        if potential_matches.empty:
            print("\n -> No potential Venmo expenses found within 3 days.")
            input("Press Enter to skip to the next item...")
            continue
            
        potential_matches['DisplayIndex'] = range(1, len(potential_matches) + 1)
        print("\n--- Potential Matching Venmo Expenses ---")
        print(potential_matches[['DisplayIndex', 'Date', 'Description', 'Amount']].to_string(index=False))

        while True:
            choice_str = input("\nEnter number(s) to link (comma-separated), 's' to skip, or 'q' to quit: ").strip().lower()
            if choice_str == 'q':
                break
            if choice_str == 's':
                break

            try:
                choices = [int(c.strip()) for c in choice_str.split(',')]
                selected_rows = potential_matches[potential_matches['DisplayIndex'].isin(choices)]

                if len(selected_rows) != len(choices):
                    print(" -> Invalid number detected. Please try again.")
                    continue

                total_selected_amount = selected_rows['Amount'].sum()
                
                # --- FIX: Corrected the comparison logic from '+' to '-' ---
                if abs(total_selected_amount - debit['Amount']) > 0.01:
                    print(f" -> Mismatch! Selected total is {total_selected_amount:.2f}. Does not match debit of {debit['Amount']:.2f}.")
                    continue
                
                # --- Match Found ---
                print("\nSelect a category for this expense:")
                for i, cat in enumerate(CATEGORIES):
                    print(f"  [{i+1}] {cat}")
                
                cat_choice = int(input("\nEnter category number: "))
                chosen_category = CATEGORIES[cat_choice - 1]

                for _, row in selected_rows.iterrows():
                    new_tx = {
                        'Date': row['Date'].strftime('%Y-%m-%d'),
                        'Account': 'Venmo',
                        'Description': row['Description'],
                        'Payee': get_clean_payee(row.get('Payee', row['Description'])),
                        'Amount': row['Amount'],
                        'Category': chosen_category,
                        'Is_Tax_Deductible': False,
                        'Is_Reimbursable': False,
                        'Source': os.path.basename(venmo_path),
                        'Reviewed': True,
                        'SourceTransactionID': debit['TransactionID']
                    }
                    new_tx['TransactionID'] = create_transaction_id(new_tx)
                    new_venmo_transactions.append(new_tx)

                indices_to_update[index] = 'Transfer: Venmo Funding'
                df_venmo.drop(selected_rows.index, inplace=True) # Prevent re-matching
                print(" -> Match logged successfully.")
                break

            except (ValueError, IndexError):
                print(" -> Invalid input. Please enter a valid number or command.")
        
        if choice_str == 'q':
            break

    # --- Final Update ---
    if new_venmo_transactions:
        print("\nUpdating master file with new Venmo transactions and links...")
        new_df = pd.DataFrame(new_venmo_transactions)
        df_master = pd.concat([df_master, new_df], ignore_index=True)
        
        for idx, new_cat in indices_to_update.items():
            df_master.loc[idx, 'Category'] = new_cat
            df_master.loc[idx, 'Reviewed'] = True
        
        df_master.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"\n✅ Success! Added {len(new_venmo_transactions)} new Venmo transactions and updated {len(indices_to_update)} bank transactions.")
    else:
        print("\nNo changes were made to the master file.")

if __name__ == "__main__":
    manual_venmo_linker()

