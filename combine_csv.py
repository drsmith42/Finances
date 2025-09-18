import pandas as pd
import os
import sys

def combine_csv_files_in_folder(folder_path):
    """
    Finds all CSV files in a folder, checks for consistent headers,
    prompts the user for an institution name, and combines them into
    a single, descriptively named CSV file.
    """
    print(f"--- CSV Combiner ---")
    
    if not os.path.isdir(folder_path):
        print(f"❌ ERROR: The path provided is not a valid folder: '{folder_path}'")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.csv')]
    
    if len(csv_files) < 1:
        print("No CSV files found in the folder.")
        return
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # --- Header Consistency Check (if more than one file) ---
    if len(csv_files) > 1:
        try:
            first_file_path = os.path.join(folder_path, csv_files[0])
            master_header = pd.read_csv(first_file_path, nrows=0).columns.tolist()
            print(f"Reference header from '{csv_files[0]}': {master_header}")

            for filename in csv_files[1:]:
                file_path = os.path.join(folder_path, filename)
                current_header = pd.read_csv(file_path, nrows=0).columns.tolist()
                if current_header != master_header:
                    print(f"\n❌ ERROR: Header mismatch in file '{filename}'.")
                    print("Aborting combination.")
                    return
        except Exception as e:
            print(f"An error occurred while reading file headers: {e}")
            return
        print("\n✅ All CSV files have matching headers. Proceeding with combination.")
    
    # --- Combine Files ---
    all_dataframes = []
    for filename in csv_files:
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)
        all_dataframes.append(df)
        
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # --- NEW: Prompt for Filename and Save ---
    print(f"\nSuccessfully combined {len(combined_df)} rows.")
    institution_name = input("Please enter a short name for the institution (e.g., 'usbank_cc', 'target', 'amex'): ").lower().strip().replace(" ", "_")
    
    if not institution_name:
        print("No name entered. Aborting save.")
        return
        
    output_filename = f"{institution_name}_combined.csv"
    output_path = os.path.join(folder_path, output_filename)
    combined_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Success! Combined file saved as '{output_path}'.")


if __name__ == "__main__":
    folder_path = input("Please provide the path to the folder containing your CSV files: ")
    combine_csv_files_in_folder(folder_path.strip().replace("'", "").replace('"', ''))