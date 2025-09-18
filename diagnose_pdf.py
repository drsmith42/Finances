import pdfplumber
import os
import sys

def diagnose_pdf_structure(pdf_path):
    """
    Opens a PDF and prints any extracted table data from EVERY page
    to help understand its structure.
    """
    print(f"--- Diagnosing PDF (All Pages): {os.path.basename(pdf_path)} ---")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print("PDF appears to have no pages.")
                return

            # --- Loop through every page in the PDF ---
            for i, page in enumerate(pdf.pages):
                print(f"\n\n--- Raw Table Data on Page {i+1} ---")
                
                # Use the extract_table() function to find a table on the current page
                table = page.extract_table()
                
                if table:
                    # A table was found, print each of its rows
                    print(f"A table was found on Page {i+1}. Here are its raw rows:")
                    for j, row in enumerate(table):
                        print(f"  Page {i+1}, Row {j}: {row}")
                else:
                    print(f"!! No table structure could be automatically detected on Page {i+1}.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Please provide the path to the PDF file you want to diagnose: ")
    
    diagnose_pdf_structure(pdf_path.strip().replace("'", "").replace('"', ''))