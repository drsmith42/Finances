import pandas as pd
import os
import sys

def audit_reconciliation_status():
    """
    Reads all relevant Chase & Amazon files and provides a high-level
    summary of the reconciliation status.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Reconciliation Data Audit ---")

    try:
        # --- Load Source Files ---
        processed_file_path = input("Path to your 'processed_...' Chase file: ").strip().replace("'", "").replace('"', '')
        df_chase = pd.read_csv(processed_file_path)

        amazon_order_path = input("Path to your Amazon 'Retail.OrderHistory.csv' file: ").strip().replace("'", "").replace('"', '')
        df_amazon = pd.read_csv(amazon_order_path)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Could not load a source file. Details: {e}")
        sys.exit(1)

    # --- Perform the Audit ---
    print("\n\n--- AUDIT REPORT ---")
    
    # 1. Chase Data Integrity Check
    print("\n## Chase Statement Breakdown ##")
    total_chase_txns = len(df_chase)
    search_pattern = "AMAZON|AMZN|WHOLE FOODS"
    amazon_txns_mask = df_chase['Description'].str.contains(search_pattern, case=False, na=False)
    amazon_txns_count = amazon_txns_mask.sum()
    non_amazon_count = total_chase_txns - amazon_txns_count
    
    print(f"Total Transactions in Processed Chase File: {total_chase_txns}")
    print(f"  - Non-Amazon Transactions: {non_amazon_count}")
    print(f"  - Amazon-Related Charges & Credits: {amazon_txns_count}")
    
    # 2. Reconciliation Status Check
    print("\n## Amazon Reconciliation Status ##")
    try:
        output_dir = os.path.dirname(processed_file_path)
        
        df_reconciled_items = pd.read_csv(os.path.join(output_dir, "reconciled_amazon_items.csv"))
        # Correctly count unique original transactions (both charges and credits)
        reconciled_txns_count = df_reconciled_items['Chase_Description'].nunique()
        
        df_unreconciled_charges = pd.read_csv(os.path.join(output_dir, "unreconciled_amazon_charges.csv"))
        unreconciled_txns_count = len(df_unreconciled_charges)

        print(f"Total Amazon Transactions to Reconcile: {amazon_txns_count}")
        print(f"  - Successfully Reconciled Transactions: {reconciled_txns_count}")
        print(f"  - Unreconciled Transactions Remaining: {unreconciled_txns_count}")

        if (reconciled_txns_count + unreconciled_txns_count) == amazon_txns_count:
            print("  -> Verification: All Amazon transactions are accounted for. ✅")
        else:
            print("  -> VERIFICATION WARNING: There is a mismatch in the number of accounted-for transactions! ⚠️")

    except FileNotFoundError:
        print("  -> Could not find reconciliation output files. Please run step5 first.")
        
    # 3. Amazon Order History Status
    print("\n## Amazon Order History Breakdown ##")
    total_amazon_items = len(df_amazon)
    wfm_items_count = len(df_amazon[df_amazon['Website'] == 'whole foods'])
    amz_items_count = total_amazon_items - wfm_items_count
    
    print(f"Total Items in Amazon Order History: {total_amazon_items}")
    print(f"  - Amazon.com Items: {amz_items_count}")
    print(f"  - Whole Foods Items: {wfm_items_count}")
    
    try:
        df_unreconciled_items = pd.read_csv(os.path.join(output_dir, "unreconciled_amazon_items.csv"))
        unreconciled_items_count = len(df_unreconciled_items)
        matched_items_count = total_amazon_items - unreconciled_items_count
        
        print(f"  - Matched Items: {matched_items_count}")
        print(f"  - Unmatched Items Remaining: {unreconciled_items_count}")
    except FileNotFoundError:
        print("  -> Could not find unreconciled items file.")
        
    print("\n--- END OF REPORT ---")


if __name__ == "__main__":
    audit_reconciliation_status()