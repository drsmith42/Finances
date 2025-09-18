import pandas as pd
import os
import hashlib
import re

# --- Helper Function for Cleaning Payee ---
def get_clean_payee(description):
    if not isinstance(description, str): return ""
    payee = re.split(r'\s{2,}|[*#@]| \d{3,}', description)[0].strip()
    return payee.title()

# --- Processor Logic for Each Institution ---

def process_us_bank(df, filename):
    """Handles both US Bank Checking and US Bank CC CSVs."""
    print(" -> US Bank format detected.")
    df['Description'] = (df['Name'].fillna('') + ' ' + df['Memo'].fillna('')).str.replace('Download from usbank.com.', '', regex=False).str.strip()
    if 'credit' in filename or 'cc' in filename:
        df['Account'] = 'US Bank CC'
    else:
        df['Account'] = 'US Bank Checking'
    return df

def process_chase_credit(df):
    print(" -> Chase Credit Card format detected.")
    df.rename(columns={'Transaction Date': 'Date'}, inplace=True)
    df['Account'] = 'Chase CC'
    df['Category'] = ''
    if 'Type' in df.columns:
        payment_mask = (df['Type'] == 'Payment')
        df.loc[payment_mask, 'Category'] = 'Transfer'
    return df

def process_amex(df):
    """Handles American Express files, distinguishing between payments and rewards."""
    print(" -> American Express format detected.")
    df['Description'] = (df['Description'].fillna('') + ' ' + df['Extended Details'].fillna('')).str.replace(r'\n', ' ', regex=True).str.strip()
    df['Amount'] = -df['Amount'].abs()
    df['Account'] = 'Amex CC'
    df['Category'] = ''
    
    payment_keywords = ['ONLINE PAYMENT', 'AUTOPAY PAYMENT', 'PAYMENT RECEIVED']
    reward_keywords = ['CASH REWARD', 'REFUND']

    for keyword in payment_keywords:
        mask = df['Description'].str.contains(keyword, case=False, na=False)
        df.loc[mask, 'Category'] = 'Transfer'
        df.loc[mask, 'Amount'] = df.loc[mask, 'Amount'].abs()

    for keyword in reward_keywords:
        mask = df['Description'].str.contains(keyword, case=False, na=False)
        df.loc[mask, 'Category'] = 'Income: Rewards'
        df.loc[mask, 'Amount'] = df.loc[mask, 'Amount'].abs()
        
    return df
    
def process_discover(df):
    print(" -> Discover Card format detected.")
    df.rename(columns={'Trans. Date': 'Date'}, inplace=True)
    df['Amount'] = df['Amount'] * -1
    df['Account'] = 'Discover CC'
    original_category = df['Category'].copy()
    df['Category'] = ''
    payment_mask = (original_category == 'Payments and Credits')
    df.loc[payment_mask, 'Category'] = 'Transfer'
    # NOTE: This has a known bug, it doesn't flip payment to positive.
    # Leaving as-is for consistency with existing data until a full refactor.
    return df

def process_wells_fargo_summary(df):
    print(" -> Wells Fargo Summary format detected.")
    df.rename(columns={'Trans Date': 'Date'}, inplace=True)
    df['Description'] = df['Payee'].fillna('') + ' ' + df['Description'].fillna('')
    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).replace({r'\$': '', r',': ''}, regex=True), errors='coerce').fillna(0)
    df['Amount'] = -df['Amount'].abs()
    df['Account'] = 'Wells Fargo CC'
    df['Category'] = ''
    payment_keywords = ['PAYMENT']
    for keyword in payment_keywords:
        mask = df['Description'].str.contains(keyword, case=False, na=False)
        df.loc[mask, 'Category'] = 'Transfer'
        df.loc[mask, 'Amount'] = df.loc[mask, 'Amount'].abs()
    return df

def process_target(df):
    """
    Handles the specific format for Target RedCard CSVs, which has
    inconsistent signs for different transaction types. This version uses
    more robust logic to correctly identify each transaction type.
    """
    print(" -> Target RedCard format detected.")
    df['Account'] = 'Target RedCard'
    df['Category'] = ''
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

    # Create a new series to hold the corrected amounts
    new_amount = df['Amount'].copy()

    # Iterate through the DataFrame to apply logic row by row, which is safer for complex conditions
    for index, row in df.iterrows():
        desc = row['Description'].upper()
        amt = row['Amount']

        if 'AUTO PAYMENT' in desc:
            new_amount.loc[index] = abs(amt)
            df.loc[index, 'Category'] = 'Transfer'
        elif 'CREDIT BALANCE REFUND' in desc:
            new_amount.loc[index] = -abs(amt)
            df.loc[index, 'Category'] = 'Transfer'
        elif 'CREDIT' in desc:
            # Explicit returns/credits should be positive
            new_amount.loc[index] = abs(amt)
        elif 'TARGET.COM' in desc:
            # Online purchases are always debits, should be negative
            new_amount.loc[index] = -abs(amt)
        else:
            # For in-store transactions, the sign indicates the type
            if amt > 0: # Positive raw amount is a purchase
                new_amount.loc[index] = -amt
            else: # Negative raw amount is a return
                new_amount.loc[index] = abs(amt)
    
    df['Amount'] = new_amount
    return df


def process_pdf_extract(df, filename):
    """Handles simple CSVs created by our PDF extractors."""
    print(" -> PDF Extract format detected.")
    if 'wells' in filename:
        df['Account'] = 'Wells Fargo CC'
    elif 'target' in filename:
        return process_target(df) # Route to the dedicated Target processor
    elif 'usb' in filename:
        df['Account'] = 'US Bank CC'
    else:
        df['Account'] = 'Unassigned PDF Extract'
    return df
    
def process_etherfi(df):
    print(" -> Etherfi Card format detected.")
    df.rename(columns={ 'timestamp': 'Date', 'description': 'Description'}, inplace=True)
    df['Amount'] = pd.to_numeric(df['original amount'], errors='coerce').fillna(0)
    refund_mask = (df['Amount'] > 0)
    df.loc[refund_mask, 'Category'] = 'Shopping: Amazon Return'
    df['Account'] = 'Etherfi CC'
    return df
    
def process_venmo(df):
    print(" -> Venmo format detected.")
    df.dropna(subset=['ID', 'Datetime'], inplace=True)
    df.rename(columns={'Datetime': 'Date', 'Amount (total)': 'Amount', 'Funding Source': 'Funding_Source'}, inplace=True)
    amount_str = df['Amount'].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False).str.replace(r'[$,+]', '', regex=True)
    df['Amount'] = pd.to_numeric(amount_str, errors='coerce').fillna(0)
    df['Description'] = df['Note'].fillna('')
    df['Payee'] = df.apply(lambda row: row['To'] if pd.notna(row['To']) else row['From'], axis=1)
    df['Account'] = 'Venmo'
    withdrawal_mask = df['Type'] == 'Standard Transfer'
    df.loc[withdrawal_mask, 'Description'] = "Venmo Withdrawal to Bank"
    df.loc[withdrawal_mask, 'Payee'] = "US Bank"
    df.loc[withdrawal_mask, 'Category'] = "Transfer"
    return df

# --- Main Script ---
def main():
    print("--- Universal Statement Processor ---")
    input_path = input("Please provide the path to your raw CSV statement file: ").strip().replace("'", "").replace('"', '')

    if not os.path.exists(input_path):
        print(f"❌ ERROR: File not found at '{input_path}'")
        return
        
    try:
        try:
            df_raw = pd.read_csv(input_path, on_bad_lines='skip')
        except UnicodeDecodeError:
            print(" -> Warning: UTF-8 decoding failed. Retrying with 'latin-1' encoding.")
            df_raw = pd.read_csv(input_path, on_bad_lines='skip', encoding='latin-1')

        header = df_raw.columns.tolist()
        df_processed = None
        filename_lower = os.path.basename(input_path).lower()

        # --- Updated Routing Logic ---
        if 'target' in filename_lower:
            df_processed = process_target(df_raw)
        elif 'venmo' in filename_lower:
            df_processed = process_venmo(df_raw)
        elif 'wells' in filename_lower and ('pdf' in filename_lower or 'extracted' in filename_lower):
            df_processed = process_pdf_extract(df_raw, filename_lower)
        elif 'usb' in filename_lower:
             df_processed = process_us_bank(df_raw, filename_lower)
        elif 'etherfi' in filename_lower:
            df_processed = process_etherfi(df_raw)
        else:
            print(" -> Filename not recognized. Attempting to identify by content...")
            if 'Funding Source' in header and 'Amount (total)' in header:
                df_processed = process_venmo(df_raw)
            elif 'timestamp' in header and 'original amount' in header:
                df_processed = process_etherfi(df_raw)
            elif 'Trans. Date' in header and 'Category' in header:
                df_processed = process_discover(df_raw)
            elif 'Extended Details' in header:
                df_processed = process_amex(df_raw)
            elif 'Name' in header and 'Memo' in header:
                df_processed = process_us_bank(df_raw, filename_lower)
            elif 'Type' in header and 'Transaction Date' in header:
                df_processed = process_chase_credit(df_raw)
            elif 'Master Category' in header and 'Subcategory' in header:
                df_processed = process_wells_fargo_summary(df_raw)
            else:
                print("❌ ERROR: Could not identify the format from filename or column headers.")
                print("\nFound the following headers:", header)
                return

        df_processed['Date'] = pd.to_datetime(df_processed['Date']).dt.date
        df_processed['Amount'] = pd.to_numeric(df_processed['Amount'], errors='coerce').fillna(0)
        
        if 'Payee' not in df_processed.columns:
            df_processed['Payee'] = df_processed['Description'].apply(get_clean_payee)
        
        for col in ['Is_Tax_Deductible', 'Is_Reimbursable']:
            if col not in df_processed.columns: df_processed[col] = False
        if 'Category' not in df_processed.columns: df_processed[col] = ''

        df_processed['Source'] = os.path.basename(input_path)

        def create_id(row):
            # Use a consistent format for amount to avoid floating point issues
            amount_str = f"{row['Amount']:.2f}"
            data_string = f"{str(row['Date'])}{row['Description']}{amount_str}".encode()
            return hashlib.md5(data_string).hexdigest()
        df_processed['TransactionID'] = df_processed.apply(create_id, axis=1)

        final_columns = ['Date', 'Account', 'Description', 'Payee', 'Amount', 'Category', 
                         'Is_Tax_Deductible', 'Is_Reimbursable', 'Source', 'TransactionID']
        extra_columns = [col for col in df_processed.columns if col not in final_columns]
        df_final = df_processed[final_columns + extra_columns]
        
        output_filename = f"processed_{os.path.basename(input_path)}"
        output_path = os.path.join(os.path.dirname(input_path), output_filename)
        
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Success! Standardized file created at: {output_path}")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

