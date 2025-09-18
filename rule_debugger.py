import pandas as pd
import os
import sys
import json

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
RULES_FILE_PATH = "rules.json"

# --- Helper Functions (Copied from step4_review.py for consistency) ---

def load_rules():
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"rules": []}

def save_rules(rules):
    with open(RULES_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=4)

def check_condition(condition, row):
    if 'field' not in condition: return False
    field, operator, value = condition['field'], condition['operator'], condition['value']
    row_value = row.get(field)
    if pd.isna(row_value): return False
    
    row_value_upper = str(row_value).upper()
    value_upper = str(value).upper()

    if operator == 'contains': return value_upper in row_value_upper
    if operator == 'not_contains': return value_upper not in row_value_upper
    if operator == 'equals':
        if isinstance(row_value, float): return abs(row_value - float(value)) < 0.001
        return row_value_upper == value_upper
    return False

def evaluate_conditions(conditions, row):
    if 'all_of' in conditions: return all(evaluate_conditions(cond, row) for cond in conditions['all_of'])
    if 'any_of' in conditions: return any(evaluate_conditions(cond, row) for cond in conditions['any_of'])
    return check_condition(conditions, row)

def find_matching_rule(row, rules_data):
    for i, rule in enumerate(rules_data.get('rules', [])):
        if evaluate_conditions(rule['conditions'], row):
            return i, rule
    return None, None

# --- Main Debugger Logic ---

def debug_rules():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Rule Debugger & Conflict Resolver ---")

    if not os.path.exists(MASTER_FILE_PATH) or not os.path.exists(RULES_FILE_PATH):
        print(f"❌ ERROR: Make sure both '{MASTER_FILE_PATH}' and '{RULES_FILE_PATH}' exist.")
        return

    df = pd.read_csv(MASTER_FILE_PATH)
    rules_data = load_rules()

    # --- FIX: Made keywords more specific to avoid flagging legitimate electronic payments ---
    non_transfer_keywords = ['ATM WITHDRAWAL', 'CUSTOMER WITHDRAWAL', 'CASH REWARD', 'CASH BACK', 'REDEMPTION', 'CASHBACK BONUS']
    
    # Find transactions that are categorized as 'Transfer' but contain one of the keywords
    problem_mask = (df['Category'] == 'Transfer') & \
                   (df['Description'].str.upper().str.contains('|'.join(non_transfer_keywords), na=False))
    
    problem_transactions = df[problem_mask]

    if problem_transactions.empty:
        print("\n✅ No obvious rule conflicts found for cash/reward transactions.")
        return

    print(f"\nFound {len(problem_transactions)} transactions that may be miscategorized by a broad 'Transfer' rule.")
    
    processed_rules = set()

    for index, row in problem_transactions.iterrows():
        rule_index, matching_rule = find_matching_rule(row, rules_data)

        if rule_index is not None and rule_index not in processed_rules:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("--- Rule Conflict Found ---")
            print("\nThe following transaction:")
            print(f"  Description: {row['Description']}")
            print(f"  Amount: {row['Amount']:.2f}")
            print("\n...was incorrectly categorized as 'Transfer' by this rule:")
            print(json.dumps(matching_rule, indent=4))

            print("\nThis rule is likely too broad. How would you like to fix it?")
            print("  [1] Make rule more specific (recommended)")
            print("  [2] Delete this rule entirely")
            print("  [s] Skip and ignore this rule for now")
            
            choice = input("\nEnter your choice: ").strip().lower()

            if choice == '1':
                print("\nTo make the rule more specific, we will add a condition to EXCLUDE reward/withdrawal keywords.")
                confirm = input("Are you sure you want to modify this rule? (y/n): ").strip().lower()
                if confirm == 'y':
                    # This is a sophisticated fix: it wraps the existing conditions
                    # in an "all_of" and adds a new block of "not_contains" conditions.
                    new_conditions = {
                        "all_of": [
                            matching_rule['conditions'], # The original conditions
                            {
                                "all_of": [
                                    {"field": "Description", "operator": "not_contains", "value": keyword}
                                    for keyword in non_transfer_keywords
                                ]
                            }
                        ]
                    }
                    rules_data['rules'][rule_index]['conditions'] = new_conditions
                    save_rules(rules_data)
                    print(" -> Rule updated successfully!")
            
            elif choice == '2':
                confirm = input("Are you sure you want to PERMANENTLY DELETE this rule? (y/n): ").strip().lower()
                if confirm == 'y':
                    del rules_data['rules'][rule_index]
                    save_rules(rules_data)
                    print(" -> Rule deleted successfully!")

            processed_rules.add(rule_index) # Mark as processed so we don't ask again for the same rule

    print("\n--- Rule Debugging Complete ---")
    print("It's recommended to run the 'interactive_recategorizer.py' script again to fix the categories.")

if __name__ == "__main__":
    debug_rules()

