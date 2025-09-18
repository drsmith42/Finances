import pandas as pd
import os
import sys
import time
import re
from datetime import timedelta

# --- Helper Functions ---
def clean_chase_file(df):
    """Prepares the processed Chase file for use."""
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
    df.dropna(subset=['Date'], inplace=True)
    return df

def clean_amazon_report(df_amazon):
    """Prepares the detailed Amazon Order History Report for use."""
    df = df_amazon.copy()
    df.rename(columns={'Product Name': 'Item_Description', 'Total Owed': 'Item_Total'}, inplace=True)
    df['Item_Total'] = pd.to_numeric(df['Item_Total'].replace({r'[\$,]': ''}, regex=True), errors='coerce').fillna(0)
    df['Order_Date_dt'] = pd.to_datetime(df['Order Date'], errors='coerce').dt.tz_localize(None).dt.normalize()
    return df

# --- Main Application Logic ---
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Guided Amazon Matcher ---")

    try:
        processed_file_path = input("Path to your 'processed_...' Chase file: ").strip().replace("'", "").replace('"', '')
        df_chase = clean_chase_file(pd.read_csv(processed_file_path))
        
        amazon_order_path = input("Path to your Amazon 'Retail.OrderHistory.csv' file: ").strip().replace("'", "").replace('"', '')
        df_amazon = clean_amazon_report(pd.read_csv(amazon_order_path))
        
    except (FileNotFoundError, KeyError) as e:
        print(f"\n❌ ERROR: Could not load a necessary file. Details: {e}")
        sys.exit(1)

    search_pattern = "AMAZON|AMZN|WHOLE FOODS"
    amazon_charges = df_chase[df_chase['Description'].str.contains(search_pattern, case=False, na=False)].copy()
    non_amazon_transactions = df_chase[~df_chase['Description'].str.contains(search_pattern, case=False, na=False)].copy()

    reconciled_items = []
    unreconciled_charges = []
    reconciled_order_ids = set()

    for index, charge in amazon_charges.iterrows():
        reconciled_this_charge = False
        while not reconciled_this_charge:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"--- Matching Charge ---")
            print(f"   Date: {charge['Date'].strftime('%Y-%m-%d')}")
            print(f" Amount: {charge['Amount']:.2f}")
            print(f"   Description: {charge['Description']}")
            print("--------------------------\n")

            keyword_input = input("Enter one or more keywords (separated by commas) to find matching items, or [s] to skip: ").lower()
            
            if keyword_input == 's':
                break

            if not keyword_input:
                continue
            
            keywords = [k.strip() for k in keyword_input.split(',')]
            search_regex = '|'.join(map(re.escape, keywords))

            candidate_items = df_amazon[df_amazon['Item_Description'].str.contains(search_regex, case=False, na=False)]

            if candidate_items.empty:
                print(f"No items found matching your keywords. Please try again.")
                time.sleep(2)
                continue

            selected_items_indices = []
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"--- Selecting items for charge: {charge['Amount']:.2f} ---")
                
                item_map = {}
                for i, (item_index, item) in enumerate(candidate_items.iterrows()):
                    marker = "[X]" if item_index in selected_items_indices else "[ ]"
                    item_map[i+1] = item_index
                    print(f" {marker} [{i+1}] {item['Order_Date_dt'].strftime('%Y-%m-%d')} - {item['Item_Description'][:60]:<60} ${item['Item_Total']:.2f}")

                selected_total = candidate_items.loc[selected_items_indices]['Item_Total'].sum()
                print(f"\nSelected Total: ${selected_total:.2f}  (Target: ${abs(charge['Amount']):.2f})")
                
                item_choice = input("\nEnter item number to toggle, [d] when done, or [c] to cancel and search new keywords: ").lower()

                if item_choice == 'd':
                    credit_amount = 0.0
                    if abs(selected_total - abs(charge['Amount'])) > 0.01:
                        print("\nTotals do not match.")
                        credit_str = input("Used points/credits? If so, how much?: ")
                        try:
                            credit_amount = float(credit_str) if credit_str else 0.0
                        except ValueError:
                            print("Invalid amount. Aborting match.")
                            time.sleep(2)
                            break
                    
                    if abs(selected_total - credit_amount - abs(charge['Amount'])) < 0.01:
                        matched_items = candidate_items.loc[selected_items_indices]
                        if credit_amount > 0:
                            item_descriptions = " & ".join(matched_items['Item_Description'].tolist())
                            combined_description = f"Amazon (Mixed Payment): {item_descriptions}"
                            reconciled_items.append({'Charge_Date': charge['Date'], 'Chase_Description': charge['Description'], 'Chase_Amount': charge['Amount'], 'Order_ID': "MULTIPLE", 'Item_Description': combined_description, 'Item_Amount': charge['Amount']})
                        else:
                            for _, item_row in matched_items.iterrows():
                                reconciled_items.append({'Charge_Date': charge['Date'], 'Chase_Description': charge['Description'], 'Chase_Amount': charge['Amount'], 'Order_ID': item_row['Order ID'], 'Item_Description': item_row['Item_Description'], 'Item_Amount': -item_row['Item_Total']})
                        
                        for order_id in matched_items['Order ID'].unique():
                            reconciled_order_ids.add(order_id)
                        reconciled_this_charge = True
                        print("\nMatch successful!")
                        time.sleep(1)
                    else:
                        print("Credit amount does not resolve the difference. Please re-select items.")
                        time.sleep(2)
                    
                    if reconciled_this_charge:
                        break

                elif item_choice == 'c':
                    break
                
                else:
                    try:
                        selected_item_index = item_map[int(item_choice)]
                        if selected_item_index in selected_items_indices:
                            selected_items_indices.remove(selected_item_index)
                        else:
                            selected_items_indices.append(selected_item_index)
                    except (ValueError, KeyError):
                        print("Invalid selection.")
                        time.sleep(1)

        if not reconciled_this_charge:
            unreconciled_charges.append(charge.to_dict())

    # --- Generate Output Files ---
    output_dir = os.path.dirname(processed_file_path)
    
    non_amazon_path = os.path.join(output_dir, "non_amazon_transactions.csv")
    non_amazon_transactions.to_csv(non_amazon_path, index=False)
    print(f"\nSaved {len(non_amazon_transactions)} non-Amazon transactions to '{non_amazon_path}'")
    
    df_reconciled = pd.DataFrame(reconciled_items)
    reconciled_path = os.path.join(output_dir, "reconciled_amazon_items.csv")
    df_reconciled.to_csv(reconciled_path, index=False)
    print(f"Saved {len(df_reconciled)} successfully reconciled Amazon items to '{reconciled_path}'")
    
    df_unreconciled_charges = pd.DataFrame(unreconciled_charges)
    unreconciled_charges_path = os.path.join(output_dir, "unreconciled_amazon_charges.csv")
    df_unreconciled_charges.to_csv(unreconciled_charges_path, index=False)
    print(f"Saved {len(df_unreconciled_charges)} unreconciled Amazon charges to '{unreconciled_charges_path}'")

    unreconciled_amazon_items = df_amazon[~df_amazon['Order ID'].isin(reconciled_order_ids)]
    unreconciled_items_path = os.path.join(output_dir, "unreconciled_amazon_items.csv")
    unreconciled_amazon_items.to_csv(unreconciled_items_path, index=False)
    print(f"Saved {len(unreconciled_amazon_items)} unreconciled items from the Amazon report to '{unreconciled_items_path}'")

if __name__ == "__main__":
    main()