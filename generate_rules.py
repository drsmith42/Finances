import pandas as pd
import json
import os
import sys
import re
import time

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
RULES_FILE_PATH = "rules.json"
# Words to ignore when generating rule keywords
COMMON_WORDS = {'THE', 'A', 'AN', 'OF', 'IN', 'FOR', 'ON', 'AT', 'TO', 'AND', 'PMT', 'PYMT'}

def load_rules():
    """Loads categorization rules from the JSON file."""
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_rules(rules):
    """Saves categorization rules to the JSON file."""
    with open(RULES_FILE_PATH, 'w') as f:
        json.dump(rules, f, indent=4, sort_keys=True)

def find_matching_rule(row, rules):
    """Checks if a transaction matches any existing rule."""
    desc_upper = str(row.get('Description', '')).upper()
    account_upper = str(row.get('Account', '')).upper()
    amount = row.get('Amount', 0.0)

    for rule_key, category in rules.items():
        rule_account, rule_keywords_str = None, rule_key
        amount_condition = None

        if "|AMOUNT=" in rule_keywords_str:
            rule_keywords_str, amount_str = rule_keywords_str.split("|AMOUNT=", 1)
            try:
                amount_condition = float(amount_str)
            except ValueError:
                continue

        if "ACCOUNT=" in rule_keywords_str:
            parts = rule_keywords_str.split('&', 1)
            rule_account = parts[0].replace('ACCOUNT=', '').strip().upper()
            rule_keywords_str = parts[1] if len(parts) > 1 else ''
        
        if rule_account and rule_account != account_upper:
            continue

        keywords = [k.strip().upper() for k in rule_keywords_str.split('&') if k.strip()]
        
        if all(k in desc_upper for k in keywords):
            if amount_condition is None or amount == amount_condition:
                return rule_key, category
            
    return None, None

def suggest_keywords(description):
    """Intelligently suggests keywords from a transaction description."""
    words = re.split(r'[^A-Z0-9]+', str(description).upper())
    suggested = [word for word in words if word and word not in COMMON_WORDS and not word.isdigit() and len(word) > 2]
    return '&'.join(suggested[:3])

def count_rule_matches(df, rule_key, rules):
    """Counts how many transactions in the DataFrame match a specific new rule."""
    match_count = 0
    # Temporarily add the new rule to check its impact
    temp_rules = rules.copy()
    
    # Deconstruct the rule key once to be efficient
    rule_account, rule_keywords_str = None, rule_key
    amount_condition = None

    if "|AMOUNT=" in rule_keywords_str:
        rule_keywords_str, amount_str = rule_keywords_str.split("|AMOUNT=", 1)
        try: amount_condition = float(amount_str)
        except ValueError: return 0 # Invalid rule

    if "ACCOUNT=" in rule_keywords_str:
        parts = rule_keywords_str.split('&', 1)
        rule_account = parts[0].replace('ACCOUNT=', '').strip().upper()
        rule_keywords_str = parts[1] if len(parts) > 1 else ''
    
    keywords = [k.strip().upper() for k in rule_keywords_str.split('&') if k.strip()]

    # Iterate through the DataFrame to count matches
    for index, row in df.iterrows():
        desc_upper = str(row.get('Description', '')).upper()
        account_upper = str(row.get('Account', '')).upper()
        amount = row.get('Amount', 0.0)

        if rule_account and rule_account != account_upper:
            continue
        
        if all(k in desc_upper for k in keywords):
            if amount_condition is None or amount == amount_condition:
                match_count += 1
                
    return match_count

def main():
    """Main function to analyze the master file and interactively generate new rules."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Intelligent Rule Generator ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    df = pd.read_csv(MASTER_FILE_PATH)
    rules = load_rules()
    print(f"✅ Master file and {len(rules)} existing rules loaded.")

    # --- NEW: Main loop to allow for re-scanning ---
    while True:
        # Find transactions that are NOT covered by an existing rule
        rows_to_analyze_indices = []
        for index, row in df.iterrows():
            if pd.notna(row['Category']) and row['Category'] not in ['NEEDS REVIEW', '']:
                 rule_key, _ = find_matching_rule(row, rules)
                 if not rule_key:
                     rows_to_analyze_indices.append(index)
        
        if not rows_to_analyze_indices:
            print("\n✅ All categorized transactions are now covered by existing rules!")
            break

        print(f"\nFound {len(rows_to_analyze_indices)} transaction(s) needing rules.")
        
        rescan_requested = False
        # --- Interactive Rule Creation Loop ---
        for i, index in enumerate(rows_to_analyze_indices):
            row = df.loc[index]
            
            # Check again in case a new rule from this session now covers this item
            if find_matching_rule(row, rules)[0]:
                continue

            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"--- Suggesting Rule for Transaction {i + 1}/{len(rows_to_analyze_indices)} ---")
            
            print(f"  Description: {row['Description']}")
            print(f"  Account: {row['Account']}")
            print(f"  Amount: {row['Amount']:.2f}")
            print(f"  Category: {row['Category']}")

            suggested_keywords = suggest_keywords(row['Description'])
            print(f"\nSuggested keywords: '{suggested_keywords}'")

            choice = input("[a]ccept, [e]dit, [s]kip, [q]uit & save: ").lower()

            if choice == 'q':
                rescan_requested = False # Ensure we exit the outer loop
                break
            elif choice == 's':
                continue
            
            final_keywords = ""
            if choice == 'a':
                final_keywords = suggested_keywords
            elif choice == 'e':
                final_keywords = input("Enter desired keywords separated by '&': ").strip().upper()

            if final_keywords:
                rule_key = final_keywords
                
                account_specific = input(f"Apply this rule only to the '{row['Account']}' account? (y/n): ").lower()
                if account_specific == 'y':
                    rule_key = f"ACCOUNT={row['Account'].upper()}&{rule_key}"

                amount_specific = input(f"Apply this rule only to the amount '{row['Amount']:.2f}'? (y/n): ").lower()
                if amount_specific == 'y':
                    rule_key = f"{rule_key}|AMOUNT={row['Amount']:.2f}"
                
                rules[rule_key] = row['Category']
                print(f" -> Rule created: '{rule_key}' -> '{row['Category']}'")
                
                rescan = input("Apply this new rule and re-scan? (y/n): ").lower()
                if rescan == 'y':
                    match_count = count_rule_matches(df, rule_key, rules)
                    print(f" -> This new rule matches {match_count} transaction(s) in your master file.")
                    time.sleep(2.5)
                    rescan_requested = True
                    break # Exit inner loop to trigger the rescan
                else:
                    time.sleep(1.5)
        
        if not rescan_requested:
            break # Exit outer loop if we finished the inner loop

    save_rules(rules)
    print("\n✅ All new rules have been saved to 'rules.json'!")

if __name__ == "__main__":
    main()
