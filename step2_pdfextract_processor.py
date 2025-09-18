import pandas as pd
import os
import hashlib

def process_pdf_extract(input_path):
    """
    Takes a CSV extracted from a PDF and adds the final columns needed for the main importer.
    """
    try:
        df = pd.read_csv(input_path)

        # --- 1. Standardize Columns ---
        # The PDF extractor already creates Date, Description, Amount. We just ensure the format is right.
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        df['Category'] = ''
        df['Source'] = os.path.basename(input_path)

        # --- 2. Create Unique Transaction ID ---
        def create_id(row):
            return hashlib.md5(f"{row['Date']}{row['Description']}{row['Amount']}".encode()).hexdigest()
        
        df['TransactionID'] = df.apply(create_id, axis=1)
        
        # --- 3. Finalize the Output ---
        final_columns = ['Date', 'Description', 'Amount', 'Category', 'Source', 'TransactionID']
        df_final = df[final_columns]
        
        output_filename = f"processed_{os.path.basename(input_path)}"
        output_path = os.path.join(os.path.dirname(input_path), output_filename)
        df_final.to_csv(output_path, index=False)
        print(f"\n✅ Success! Standardized PDF extract created at: {output_path}")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("--- PDF Extract Processor ---")
    csv_file_path = input("Please provide the path to a CSV file created by the PDF extractor: ")
    cleaned_path = csv_file_path.strip().replace("'", "").replace('"', '')
    process_pdf_extract(cleaned_path)