import pandas as pd
import os

MASTER_FILE_PATH = "master_transactions.csv"

def main():
    print("--- Category Diagnoser ---")
    
    if not os.path.exists(MASTER_FILE_PATH):
        print(f"❌ ERROR: Master file not found at '{MASTER_FILE_PATH}'.")
        return

    try:
        df = pd.read_csv(MASTER_FILE_PATH)
        
        # Drop rows where the category is empty to focus on filled ones
        unique_categories = df['Category'].dropna().unique()

        if len(unique_categories) == 0:
            print("No categories found in the file.")
            return

        print("\nFound the following unique values in your 'Category' column:")
        print("---------------------------------------------------------")
        for category in unique_categories:
            # We print the category in quotes and show its length to easily spot extra spaces
            print(f"Value: '{category}' (Length: {len(str(category))})")
        print("---------------------------------------------------------")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()