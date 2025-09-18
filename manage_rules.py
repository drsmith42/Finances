import json
import os
import sys
import time

# --- Configuration ---
RULES_FILE_PATH = "rules.json"

def load_rules():
    """Loads categorization rules from a JSON file into an ordered list."""
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, 'r') as f:
            try:
                rules_dict = json.load(f)
                return list(rules_dict.items())
            except json.JSONDecodeError:
                print("Warning: rules.json is empty or corrupted. Starting with a new rule list.")
                return []
    return []

def save_rules(rules_list):
    """Saves a list of rule tuples back to a JSON file."""
    rules_dict = {key: value for key, value in rules_list}
    with open(RULES_FILE_PATH, 'w') as f:
        json.dump(rules_dict, f, indent=4)

# --- Main Application Logic ---
def main():
    """Main loop for the rule management tool."""
    while True:
        rules_list = load_rules()
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- Rule Manager ---")
        
        if not rules_list:
            print("\nNo rules found.")
        else:
            print("\nCurrent Rules:")
            for i, (key, value) in enumerate(rules_list):
                print(f"  [{i+1}] '{key}' -> '{value}'")

        print("\nOptions:")
        print("  [D] Delete a rule")
        print("  [Q] Quit")
        
        choice = input("\nEnter your choice: ").lower()

        if choice == 'd':
            if not rules_list:
                print("There are no rules to delete.")
                time.sleep(1)
                continue
            
            try:
                rule_num_str = input("Enter the number of the rule to delete: ")
                rule_num = int(rule_num_str)
                
                if 1 <= rule_num <= len(rules_list):
                    removed_rule = rules_list.pop(rule_num - 1)
                    save_rules(rules_list)
                    print(f"\nDeleted rule: '{removed_rule[0]}' -> '{removed_rule[1]}'")
                    print("Changes saved.")
                    input("Press Enter to continue...")
                else:
                    print("Invalid rule number.")
                    input("Press Enter to continue...")

            except ValueError:
                print("Invalid input. Please enter a number.")
                input("Press Enter to continue...")

        elif choice == 'q':
            print("\nExiting Rule Manager.")
            break
        
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()