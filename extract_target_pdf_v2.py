import pandas as pd
import pdfplumber
import os
import sys
import re

def get_year_from_filename(filename):
    """Extracts a 4-digit year from the filename."""
    match = re.search(r'(20\d{2})', filename)
    if match:
        return match.group(1)
    return None

def parse_date_from_match(date_str, year_str):
    """Converts a MM/DD date string and a year string into a standard date format."""
    month, day = date_str.split('/')
    return f"{year_str}-{int(month):02d}-{int(day):02d}"

def extract_transactions_from_pdf(pdf_path):
    """
    Extracts transactions from a Target PDF using a regex-based, text-parsing strategy.
    """
    print(f"Processing PDF: {os.path.basename(pdf_path)}...")
    all_transactions = []
    
    # This regex is the "brain". It looks for lines starting with a date, followed by a description, and ending with a dollar amount.
    transaction_pattern = re.compile(r"^\s*(\d{1,2}/\d{1,2})\s+(.+?)\s+(-?\$[\d,]+\.\d{2})$", re.MULTILINE)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            year = get_year_from_filename(os.path.basename(pdf_path))
            
            if not year:
                # Fallback to searching text if not in filename
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    year_match = re.search(r'(20\d{2})', first_page_text)
                    if year_match: year = year_match.group(1)
            
            if year:
                print(f"  -> Determined statement year to be: {year}")
            else:
                 print("  -> WARNING: Could not determine statement year. Dates will be incomplete.")
                 year = "YYYY" 

            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2)
                if not text:
                    continue

                # Find all lines in the text that match our transaction pattern
                matches = transaction_pattern.findall(text)
                for match in matches:
                    date_md, description, amount_str = match
                    
                    full_date = parse_date_from_match(date_md, year)
                    amount = float(amount_str.replace('$', '').replace(',', ''))
                    
                    # Reverse the polarity to match our system's standard (expenses negative, payments positive)
                    amount = amount * -1
                    
                    # Filter out summary lines that might accidentally match
                    if "TOTAL" not in description.upper():
                        all_transactions.append([full_date, description.strip(), amount])

    except Exception as e:
        print(f"  -> Could not process PDF file. Error: {e}")
        return

    if not all_transactions:
        print("  -> No transactions could be extracted with the pattern-matching method.")
        return

    df = pd.DataFrame(all_transactions, columns=['Date', 'Description', 'Amount'])
    
    output_filename = f"extracted_{os.path.basename(pdf_path).replace('.pdf', '.csv')}"
    output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
    df.to_csv(output_path, index=False)
    
    print(f"  -> Success! Saved {len(df)} transactions to '{output_filename}'")


if __name__ == "__main__":
    print("--- Target PDF Extractor (Regex Version) ---")
    pdf_path = input("Please provide the path to a Target PDF statement file: ")
    extract_transactions_from_pdf(pdf_path.strip().replace("'", "").replace('"', ''))