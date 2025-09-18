import pandas as pd
import os
import sys
from datetime import datetime
import re

# --- Configuration ---
MASTER_FILE_PATH = "master_transactions.csv"
OUTPUT_EXCEL_FILE = "financial_dashboard.xlsx"

def generate_excel_dashboard():
    """
    Reads the master transaction file and generates a comprehensive, multi-sheet
    Excel dashboard with yearly summaries, comparisons, and detailed drill-downs.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Financial Dashboard Generator ---")

    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        sys.exit(1)

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        print(f"✅ Master file loaded. Analyzing {len(df)} transactions...")

        # --- Data Preparation ---
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        df['Date'] = pd.to_datetime(df['Date'], format='mixed')
        df['Year'] = df['Date'].dt.year
        df['Category'] = df['Category'].fillna('Uncategorized')
        
    except Exception as e:
        print(f"❌ An error occurred while processing the master file: {e}")
        return

    print(f"\nWriting dashboard to '{OUTPUT_EXCEL_FILE}'...")
    with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='xlsxwriter') as writer:
        
        years = sorted(df['Year'].unique())
        
        # --- 1. Generate Report for Each Year ---
        for year in years:
            print(f" -> Processing data for {year}...")
            yearly_data = df[df['Year'] == year].copy()
            
            # --- NEW, DEFINITIVE SUMMARIZATION LOGIC ---
            # This method is the most robust, as it calculates all metrics at once
            # before aggregation, ensuring no transactions are miscounted or dropped.

            is_transfer = yearly_data['Category'].str.startswith('Transfer', na=False)

            # Create temporary columns for each metric type
            yearly_data['Spending'] = yearly_data.loc[~is_transfer & (yearly_data['Amount'] < 0), 'Amount']
            yearly_data['Income'] = yearly_data.loc[~is_transfer & (yearly_data['Amount'] > 0), 'Amount']
            yearly_data['Transfers_In'] = yearly_data.loc[is_transfer & (yearly_data['Amount'] > 0), 'Amount']
            yearly_data['Transfers_Out'] = yearly_data.loc[is_transfer & (yearly_data['Amount'] < 0), 'Amount']
            
            # Fill any non-applicable rows with 0
            yearly_data[['Spending', 'Income', 'Transfers_In', 'Transfers_Out']] = yearly_data[['Spending', 'Income', 'Transfers_In', 'Transfers_Out']].fillna(0)

            # Group by account and sum the temporary columns to get a guaranteed-correct summary
            full_summary = yearly_data.groupby('Account')[['Spending', 'Income', 'Transfers_In', 'Transfers_Out']].sum().reset_index()

            # --- Create the two separate reports from the single summary ---
            operational_summary = full_summary[['Account', 'Spending', 'Income']].copy()
            operational_summary['Operational_Balance'] = operational_summary['Spending'] + operational_summary['Income']

            transfer_audit = full_summary[['Account', 'Transfers_In', 'Transfers_Out']].copy()
            
            grand_total_in = transfer_audit['Transfers_In'].sum()
            grand_total_out = transfer_audit['Transfers_Out'].sum()

            total_row = pd.DataFrame([{'Account': '--- GRAND TOTAL ---', 'Transfers_In': grand_total_in, 'Transfers_Out': grand_total_out}])
            transfer_audit = pd.concat([transfer_audit, total_row], ignore_index=True)
            transfer_audit['Net_Position'] = transfer_audit['Transfers_In'] + transfer_audit['Transfers_Out']

            # --- Write to Excel Sheet ---
            sheet_name = f'{year}_Summary'
            operational_summary.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)
            
            transfer_audit_start_row = len(operational_summary) + 4
            transfer_audit.to_excel(writer, sheet_name=sheet_name, index=False, startrow=transfer_audit_start_row)

        # --- 2. Write Master Data and Drill-Downs ---
        print(" -> Writing master data sheet...")
        df_to_write = df.copy()
        df_to_write['Date'] = df_to_write['Date'].dt.strftime('%Y-%m-%d')
        df_to_write.to_excel(writer, sheet_name='Master_Data', index=False)

        print(" -> Creating drill-down sheets for each category...")
        all_categories = sorted(df['Category'].unique())
        
        for category in all_categories:
            sheet_name = f"Details_{re.sub('[^A-Za-z0-9]+', '', category)[:22]}"
            category_df = df[df['Category'] == category].sort_values(by='Date')
            total_amount = category_df['Amount'].sum()
            
            # Prepare df for writing
            category_df_with_total = category_df[['Date', 'Account', 'Description', 'Amount']].copy()
            category_df_with_total['Date'] = category_df_with_total['Date'].dt.strftime('%Y-%m-%d')
            
            total_row = pd.DataFrame([{'Date': '', 'Account': '', 'Description': 'TOTAL', 'Amount': total_amount}])
            category_df_with_total = pd.concat([category_df_with_total, total_row], ignore_index=True)
            category_df_with_total.to_excel(writer, sheet_name=sheet_name, index=False)

        # --- 3. Apply Formatting ---
        print(" -> Applying formatting...")
        workbook = writer.book
        money_format = workbook.add_format({'num_format': '$#,##0.00'})
        bold_money_format = workbook.add_format({'num_format': '$#,##0.00', 'bold': True})
        header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#4F81BD', 'align': 'center'})
        section_header_format = workbook.add_format({'bold': True, 'font_size': 14})
        
        for year in years:
            worksheet = writer.sheets[f'{year}_Summary']
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:E', 18, money_format)

            # Format Operational Summary
            worksheet.write('A1', 'Operational Summary', section_header_format)
            for col_num, value in enumerate(operational_summary.columns.values):
                worksheet.write(1, col_num, value, header_format)

            # Format Transfer Audit
            transfer_audit_header_row = len(operational_summary) + 4
            worksheet.write(transfer_audit_header_row - 1, 0, 'Inter-Account Transfer Audit', section_header_format)
            for col_num, value in enumerate(transfer_audit.columns.values):
                worksheet.write(transfer_audit_header_row, col_num, value, header_format)
            
            # Make the total row bold
            worksheet.conditional_format(f'A{transfer_audit_header_row + len(transfer_audit)}:E{transfer_audit_header_row + len(transfer_audit)}', {'type': 'no_blanks', 'format': bold_money_format})
        
        for category in all_categories:
            sheet_name = f"Details_{re.sub('[^A-Za-z0-9]+', '', category)[:22]}"
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 60)
            worksheet.set_column('D:D', 12, money_format)
            
            # Find the total row and apply bold formatting
            last_row_index = len(df[df["Category"] == category]) + 2
            worksheet.conditional_format(f'A{last_row_index}:D{last_row_index}', {'type': 'no_blanks', 'format': bold_money_format})

    print("\n✅ Dashboard generated successfully!")

if __name__ == "__main__":
    generate_excel_dashboard()

