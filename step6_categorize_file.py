import pandas as pd
import os
import google.generativeai as genai
import time
import sys
import json

# --- Configuration & Helper Functions ---
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
RULES_FILE_PATH = "rules.json"

def get_category_from_ai(description, amount, model, request_options):
    """Uses the Gemini model to categorize a transaction with an enhanced prompt and timeout."""
    transaction_type = "Income" if amount > 0 else "Expense/Transfer"
    prompt = f"""You are an expert financial categorization assistant. Your task is to analyze a transaction and select the single most appropriate category from the provided list. Follow these rules carefully:

1.  **Analyze the Transaction:**
    * Transaction Type: {transaction_type}
    * Transaction Description: "{description}"

2.  **Apply These Heuristics First:**
    * **Reimbursements:** If the transaction is income from 'ZELLE', 'VENMO', 'PAYPAL', or a person's name, it is likely a reimbursement. Categorize it as **'Income: Reimbursement'**.
    * **Transfers vs. Income:** Deposits from major banks like 'BANK OF AMERICA', 'CHASE', etc. are likely a **'Transfer'**.
    * **Credit Card Payments:** Payments made to credit cards (e.g., 'AMEX EPAYMENT', 'CHASE CREDIT CRD') are always a **'Transfer'**.
    * **Waived Fees/Refunds:** Transactions with 'WAIVED', 'REVERSAL', or 'REFUND' are not income. Categorize these as **'Transfer'**.
    * **Ambiguous Checks:** If the description is just 'CHECK', it must be **'NEEDS REVIEW'** unless a specific rule applies.

3.  **Select a Category:**
    * Choose the single best category from this list: {', '.join(CATEGORIES)}
    * Only return the category name.

Selected Category:"""
    try:
        response = model.generate_content(prompt, request_options=request_options)
        category = response.text.strip()
        return category if category in CATEGORIES else "NEEDS REVIEW"
    except Exception as e:
        print(f"  -> AI Error: {e}. Defaulting to 'NEEDS REVIEW'.")
        return "NEEDS REVIEW"

# --- Main Application Logic ---
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- File Categorizer ---")

    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key: raise KeyError
        genai.configure(api_key=api_key)

        input_path = input("Path to the file you want to categorize: ").strip().replace("'", "").replace('"', '')
        df = pd.read_csv(input_path)
        
        rules = {}
        if os.path.exists(RULES_FILE_PATH):
            with open(RULES_FILE_PATH, 'r') as f:
                rules = json.load(f)
        
    except (FileNotFoundError, KeyError) as e:
        print(f"\n❌ ERROR: Could not load a necessary file. Details: {e}")
        sys.exit(1)

    if 'Category' not in df.columns:
        df['Category'] = ''

    # --- Apply Rules ---
    print("\nApplying custom rules...")
    for index, row in df.iterrows():
        description = row.get('Item_Description', row.get('Description', ''))
        desc_upper = description.upper()
        for rule_key, category in rules.items():
            keyword, amount_condition = rule_key, None
            if '|' in rule_key:
                keyword, amount_str = rule_key.split('|', 1)
                amount_condition = float(amount_str)
            if keyword in desc_upper and (amount_condition is None or row.get('Amount', row.get('Item_Amount')) == amount_condition):
                df.loc[index, 'Category'] = category
                break
    
    # --- AI Categorization for the Rest ---
    needs_ai = df[df['Category'].isna() | (df['Category'] == '')].copy()
    if not needs_ai.empty:
        print(f"\nFound {len(needs_ai)} transactions that need AI categorization.")
        proceed = input("Do you wish to continue? (y/n): ").lower()
        if proceed == 'y':
            ai_model = genai.GenerativeModel('gemini-1.5-flash')
            request_options = {"timeout": 30}
            for index, row in needs_ai.iterrows():
                description = row.get('Item_Description', row.get('Description', ''))
                amount = row.get('Amount', row.get('Item_Amount', 0))
                
                print(f"  -> Sending to AI: '{description[:80]}...'")
                try:
                    category = get_category_from_ai(description, amount, ai_model, request_options)
                    df.loc[index, 'Category'] = category
                    print("     ... Success!")
                except Exception as e:
                    print(f"     ... ERROR on this transaction: {e}. Marking for review.")
                    df.loc[index, 'Category'] = 'NEEDS REVIEW'
                time.sleep(0.1)

    # --- Save the final, categorized file ---
    output_dir = os.path.dirname(input_path)
    base_name = os.path.basename(input_path)
    output_path = os.path.join(output_dir, f"categorized_{base_name}")
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Categorization complete. Your new file is ready at '{output_path}'.")

if __name__ == "__main__":
    main()