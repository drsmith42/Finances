import pdfplumber
import os
import sys

def visual_debug_pdf(pdf_path, page_number):
    """
    Generates a debug image of a PDF page, showing what the table finder "sees".
    """
    output_filename = "debug_output.png"
    print(f"--- Visual PDF Debugger ---")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages or len(pdf.pages) < page_number:
                print(f"❌ ERROR: PDF does not have a page {page_number}.")
                return

            # Select the specific page the user wants to debug
            page = pdf.pages[page_number - 1]
            
            print(f"Generating debug image for Page {page_number}...")
            
            # Create an image of the page
            im = page.to_image(resolution=150)
            
            # Use the built-in debugger to draw the detected table structure
            # This will draw red circles for character positions, blue lines for detected edges,
            # and thick blue rectangles for the table areas it finds.
            im.debug_tablefinder()
            
            im.save(output_filename)
            
            print(f"\n✅ Success! A debug image has been saved as '{output_filename}'.")
            print("Please upload this file for review.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    pdf_path = input("Please provide the path to the PDF file you want to diagnose: ").strip().replace("'", "").replace('"', '')
    
    try:
        page_num_str = input("Enter the page number with the transactions (e.g., 2 or 3): ")
        page_num = int(page_num_str)
        visual_debug_pdf(pdf_path, page_num)
    except ValueError:
        print("Invalid page number. Please enter a number.")