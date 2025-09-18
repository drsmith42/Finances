import pandas as pd
import os
import sys

def investigate_wfm_matches():
    """
    Loads unreconciled data and displays aggregated Whole Foods receipts
    alongside unreconciled charges to help manually identify mismatches.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Whole Foods Match Investigator ---")

    try:
        input_dir = input("Enter the path to the FOLDER where your unreconciled files are: ").strip().replace("'", "").replace('"', '')
        
        unreconciled_charges_path = os.path.join(input_dir, "unreconciled_amazon_charges.csv")
        df_charges = pd.read_csv(unreconciled_charges_path)
        df_charges['Date'] = pd.to_datetime(df_charges['Date'], errors='coerce').dt.normalize()

        unreconciled_items_path = os.path.join(input_dir, "unreconciled_amazon_items.csv")
        df_items = pd.read_csv(unreconciled_items_path)
        if 'Order Date' in df_items.columns:
            df_items['Order_Date_dt'] = pd.to_datetime(df_items['Order Date'], errors='coerce').dt.tz_localize(None).dt.normalize()
        if 'Item_Total' not in df_items.columns and 'Total Owed' in df_items.columns:
            df_items.rename(columns={'Total Owed': 'Item_Total'}, inplace=True)
        df_items['Item_Total'] = pd.to_numeric(df_items['Item_Total'], errors='coerce').fillna(0)

    except (FileNotFoundError, KeyError) as e:
        print(f"\n❌ ERROR: Could not load a necessary file. Details: {e}")
        sys.exit(1)

    # --- Aggregate Whole Foods Items ---
    wfm_items = df_items[df_items['Website'] == 'whole foods'].copy()
    if wfm_items.empty:
        print("\nNo Whole Foods items found in the unreconciled items file.")
        return
        
    wfm_baskets = wfm_items.groupby('Order_Date_dt')['Item_Total'].sum().reset_index()

    # --- Display Reports ---
    print("\n\n--- Report 1: Aggregated Whole Foods Receipts ---")
    if not wfm_baskets.empty:
        for _, basket in wfm_baskets.iterrows():
            print(f"  - Date: {basket['Order_Date_dt'].strftime('%Y-%m-%d')}, Total: ${basket['Item_Total']:.2f}")
    else:
        print("No Whole Foods receipts to display.")
        
    print("\n\n--- Report 2: Unreconciled Chase Charges ---")
    if not df_charges.empty:
        for _, charge in df_charges.iterrows():
            print(f"  - Date: {charge['Date'].strftime('%Y-%m-%d')}, Amount: ${abs(charge['Amount']):.2f}, Description: {charge['Description']}")
    else:
        print("No unreconciled charges to display.")
        
    print("\n\n--- End of Report ---")


if __name__ == "__main__":
    investigate_wfm_matches()