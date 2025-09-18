import pandas as pd
import os
import sys

# --- (Ensure the CATEGORIES list is the same as your other scripts) ---
CATEGORIES = [
    "Home: Rent", "Home: Utilities", "Home: Phone Bill", "Home: Laundry",
    "Auto & Transport: Car Loan", "Auto & Transport: Gasoline", "Auto & Transport: Insurance", "Auto & Transport: Fees & Registration", "Auto & Transport: Misc",
    "Food: Groceries", "Food: Restaurants",
    "Health & Wellness: Premiums", "Health & Wellness: Therapy", "Health & Wellness: Co-pays", "Health & Wellness: Prescriptions", "Health & Wellness: Other",
    "Child-Related: Afterschool", "Child-Related: Nanny", "Child-Related: Support", "Child-Related: Misc Expenses",
    "Fees & Subscriptions: Credit Card", "Fees & Subscriptions: Union Dues", "Fees & Subscriptions: Bank Fees", "Fees & Subscriptions: General", "Fees & Subscriptions: Work Subscriptions",
    "Shopping: Amazon (Unsorted)", "Shopping: Target (Unsorted)", "Shopping: General", "Shopping: Amazon Return",
    "Financial: Taxes", "Financial: Interest Paid",
    "Office: Expenses",
    "Entertainment & Travel: Vacation", "Entertainment & Travel: Entertainment",
    "Income: Paycheck", "Income: 1099", "Income: Disability", "Income: Investment", "Income: Reimbursement",
    "Misc Income: Ed's Dead", "Misc Income: Tax Man", "Misc Income: Misc Income",
    "Transfer", "Venmo Unsorted", "NEEDS RECONCILIATION", "NEEDS REVIEW", "NEEDS REVIEW (Bad Date)", "Orphan Groceries"
]

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Manual Transaction Categorizer ---")

    try:
        input_path = input("Path to the CSV file you want to categorize (e.g., unreconciled_amazon_charges.csv): ").strip().replace("'", "").replace('"', '')
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"\n❌ ERROR: File not found at '{input_path}'")
        sys.exit(1)

    categorized_rows = []
    
    for index, row in df.iterrows():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"--- Categorizing Transaction ({index + 1}/{len(df)}) ---")
        print(f"   Date: {row['Date']}")
        print(f" Amount: {row['Amount']:.2f}")
        print(f"   Description: {row['Description']}")
        print("--------------------------\n")
        
        for i, category in enumerate(CATEGORIES):
            print(f"  [{i+1}] {category}")
            
        try:
            choice = int(input("\nEnter the number for the correct category: "))
            row['Category'] = CATEGORIES[choice - 1]
            categorized_rows.append(row.to_dict())
        except (ValueError, IndexError):
            print("Invalid selection. Marking as NEEDS REVIEW.")
            row['Category'] = 'NEEDS REVIEW'
            categorized_rows.append(row.to_dict())
            
    df_categorized = pd.DataFrame(categorized_rows)
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "categorized_manual_charges.csv")
    df_categorized.to_csv(output_path, index=False)
    
    print(f"\n✅ Categorization complete. Saved to '{output_path}'.")

if __name__ == "__main__":
    main()