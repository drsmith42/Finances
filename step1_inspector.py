import pandas as pd
import os
import sys

def inspect_file():
    """
    A diagnostic tool to read a CSV or a specific sheet from an XLSX file
    and display its column names and a user-specified number of rows.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- Universal File Inspector ---")
    
    try:
        input_path = input("Please drag and drop your CSV or XLSX file, or type the full path: ").strip().replace("'", "").replace('"', '')

        if not os.path.exists(input_path):
            print(f"❌ ERROR: File not found at '{input_path}'")
            return

        df = None
        
        # Handle both CSV and XLSX files
        if input_path.lower().endswith('.csv'):
            df = pd.read_csv(input_path, on_bad_lines='skip')
        
        elif input_path.lower().endswith('.xlsx'):
            try:
                xls = pd.ExcelFile(input_path)
                sheet_names = xls.sheet_names
                
                if not sheet_names:
                    print("❌ ERROR: This Excel file contains no sheets.")
                    return

                print("\nSheets found in this Excel file:")
                for i, name in enumerate(sheet_names):
                    print(f"  [{i+1}] {name}")
                
                while True:
                    sheet_choice_str = input("\nEnter the number of the sheet to inspect: ").strip()
                    try:
                        sheet_choice = int(sheet_choice_str)
                        if 1 <= sheet_choice <= len(sheet_names):
                            selected_sheet = sheet_names[sheet_choice - 1]
                            df = pd.read_excel(input_path, sheet_name=selected_sheet)
                            break
                        else:
                            print("Invalid number.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            except ImportError:
                 print("\n❌ ERROR: The 'openpyxl' library is required to read Excel files.")
                 print("   Please install it by running: pip install openpyxl")
                 return
            except Exception as e:
                print(f"\n❌ An error occurred while reading the Excel file: {e}")
                return
        else:
            print("❌ ERROR: Unsupported file type. Please provide a .csv or .xlsx file.")
            return

        print("\n✅ File/Sheet read successfully!")
        print("------------------------------")
        print("COLUMN NAMES:")
        print(df.columns.tolist())
        print("------------------------------")

        # --- REWRITTEN SECTION: User-defined row selection ---
        while True:
            total_rows = len(df)
            prompt = (
                f"\nEnter rows to display (1-{total_rows}). "
                "Examples: '5' (first 5), '10-22' (a range), or 'all': "
            )
            rows_input = input(prompt).strip().lower()

            try:
                if rows_input == 'all':
                    print("\n--- FULL DATA ---")
                    print(df.to_string())
                    break

                elif '-' in rows_input:
                    parts = rows_input.split('-')
                    if len(parts) != 2:
                        raise ValueError("Range must be in 'start-end' format.")
                    
                    start_row = int(parts[0])
                    end_row = int(parts[1])

                    # Validate the user's 1-based input
                    if not (1 <= start_row <= end_row <= total_rows):
                        print(f"❌ Invalid range. Please enter numbers between 1 and {total_rows}.")
                        continue
                    
                    print(f"\n--- ROWS {start_row} TO {end_row} ---")
                    # Convert 1-based user input to 0-based pandas slice
                    print(df.iloc[start_row - 1:end_row].to_string())
                    break

                else:
                    num_rows = int(rows_input)
                    if not (1 <= num_rows <= total_rows):
                        print(f"❌ Invalid number. Please enter a number between 1 and {total_rows}.")
                        continue

                    print(f"\n--- FIRST {num_rows} ROWS ---")
                    print(df.head(num_rows).to_string())
                    break

            except ValueError:
                print("❌ Invalid input. Please follow the format examples (e.g., '5', '10-22', 'all').")
        # --- END REWRITTEN SECTION ---
        
        print("------------------------------")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    inspect_file()