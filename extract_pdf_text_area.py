import pdfplumber
import sys

def extract_text_from_area(pdf_path, page_number):
    """
    Goes to a specific page and prints the raw text from the main transaction area.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < page_number:
                print(f"Error: PDF only has {len(pdf.pages)} pages. Please enter a valid page number.")
                return

            page = pdf.pages[page_number - 1]
            
            # Define a bounding box to isolate the main body of the page
            page_height = page.height
            bounding_box = (40, page_height * 0.15, page.width - 40, page_height * 0.85)
            cropped_page = page.crop(bounding_box)

            print(f"\n--- Raw Text from Cropped Area on Page {page_number} ---")
            
            # Extract text with layout preservation to see how lines are structured
            text = cropped_page.extract_text(x_tolerance=2, y_tolerance=2, layout=True)
            
            if text:
                print(text)
            else:
                print("!! No text could be extracted from this area on this page.")
            print("--- End of Raw Text ---")
            print("\nPlease copy and paste the entire block of text above.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("--- Advanced PDF Text Area Extractor ---")
    pdf_path = input("Enter path to the PDF: ")
    page_num_str = input("Enter the page number with the main transaction list: ")
    try:
        page_num = int(page_num_str)
        extract_text_from_area(pdf_path.strip().replace("'", "").replace('"', ''), page_num)
    except ValueError:
        print("Invalid page number. Please enter an integer.")