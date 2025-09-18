import pandas as pd
import json
import os
import sys
import time
import re
from datetime import datetime
import hashlib

# --- Configuration & Helper Functions ---
MASTER_FILE_PATH = "master_transactions.csv"
RULES_FILE_PATH = "rules.json"
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
# --- UPDATED: Added 'Duplicate_Ignored' to the master list of columns ---
MASTER_COLUMNS = [
    'Date', 'Account', 'Description', 'Payee', 'Amount', 'Category',
    'Is_Tax_Deductible', 'Is_Reimbursable', 'Source', 'TransactionID', 'Reviewed', 'Rule_Ignored', 'Duplicate_Ignored'
]

def load_rules():
    """Loads categorization rules from the JSON file with UTF-8 encoding."""
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"rules": []}

def save_rules(rules):
    """Saves categorization rules to the JSON file with UTF-8 encoding."""
    with open(RULES_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=4)

def check_condition(condition, row):
    """
    Checks if a single, simple condition is met by the transaction row.
    """
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
    """
    Recursively evaluates a block of conditions.
    """
    if 'all_of' in conditions:
        return all(evaluate_conditions(cond, row) for cond in conditions['all_of'])
    if 'any_of' in conditions:
        return any(evaluate_conditions(cond, row) for cond in conditions['any_of'])
    return check_condition(conditions, row)

def find_matching_rule(row, rules_data):
    """
    Finds the first rule that matches the transaction row.
    """
    for i, rule in enumerate(rules_data.get('rules', [])):
        if evaluate_conditions(rule['conditions'], row):
            return i, rule['category']
    return None, None

def apply_rules_and_rescan(df, rules_data, indices_to_scan=None):
    """Applies all rules to a specific scope of transactions, skipping ignored ones."""
    categorized_count = 0
    scan_indices = indices_to_scan if indices_to_scan is not None else df.index

    for index in scan_indices:
        if df.loc[index, 'Rule_Ignored']:
            continue
            
        row = df.loc[index]
        _, new_category = find_matching_rule(row, rules_data)
        
        if new_category and df.loc[index, 'Category'] != new_category:
            df.loc[index, 'Category'] = new_category
            df.loc[index, 'Reviewed'] = True
            categorized_count += 1
            
    return df, categorized_count


def review_transactions(df, indices_to_review, rules_data, category_name=None, rule_count=0):
    """The main loop for reviewing and editing a list of transactions."""
    i = 0
    rescan_requested = False
    original_indices = list(indices_to_review)

    while i < len(original_indices):
        idx = original_indices[i]
        
        if idx not in df.index:
            i += 1
            continue

        row = df.loc[idx]
        original_category = row['Category']

        os.system('cls' if os.name == 'nt' else 'clear')
        
        if category_name:
            print(f"--- Reviewing Category: {category_name} ({len(original_indices)} total, {rule_count} from rules) ---")
            print(f"--- Item {i + 1}/{len(original_indices)} ---")
        else:
            print(f"--- Reviewing Unreviewed Transactions ({i + 1}/{len(original_indices)}) ---")

        print(f"  Date: {row['Date']} | Account: {row.get('Account', 'N/A')}")
        print(f"  Payee: {row.get('Payee', 'N/A')}")
        print(f"  Description: {row['Description']}")
        print(f"  Amount: {row.get('Amount', 0.0):.2f}")
        print(f"  Current Category: '{row['Category']}'\n")
        
        print("OPTIONS:")
        print("  [c] Change Category  [e] Edit Details     [f] Flip Amount Sign")
        print("  [Enter] Skip (Approve) [b] Back             [d] Delete")
        print("  [q] Quit to Previous Menu")
        
        choice = input("\nEnter your choice: ").lower()

        if choice == 's' or choice == '':
            df.loc[idx, 'Reviewed'] = True
            i += 1
            continue
        elif choice == 'q':
            break
        elif choice == 'b':
            if i > 0:
                i -= 1
            else:
                print(" -> Already at the first item.")
                time.sleep(1)
            continue
        elif choice == 'd':
            confirm = input("Type 'DELETE' to permanently delete this transaction: ").strip()
            if confirm == 'DELETE':
                df.drop(idx, inplace=True)
                original_indices.pop(i)
                print(" -> Transaction deleted.")
                time.sleep(1)
                continue
            else:
                print(" -> Deletion cancelled.")
                time.sleep(1)
                continue
        elif choice == 'f':
            df.loc[idx, 'Amount'] = -df.loc[idx, 'Amount']
            print(" -> Amount sign flipped.")
            time.sleep(1)
            continue
        elif choice == 'e':
            new_date = input(f"  Edit Date ({row['Date']}) or press Enter: ").strip()
            if new_date: df.loc[idx, 'Date'] = new_date
            new_desc = input(f"  Edit Description ({row['Description']}) or press Enter: ").strip()
            if new_desc: df.loc[idx, 'Description'] = new_desc
            new_payee = input(f"  Edit Payee ({row['Payee']}) or press Enter: ").strip()
            if new_payee: df.loc[idx, 'Payee'] = new_payee
            new_amount = input(f"  Edit Amount ({row['Amount']}) or press Enter: ").strip()
            if new_amount:
                try: df.loc[idx, 'Amount'] = float(new_amount)
                except ValueError: print("Invalid amount. Keeping original.")
            print(" -> Details updated.")
            time.sleep(1)
            continue

        elif choice == 'c':
            for j, cat in enumerate(CATEGORIES):
                print(f"  [{j+1}] {cat}")
            
            cat_choice_str = input("\nEnter category number: ").lower()
            try:
                cat_choice = int(cat_choice_str)
                if 1 <= cat_choice <= len(CATEGORIES):
                    chosen_category = CATEGORIES[cat_choice - 1]
                    df.loc[idx, 'Category'] = chosen_category
                    
                    rule_index, rule_category = find_matching_rule(row, rules_data)
                    if rule_index is not None and rule_category == original_category and chosen_category != original_category:
                        print(f"\nWarning: This transaction was categorized by a rule.")
                        conflict_choice = input("Do you want to (o)verride & ignore future rules, (u)pdate the rule, or (d)elete the rule? ").lower()
                        if conflict_choice == 'u':
                            rules_data['rules'][rule_index]['category'] = chosen_category
                            save_rules(rules_data)
                            print(f" -> Rule updated.")
                        elif conflict_choice == 'd':
                            del rules_data['rules'][rule_index]
                            save_rules(rules_data)
                            print(f" -> Rule deleted.")
                        else:
                            df.loc[idx, 'Rule_Ignored'] = True
                            print(" -> Overriding category and ignoring future rules for this item.")
                    else:
                        create_rule = input("Create a rule for this? (y/n): ").lower()
                        if create_rule == 'y':
                            keyword_input = input("Enter keyword(s) separated by '&' (e.g., VENMO&PIZZA): ").strip().upper()
                            if keyword_input:
                                new_rule = {"category": chosen_category, "conditions": {"all_of": []}}
                                keywords = [k.strip() for k in keyword_input.split('&')]
                                for k in keywords:
                                    new_rule["conditions"]["all_of"].append({"field": "Description", "operator": "contains", "value": k})
                                
                                account_specific = input(f"Apply only to '{row.get('Account', 'N/A')}' account? (y/n): ").lower()
                                if account_specific == 'y':
                                    new_rule["conditions"]["all_of"].append({"field": "Account", "operator": "equals", "value": row.get('Account', '')})

                                amount_specific = input(f"Apply this rule only to the amount '{row.get('Amount', 0.0):.2f}'? (y/n): ").lower()
                                if amount_specific == 'y':
                                    new_rule["conditions"]["all_of"].append({"field": "Amount", "operator": "equals", "value": row.get('Amount', 0.0)})
                                
                                rules_data['rules'].append(new_rule)
                                save_rules(rules_data)
                                print(f" -> Rule created.")
                                
                                rescan = input("Re-scan items with new rule? (y/n): ").lower()
                                if rescan == 'y':
                                    rescan_requested = True
                                    break
                    
                    df.loc[idx, 'Reviewed'] = True
                    i += 1
                else:
                    print("Invalid category number.")
                    time.sleep(1)
            except ValueError:
                print("Invalid input.")
                time.sleep(1)
        else:
            print("Invalid choice.")
            time.sleep(1)
            
    return df, rules_data, rescan_requested

def add_manual_transaction(df):
    """Prompts the user for details and adds a new transaction to the DataFrame."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Add Manual Transaction ---")
    
    try:
        date_str = input("Enter Date (YYYY-MM-DD): ").strip()
        date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        account = input("Enter Account (e.g., Cash): ").strip()
        description = input("Enter Description: ").strip()
        
        amount_str = input("Enter Amount (use '-' for expenses): ").strip()
        amount = float(amount_str)

        print("\nSelect a Category:")
        for i, cat in enumerate(CATEGORIES):
            print(f"  [{i+1}] {cat}")
        cat_choice = int(input("\nEnter category number: "))
        category = CATEGORIES[cat_choice - 1]

        id_string = f"{date}{description}{amount}".encode()
        transaction_id = hashlib.md5(id_string).hexdigest()

        new_transaction = {
            'Date': date, 'Account': account, 'Description': description,
            'Payee': description.split('*')[0].strip().title(), 'Amount': amount,
            'Category': category, 'Is_Tax_Deductible': False,
            'Is_Reimbursable': False, 'Source': 'Manual Entry',
            'TransactionID': transaction_id, 'Reviewed': True, 'Rule_Ignored': False, 'Duplicate_Ignored': False
        }
        
        new_df = pd.DataFrame([new_transaction])
        df = pd.concat([df, new_df], ignore_index=True)
        print("\n✅ Transaction added successfully.")
        time.sleep(2)

    except (ValueError, IndexError):
        print("\n❌ Invalid input. Please try again.")
        time.sleep(2)
    
    return df

def review_potential_duplicates(df):
    """
    Finds and allows the user to manage potential duplicate transactions.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Find & Review Duplicates ---")
    
    df_to_scan = df[df['Duplicate_Ignored'] == False]
    
    duplicates = df_to_scan.groupby(['Date', 'Amount', 'Account']).filter(lambda x: len(x) >= 2)
    
    if duplicates.empty:
        print("No potential duplicate groups found.")
        time.sleep(2)
        return df

    unique_groups = duplicates[['Date', 'Amount', 'Account']].drop_duplicates().values.tolist()
    indices_to_delete = []

    for i, (date, amount, account) in enumerate(unique_groups):
        current_indices = df[(df['Date'] == date) & (df['Amount'] == amount) & (df['Account'] == account)].index
        
        if any(idx in indices_to_delete for idx in current_indices):
            continue

        group_df = df.loc[current_indices].copy()
        
        if len(group_df) < 2:
            continue

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"--- Reviewing Group {i + 1}/{len(unique_groups)} ---")
        print(f"Date: {date}, Amount: {amount:.2f}, Account: {account}\n")
        
        group_df['DisplayIndex'] = range(1, len(group_df) + 1)
        print(group_df[['DisplayIndex', 'Description', 'Category', 'Source']].to_string(index=False))
        
        choice = input("\nAction: [k]eep specific items, [i]gnore group forever, [s]kip for now, [q]uit and save: ").lower()

        if choice == 'q':
            break
        elif choice == 's':
            continue
        elif choice == 'i':
            for idx in group_df.index:
                df.loc[idx, 'Duplicate_Ignored'] = True
            print(" -> Group marked to be ignored in future scans.")
            time.sleep(1)
            continue
        elif choice == 'k':
            while True:
                try:
                    keep_input = input(f"Enter the number(s) of the transaction(s) to KEEP (1-{len(group_df)}), separated by commas: ").strip()
                    if not keep_input:
                        print("No selection made. Please enter at least one number.")
                        continue
                    
                    keep_choices = [int(x.strip()) for x in keep_input.split(',')]
                    
                    if all(1 <= choice <= len(group_df) for choice in keep_choices):
                        indices_to_keep = [group_df.index[choice - 1] for choice in keep_choices]
                        
                        for idx in group_df.index:
                            if idx not in indices_to_keep:
                                indices_to_delete.append(idx)
                        
                        print(f" -> Marked {len(group_df) - len(indices_to_keep)} transaction(s) for deletion.")
                        time.sleep(1)
                        break
                    else:
                        print("Invalid number entered. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter numbers separated by commas.")
                    time.sleep(1)

    if indices_to_delete:
        unique_indices_to_delete = list(set(indices_to_delete))
        print(f"\nDeleting {len(unique_indices_to_delete)} marked transaction(s)...")
        df.drop(unique_indices_to_delete, inplace=True)
        print("✅ Duplicates removed.")
    else:
        print("\nNo changes were made to the master file.")
    
    time.sleep(2)
    return df


def main():
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    df = pd.read_csv(MASTER_FILE_PATH, dtype={'Category': 'object'})
    rules = load_rules()
    
    if 'Reviewed' not in df.columns: df['Reviewed'] = False
    if 'Rule_Ignored' not in df.columns: df['Rule_Ignored'] = False
    if 'Duplicate_Ignored' not in df.columns: df['Duplicate_Ignored'] = False
    
    df['Reviewed'] = df['Reviewed'].fillna(False).astype(bool)
    df['Rule_Ignored'] = df['Rule_Ignored'].fillna(False).astype(bool)
    df['Duplicate_Ignored'] = df['Duplicate_Ignored'].fillna(False).astype(bool)
    df['Category'] = df['Category'].fillna('')

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- Transaction Review & Audit Tool ---")
        
        unreviewed_mask = (df['Reviewed'] == False) | (df['Category'] == '')
        unreviewed_count = len(df[unreviewed_mask])
        
        print(f"\n[1] Review Unreviewed Transactions ({unreviewed_count} remaining)")
        print("[2] Review by Specific Category")
        print("[3] Add Manual Transaction")
        print("[4] Find & Review Duplicates")
        print("[5] Quit and Save")
        
        main_choice = input("\nEnter your choice: ")

        if main_choice == '5':
            break
        elif main_choice == '1':
            while True:
                unreviewed_mask = (df['Reviewed'] == False) | (df['Category'] == '')
                review_indices = df[unreviewed_mask].index.tolist()
                
                if not review_indices:
                    print("No unreviewed transactions to show.")
                    time.sleep(2)
                    break
                df, rules, rescan_needed = review_transactions(df, review_indices, rules)
                if rescan_needed:
                    print("\nRe-scanning all unreviewed transactions with updated rules...")
                    df, categorized_count = apply_rules_and_rescan(df, rules)
                    print(f" -> {categorized_count} item(s) were automatically categorized.")
                    time.sleep(2)
                else:
                    break

        elif main_choice == '2':
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("--- Review by Category ---")
                for i, cat in enumerate(CATEGORIES):
                    print(f"  [{i+1}] {cat}")
                print("\n  [q] Back to Main Menu")
                
                cat_choice_str = input("\nSelect a category to review: ").lower()
                if cat_choice_str == 'q':
                    break

                try:
                    cat_choice = int(cat_choice_str)
                    if 1 <= cat_choice <= len(CATEGORIES):
                        chosen_cat = CATEGORIES[cat_choice - 1]
                        review_indices = df[df['Category'] == chosen_cat].index.tolist()
                        
                        if not review_indices:
                            print(f"No transactions found in category '{chosen_cat}'.")
                            time.sleep(2)
                            continue
                        
                        rule_count = 0
                        for idx in review_indices:
                            rule_key, _ = find_matching_rule(df.loc[idx], rules)
                            if rule_key is not None:
                                rule_count += 1
                        
                        df, rules, rescan_needed = review_transactions(df, review_indices, rules, category_name=chosen_cat, rule_count=rule_count)
                        
                        if rescan_needed:
                            print(f"\nRe-scanning all transactions in '{chosen_cat}' with updated rules...")
                            df, categorized_count = apply_rules_and_rescan(df, rules, indices_to_scan=review_indices)
                            print(f" -> {categorized_count} item(s) were re-categorized in this category.")
                            time.sleep(2.5)
                    else:
                        print("Invalid category number.")
                        time.sleep(1)
                except ValueError:
                    print("Invalid input.")
                    time.sleep(1)
        elif main_choice == '3':
            df = add_manual_transaction(df)
        elif main_choice == '4':
            df = review_potential_duplicates(df)
        else:
            print("Invalid choice.")
            time.sleep(1)

    # --- Safe Save Logic ---
    while True:
        try:
            df.to_csv(MASTER_FILE_PATH, index=False, encoding='utf-8-sig')
            print("\n✅ All changes have been saved to your master file!")
            break
        except PermissionError:
            print(f"\n❌ ERROR: Could not save to '{MASTER_FILE_PATH}'.")
            print("   The file is likely open in another program (like Excel).")
            input("   Please close the file and press Enter to try again...")
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during save: {e}")
            break

if __name__ == "__main__":
    main()
