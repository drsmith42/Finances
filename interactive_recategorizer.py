import pandas as pd
import os
import sys
import time

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
    "Expenses: Office",
    "Expenses: Work",
    "Entertainment & Travel: Vacation", "Entertainment & Travel: Entertainment",
    "Income: Paycheck", "Income: 1099", "Income: Disability", "Income: Investment", "Income: Reimbursement", "Income: Rewards",
    "Misc Income: Ed's Dead", "Misc Income: Tax Man", "Misc Income: Misc Income",
    "Non-Taxable Income: Rewards", # --- ADDED ---
    "Transfer", "Venmo Unsorted", "NEEDS RECONCILIATION", "NEEDS REVIEW",
    "Cash Spending"
]
# --- UPDATED: Added keywords for both cash and rewards ---
CASH_KEYWORDS = ['ATM WITHDRAWAL', 'CUSTOMER WITHDRAWAL']
REWARD_KEYWORDS = ['CASH BACK', 'REDEMPTION', 'REWARD']

def recategorize_non_payments():
    """
    Finds transactions in the 'Transfer' category that are not true
    inter-account transfers (e.g., ATM withdrawals, cashback rewards)
    and allows the user to interactively re-categorize them.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Interactive Re-Categorizer for Mismatched Transfers ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object'})

        # --- UPDATED: Expanded mask to find both types of miscategorized items ---
        cash_mask = df['Description'].str.contains('|'.join(CASH_KEYWORDS), case=False, na=False)
        reward_mask = df['Description'].str.contains('|'.join(REWARD_KEYWORDS), case=False, na=False)

        mask = (
            (df['Category'] == 'Transfer') &
            (df['ReconciliationID'].isna()) &
            (cash_mask | reward_mask)
        )
        transactions_to_review = df[mask].copy()
        # --- END UPDATE ---

        if transactions_to_review.empty:
            print("\n✅ No obvious cash withdrawals or rewards found in the unmatched 'Transfer' category.")
            return

        print(f"\nFound {len(transactions_to_review)} transactions that may be miscategorized as 'Transfer'.")
        
        indices_to_update = list(transactions_to_review.index)
        i = 0
        while i < len(indices_to_update):
            idx = indices_to_update[i]
            row = df.loc[idx]

            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"--- Reviewing Item {i + 1}/{len(indices_to_update)} ---")
            print(f"  Date: {row['Date']}")
            print(f"  Account: {row['Account']}")
            print(f"  Description: {row['Description']}")
            print(f"  Amount: {row['Amount']:.2f}")
            print(f"  Current Category: '{row['Category']}'\n")
            
            # --- UPDATED: Dynamic prompt based on keywords ---
            prompt_text = "This transaction appears to be"
            if any(keyword in row['Description'].upper() for keyword in CASH_KEYWORDS):
                prompt_text += " a cash withdrawal."
            elif any(keyword in row['Description'].upper() for keyword in REWARD_KEYWORDS):
                prompt_text += " a cashback reward."
            print(prompt_text)
            
            print("Please choose a new category:")
            for j, cat in enumerate(CATEGORIES):
                print(f"  [{j+1}] {cat}")
            
            print("\n  [s] Skip this item")
            print("  [q] Quit and Save Changes")

            choice_str = input("\nEnter category number, (s)kip, or (q)uit: ").strip().lower()

            if choice_str == 'q':
                break
            elif choice_str == 's':
                i += 1
                continue
            
            try:
                cat_choice = int(choice_str)
                if 1 <= cat_choice <= len(CATEGORIES):
                    chosen_category = CATEGORIES[cat_choice - 1]
                    df.loc[idx, 'Category'] = chosen_category
                    df.loc[idx, 'Reviewed'] = True # Mark as reviewed since it's been handled
                    print(f" -> Category updated to '{chosen_category}'.")
                    time.sleep(1)
                    i += 1
                else:
                    print("Invalid number.")
                    time.sleep(1)
            except ValueError:
                print("Invalid input. Please enter a number, 's', or 'q'.")
                time.sleep(1)
        
        # Save the updated file
        df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"\n✅ Master file saved. Processed {i} transaction(s).")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    recategorize_non_payments()


