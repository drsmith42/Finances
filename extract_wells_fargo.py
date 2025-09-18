import pdfplumber
import pandas as pd
import os
import sys
import re

def parse_amount(text_list):
    """Finds the last valid number in a list of strings."""
    for text in reversed(text_list):
        if text and text.strip():
            cleaned_text = text.strip().replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
            try:
                return float(cleaned_text)
            except ValueError:
                continue
    return 0.0

def get_year_from_period(text):
    """Finds the year from the statement period text."""
    matches = re.findall(r'\d{2}/\d{2}/(\d{4})', text)
    if matches:
        return matches[-1]
    return None

def extract_transactions_from_pdf(pdf_path):
    """
    Extracts transactions from a Wells Fargo PDF using a context-aware, line-by-line parsing method.
    """
    print(f"Processing PDF: {os.path.basename(pdf_path)}...")
    all_transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            year = None
            first_page_text = pdf.pages[0].extract_text()
            if first_page_text:
                year = get_year_from_period(first_page_text)
            
            if not year:
                print("  -> WARNING: Could not determine statement year.")
            else:
                print(f"  -> Determined statement year to be: {year}")

            current_section = None 

            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2)
                if not text:
                    continue

                for line in text.split('\n'):
                    line = line.strip()
                    
                    if 'OTHER CREDITS' in line.upper():
                        current_section = 'credits'
                        continue
                    elif 'PURCHASES, BALANCE TRANSFERS & OTHER CHARGES' in line.upper():
                        current_section = 'charges'
                        continue
                    
                    if re.match(r'^\d{4}\s+\d{2}/\d{2}', line):
                        parts = line.split()
                        
                        # Ensure the line is long enough to be a transaction
                        if len(parts) < 5:
                            continue

                        trans_date_md = parts[1]
                        full_date = f"{trans_date_md}/{year}" if year else trans_date_md
                        
                        # --- THIS IS THE FIX ---
                        # The description starts from the 5th element (index 4), not the 4th.
                        description = " ".join(parts[4:-1])
                        
                        amount_val = parse_amount(parts[-1:])
                        
                        if current_section == 'charges':
                            amount = -abs(amount_val)
                        else:
                            amount = abs(amount_val)
                        
                        if "TOTAL" not in description.upper():
                            all_transactions.append([full_date, description, amount])

    except Exception as e:
        print(f"  -> Could not process PDF file. Error: {e}")
        return

    if not all_transactions:
        print("  -> No transactions could be extracted with the final method.")
        return

    df = pd.DataFrame(all_transactions, columns=['Date', 'Description', 'Amount'])
    
    output_filename = f"extracted_{os.path.basename(pdf_path).replace('.pdf', '.csv')}"
    output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
    df.to_csv(output_path, index=False)
    
    print(f"  -> Success! Saved {len(df)} transactions to '{output_filename}'")


if __name__ == "__main__":
    print("--- Wells Fargo PDF Extractor (v2 - Corrected) ---")
    pdf_path = input("Please provide the path to a Wells Fargo PDF statement file: ")
    extract_transactions_from_pdf(pdf_path.strip().replace("'", "").replace('"', ''))