import pandas as pd
import os
import sys

def investigate_all_charges():
    """
    Loads aggregated Whole Foods receipts and the ENTIRE processed Chase file
    to find potential matches, regardless of initial classification.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Universal Match Investigator ---")

    try:
        # Load the unreconciled items to get the WFM receipts
        input_dir = input("Enter the path to the FOLDER where your unreconciled files are: ").strip().replace("'", "").replace('"', '')
        unreconciled_items_path = os.path.join(input_dir, "unreconciled_amazon_items.csv")
        df_items = pd.read_csv(unreconciled_items_path)
        if 'Order Date' in df_items.columns:
            df_items['Order_Date_dt'] = pd.to_datetime(df_items['Order Date'], errors='coerce').dt.tz_localize(None).dt.normalize()
        if 'Item_Total' not in df_items.columns and 'Total Owed' in df_items.columns:
            df_items.rename(columns={'Total Owed': 'Item_Total'}, inplace=True)
        df_items['Item_Total'] = pd.to_numeric(df_items['Item_Total'], errors='coerce').fillna(0)

        # Load the ENTIRE processed Chase file
        processed_chase_path = input("Path to your 'processed_...' Chase file: ").strip().replace("'", "").replace('"', '')
        df_chase = pd.read_csv(processed_chase_path)
        df_chase['Date'] = pd.to_datetime(df_chase['Date'], errors='coerce').dt.normalize()
        
    except (FileNotFoundError, KeyError) as e:
        print(f"\n❌ ERROR: Could not load a necessary file. Details: {e}")
        sys.exit(1)

    # --- Aggregate Whole Foods Items ---
    wfm_items = df_items[df_items['Website'] == 'whole foods'].copy()
    if wfm_items.empty:
        print("\nNo Whole Foods items found in the unreconciled items file.")
        return
        
    wfm_baskets = wfm_items.groupby('Order_Date_dt')['Item_Total'].sum().reset_index()

    # --- Search for Matches in the ENTIRE Chase File ---
    print("\n\n--- Potential Matches Report ---")
    print("Searching all Chase transactions for matches to Whole Foods receipts...")
    
    found_match = False
    for _, basket in wfm_baskets.iterrows():
        basket_date, basket_total = basket['Order_Date_dt'], basket['Item_Total']
        
        # Search for a charge with a matching date and amount
        match = df_chase[
            (df_chase['Date'] == basket_date) & 
            (abs(abs(df_chase['Amount']) - basket_total) < 0.01)
        ]
        
        if not match.empty:
            found_match = True
            matched_charge = match.iloc[0]
            print("\n-------------------------------------------")
            print(f"✅ POTENTIAL MATCH FOUND")
            print(f"  - WFM Receipt Date: {basket_date.strftime('%Y-%m-%d')}")
            print(f"  - WFM Receipt Total: ${basket_total:.2f}")
            print(f"  - Matched Chase Charge Description: '{matched_charge['Description']}'")
            print("-------------------------------------------")

    if not found_match:
        print("\nNo potential matches were found in the entire Chase file.")
        
    print("\n--- End of Report ---")


if __name__ == "__main__":
    investigate_all_charges()