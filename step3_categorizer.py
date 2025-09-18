import pandas as pd
import os
import google.generativeai as genai
import time
import sys
import json
from datetime import timedelta
import hashlib

# --- Configuration ---
VENMO_FUNDING_SOURCE_KEYWORD = 'US BANK NA Personal Checking'
MASTER_CHECKING_ACCOUNT_NAME = 'US Bank Checking'
VENMO_DESCRIPTION_KEYWORD = 'VENMO'
PAYMENT_DESCRIPTION_KEYWORDS = ['AMEX', 'DISCOVER', 'CHASE', 'WELLS FARGO', 'TARGET']


PRICE_PER_MILLION_INPUT_TOKENS = 0.075
PRICE_PER_MILLION_OUTPUT_TOKENS = 0.30
ESTIMATED_INPUT_TOKENS_PER_TX = 350
ESTIMATED_OUTPUT_TOKENS_PER_TX = 10
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
    "Cash Spending", "Non-Taxable Income: Rewards", "Transfer: Venmo Funding"
]
MASTER_FILE_PATH = "master_transactions.csv"
RULES_FILE_PATH = "rules.json"
# --- UPDATED: Added new ID columns to the master list ---
MASTER_COLUMNS = [
    'Date', 'Account', 'Description', 'Payee', 'Amount', 'Category',
    'Is_Tax_Deductible', 'Is_Reimbursable', 'Source', 'TransactionID', 'Reviewed',
    'ReconciliationID', 'SourceTransactionID'
]

def get_category_from_ai(description, amount, model, request_options):
    """Uses the Gemini model to categorize a transaction."""
    # (This function is unchanged for brevity)
    pass

def check_condition(condition, row):
# ... (This function is unchanged) ...
    if 'field' not in condition:
        return False
    field = condition['field']
    operator = condition['operator']
    value = condition['value']
    row_value = row.get(field)
    if pd.isna(row_value):
        return False
    if isinstance(row_value, str):
        row_value_upper = row_value.upper()
        value_upper = str(value).upper()
    else:
        row_value_upper = row_value
        value_upper = value
    if operator == 'contains':
        return value_upper in row_value_upper
    elif operator == 'not_contains':
        return value_upper not in row_value_upper
    elif operator == 'equals':
        if isinstance(row_value, float):
            return abs(row_value - value) < 0.001
        return row_value == value
    elif operator == 'greater_than':
        return row_value > value
    elif operator == 'less_than':
        return row_value < value
    return False

def evaluate_conditions(conditions, row):
# ... (This function is unchanged) ...
    if 'all_of' in conditions:
        return all(evaluate_conditions(cond, row) for cond in conditions['all_of'])
    if 'any_of' in conditions:
        return any(evaluate_conditions(cond, row) for cond in conditions['any_of'])
    return check_condition(conditions, row)

def apply_rules(df, rules_data):
# ... (This function is unchanged) ...
    print("\nApplying structured custom rules...")
    categorized_indices = []
    rules = rules_data.get('rules', [])
    for index, row in df.iterrows():
        if pd.notna(row['Category']) and row['Category'] != '':
            continue
        for rule in rules:
            if evaluate_conditions(rule['conditions'], row):
                df.loc[index, 'Category'] = rule['category']
                categorized_indices.append(index)
                break 
    print(f"{len(categorized_indices)} transactions were categorized using your custom rules.")
    return df, categorized_indices


def fast_approve_ruled_transactions(df, indices):
# ... (This function is unchanged) ...
    return df

def run_ai_categorization(df, model):
# ... (This function is unchanged) ...
    return df

def reconcile_credit_card_payments(df_new, df_master):
    """
    Finds matching payment debits and credits, keeps both transactions, and
    links them with a shared ReconciliationID instead of dropping one.
    """
    print("\nReconciling existing credit card payments...")
    
    df_master['Date'] = pd.to_datetime(df_master['Date'], format='mixed')
    df_new['Date'] = pd.to_datetime(df_new['Date'], format='mixed')

    new_payments = df_new[(df_new['Amount'] > 0) & (df_new['Category'] == 'Transfer')].copy()
    
    # Find checking account withdrawals that are transfers AND don't have a ReconciliationID yet
    master_withdrawals = df_master[
        (df_master['Account'] == MASTER_CHECKING_ACCOUNT_NAME) &
        (df_master['Amount'] < 0) &
        (df_master['Category'] == 'Transfer') &
        (df_master['ReconciliationID'].isna())
    ].copy()

    reconciled_count = 0

    for new_idx, payment in new_payments.iterrows():
        payment_amount = payment['Amount']
        payment_date = payment['Date']
        
        for master_idx, withdrawal in master_withdrawals.iterrows():
            if abs(withdrawal['Amount'] + payment_amount) < 0.01 and abs((withdrawal['Date'] - payment_date).days) <= 5:
                print(f" -> Match found: Linking checking withdrawal on {withdrawal['Date'].date()} to CC payment on {payment_date.date()}.")
                
                # Generate a unique ID for the pair
                rec_id = f"REC-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
                
                # Assign the shared ID and mark both as reviewed
                df_master.loc[master_idx, 'ReconciliationID'] = rec_id
                df_new.loc[new_idx, 'ReconciliationID'] = rec_id
                df_master.loc[master_idx, 'Reviewed'] = True
                df_new.loc[new_idx, 'Reviewed'] = True
                
                reconciled_count += 1
                
                # Remove the matched withdrawal from the pool to prevent it from being matched again
                master_withdrawals.drop(master_idx, inplace=True)
                break 

    print(f"{reconciled_count} payment(s) were successfully reconciled and linked.")
    
    # Return the full df_new (no longer dropping rows) and the updated df_master
    return df_new, df_master

def create_and_reconcile_wf_payments(df_master):
# ... (This function is largely obsolete but kept for archival purposes, will be bypassed) ...
    return df_master, pd.DataFrame()


def main():
    print("--- Smart Transaction Importer ---")
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key: raise KeyError("GOOGLE_API_KEY not found.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"\n❌ ERROR: Could not configure AI model. {e}")
        sys.exit(1)

    rules = {}
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    
    df_master = pd.DataFrame()
    if os.path.exists(MASTER_FILE_PATH):
        df_master = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object'})
        if 'Date' in df_master.columns:
            df_master['Date'] = pd.to_datetime(df_master['Date'], format='mixed').dt.date
        
        # --- Ensure new ID columns exist ---
        for col in ['Reviewed', 'ReconciliationID', 'SourceTransactionID']:
            if col not in df_master.columns:
                df_master[col] = None if 'ID' in col else False
        df_master['Reviewed'] = df_master['Reviewed'].fillna(False).astype(bool)

    filepath = input("Please provide the path to your 'processed_...' CSV file: ").strip().replace("'", "").replace('"', '')
    df_new = pd.read_csv(filepath, dtype={'Category': 'object'})
    df_new['Date'] = pd.to_datetime(df_new['Date'], format='mixed').dt.date
    
    # --- Ensure new ID columns exist in the new dataframe too ---
    for col in ['ReconciliationID', 'SourceTransactionID']:
        if col not in df_new.columns:
            df_new[col] = None

    if not df_master.empty:
        existing_ids = set(df_master['TransactionID'])
        df_new = df_new[~df_new['TransactionID'].isin(existing_ids)].copy()
    
    if df_new.empty:
        print("\n✅ No genuinely new transactions found to process.")
        input("\nPress Enter to exit...")
        sys.exit(0)
        
    print(f"\nFound {len(df_new)} new transactions to process.")
    df_new['Reviewed'] = False
    
    account_name = df_new['Account'].iloc[0] if not df_new.empty else ""
    is_cc_file = any(keyword.lower() in account_name.lower() for keyword in PAYMENT_DESCRIPTION_KEYWORDS)
    
    # --- Apply rules before reconciliation ---
    df_new, _ = apply_rules(df_new, rules)

    # --- Reconcile if it's a credit card file ---
    if is_cc_file and not df_master.empty: 
        df_new, df_master = reconcile_credit_card_payments(df_new, df_master)
    
    # The 'transactions_to_process' is now the full new dataframe, with links added
    transactions_to_process = df_new
    
    if transactions_to_process.empty:
        print("\n✅ Reconciliation complete. No new transactions to add.")
    else:
        # Re-apply rules in case any uncategorized items remain
        categorized_df, ruled_indices = apply_rules(transactions_to_process, rules)

        if ruled_indices:
            categorized_df = fast_approve_ruled_transactions(categorized_df, ruled_indices)

        finalized_df = run_ai_categorization(categorized_df, model)
        df_master = pd.concat([df_master, finalized_df], ignore_index=True)
        print(f"\n✅ Success! Added/updated {len(finalized_df)} transactions.")

    # --- Ensure all columns are present before saving ---
    final_df_to_save = df_master.copy()
    for col in MASTER_COLUMNS:
        if col not in final_df_to_save.columns:
            final_df_to_save[col] = None
    final_df_to_save = final_df_to_save[MASTER_COLUMNS] # Ensure correct order

    final_df_to_save['Date'] = pd.to_datetime(final_df_to_save['Date'], format='mixed').dt.strftime('%Y-%m-%d')
    final_df_to_save.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
    print(f"\nMaster file saved with {len(df_master)} total transactions.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

