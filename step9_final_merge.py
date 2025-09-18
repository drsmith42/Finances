import pandas as pd
import os
import sys
import hashlib

# --- Configuration ---
MASTER_COLUMNS = [
    'Date', 'Account', 'Description', 'Payee', 'Amount', 'Category', 
    'Is_Tax_Deductible', 'Is_Reimbursable', 'Source', 'TransactionID', 'Reviewed'
]
ACCOUNT_NAME = "Chase CC"

def load_and_prepare_file(path, source_prefix):
    """Loads a CSV and prepares it for merging by standardizing columns."""
    print(f"    -> Processing {os.path.basename(path)}...")
    df = pd.read_csv(path)
    
    df_standard = pd.DataFrame()
    
    # --- Column Mapping ---
    if 'Item_Description' in df.columns:
        df_standard['Description'] = df['Item_Description']
        df_standard['Amount'] = pd.to_numeric(df['Item_Amount'], errors='coerce')
        df_standard['Date'] = pd.to_datetime(df['Charge_Date']).dt.strftime('%Y-%m-%d')
    else:
        df_standard['Description'] = df['Description']
        df_standard['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df_standard['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    df_standard['Account'] = ACCOUNT_NAME
    df_standard['Payee'] = df.get('Payee', df_standard['Description'].str.split('*').str[0].str.title().str.strip())
    df_standard['Category'] = df.get('Category', 'NEEDS REVIEW')
    
    df_standard['Is_Tax_Deductible'] = False
    df_standard['Is_Reimbursable'] = False
    # --- FIX: Standardized the source name to prevent duplication ---
    df_standard['Source'] = f"{source_prefix}_{os.path.basename(path)}"
    df_standard['Reviewed'] = False
    
    def create_id(row):
        data_string = f"{row['Date']}{row['Description']}{row['Amount']:.2f}{row['Account']}"
        return hashlib.md5(data_string.encode()).hexdigest()
        
    df_standard['TransactionID'] = df_standard.apply(create_id, axis=1)
    
    return df_standard[MASTER_COLUMNS]

def main():
    """Main function to perform a clean merge for Amazon and non-Amazon transactions."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Amazon Reconciliation Final Merge ---")

    try:
        input_dir = input("Enter the path to the FOLDER where your categorized CSVs are: ").strip().replace("'", "").replace('"', '')
        
        master_path = os.path.join(input_dir, "..", "master_transactions.csv")
        reconciled_items_path = os.path.join(input_dir, "categorized_reconciled_amazon_items.csv")
        non_amazon_path = os.path.join(input_dir, "categorized_non_amazon_transactions.csv")
        manual_charges_path = os.path.join(input_dir, "categorized_manual_charges.csv")

        if not os.path.exists(master_path):
            print(f"\n❌ ERROR: Master file not found at '{master_path}'.")
            sys.exit(1)
        df_master = pd.read_csv(master_path)
        print(f"\n✅ Master file loaded. Contains {len(df_master)} transactions.")

    except Exception as e:
        print(f"\n❌ ERROR: Could not load a necessary file. Details: {e}")
        sys.exit(1)

    # --- Step 1: Prepare and Combine New Transaction Files ---
    all_new_transactions = []
    print("\nStep 1: Preparing new transaction files for merge...")
    
    # --- FIX: Using a consistent prefix for all reconciled files ---
    if os.path.exists(reconciled_items_path):
        all_new_transactions.append(load_and_prepare_file(reconciled_items_path, "chase_reconciliation"))
    if os.path.exists(non_amazon_path):
        all_new_transactions.append(load_and_prepare_file(non_amazon_path, "chase_reconciliation"))
    if os.path.exists(manual_charges_path):
        all_new_transactions.append(load_and_prepare_file(manual_charges_path, "chase_reconciliation"))

    if not all_new_transactions:
        print("\nNo new transaction files found to merge.")
        return
        
    df_to_append = pd.concat(all_new_transactions, ignore_index=True)
    
    # --- Step 2: Final Merge and Save ---
    print("\nStep 2: Merging new data into master file...")
    
    # Safety check to ensure we don't re-add transactions if the script is run twice
    existing_ids = set(df_master['TransactionID'])
    df_to_append = df_to_append[~df_to_append['TransactionID'].isin(existing_ids)]
    
    if df_to_append.empty:
        print("\nNo genuinely new transactions to add. Master file is already up to date.")
    else:
        print(f" -> Adding {len(df_to_append)} new, unique transactions.")
    
    df_final_master = pd.concat([df_master, df_to_append], ignore_index=True)
    
    df_final_master.to_csv(master_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Success! Master file updated. It now contains {len(df_final_master)} total transactions.")
    print("The Chase reconciliation is now complete.")

if __name__ == "__main__":
    main()
