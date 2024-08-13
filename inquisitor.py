import os
from PyPDF2 import PdfReader
from colorama import init, Fore, Style
import sys
import signal

# Initialize colorama
init()

# Paths for the output files
output_ocred_file = 'output_ocred.txt'
output_image_file = 'output_image.txt'
output_doublecheck_file = 'output_doublecheck.txt'

# Flag to track if the process should be stopped
stop_processing = False

# Handle interrupts to stop processing gracefully
def signal_handler(sig, frame):
    global stop_processing
    stop_processing = True
    print(f"\n{Fore.YELLOW}Processing stopped by user. Exiting...{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Load the paths of already processed files
def load_processed_files(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

# Write a file path to the specified output file
def write_to_output_file(filename, path):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(path + '\n')
    except IOError as e:
        print(f"{Fore.RED}Error writing to {filename}: {e}{Style.RESET_ALL}")

# Check if a specific page in the PDF has text
def page_has_text(pdf, page_number):
    try:
        page = pdf.pages[page_number]
        text = page.extract_text()
        return text is not None and len(text.strip()) > 0
    except IndexError:
        return False

# Process a single PDF file
def process_pdf(pdf_path, processed_ocred, processed_image, processed_doublecheck):
    status_message = "Unknown status"  # Initialize with a default value

    # Skip if already processed
    if pdf_path in processed_ocred or pdf_path in processed_image or pdf_path in processed_doublecheck:
        return None  # Indicate no status change

    try:
        # Check if the PDF file exists
        if not os.path.isfile(pdf_path):
            print(f"{Fore.YELLOW}File not found: {pdf_path}{Style.RESET_ALL}")
            return None  # Indicate no status change

        pdf = PdfReader(pdf_path)
        num_pages = len(pdf.pages)

        # Determine pages to check
        pages_to_check = []
        if num_pages >= 36:
            pages_to_check = [8, 16, 34]  # 0-based index
        elif num_pages >= 18:
            pages_to_check = [8, 16, num_pages - 1]
        elif num_pages >= 9:
            pages_to_check = [8, num_pages - 1]
        else:
            pages_to_check = [0, num_pages - 1]

        # Check the pages
        text_found = False
        no_text_pages = 0
        has_text_pages = 0

        for page in pages_to_check:
            if stop_processing:
                return None  # Stop processing if a stop signal is received
            if page_has_text(pdf, page):
                has_text_pages += 1
                text_found = True
            else:
                no_text_pages += 1

        # Classification based on pages with text
        if has_text_pages > 0 and no_text_pages == 0:
            write_to_output_file(output_ocred_file, pdf_path)
            status_message = "File with OCR text"
        elif has_text_pages > 0 and no_text_pages > 0:
            write_to_output_file(output_doublecheck_file, pdf_path)
            status_message = "File with some OCR text (needs double-check)"
        else:
            write_to_output_file(output_image_file, pdf_path)
            status_message = "File without OCR text"

    except IOError as e:
        print(f"{Fore.RED}IOError processing {pdf_path}: {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error processing {pdf_path}: {e}{Style.RESET_ALL}")

    return status_message

# Recursively process directories to find PDF files
def process_directories(root_dir, processed_ocred, processed_image, processed_doublecheck):
    total_files = 0
    processed_files = 0

    pdf_files_list = []

    for root, _, files in os.walk(root_dir):
        pdf_files = [os.path.join(root, f) for f in files if f.lower().endswith('.pdf')]
        pdf_files_list.extend(pdf_files)
        total_files += len(pdf_files)

    print(f"{Fore.YELLOW}Total PDF files to process: {total_files}{Style.RESET_ALL}")

    for i, pdf_path in enumerate(pdf_files_list):
        if stop_processing:
            return  # Stop processing if a stop signal is received
        status_message = process_pdf(pdf_path, processed_ocred, processed_image, processed_doublecheck)
        if status_message:
            processed_files += 1

        # Dynamic progress bar update
        progress = (i + 1) / total_files * 100
        sys.stdout.write(f"\r{Fore.GREEN}Processing: {processed_files}/{total_files} files ({progress:.2f}% complete) - {status_message}{Style.RESET_ALL}")
        sys.stdout.flush()

    print(f"\n{Fore.MAGENTA}Summary for {root_dir}:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total files found: {total_files}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Files processed: {processed_files}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Files with OCR text: {len(load_processed_files(output_ocred_file))}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Files needing double-check: {len(load_processed_files(output_doublecheck_file))}{Style.RESET_ALL}")
    print(f"{Fore.RED}Files without OCR text: {len(load_processed_files(output_image_file))}{Style.RESET_ALL}")

# Main function to process the PDFs
def process_pdfs(paths_file):
    # Load already processed files
    processed_ocred = load_processed_files(output_ocred_file)
    processed_image = load_processed_files(output_image_file)
    processed_doublecheck = load_processed_files(output_doublecheck_file)

    # Read the paths from paths.txt
    try:
        with open(paths_file, 'r', encoding='utf-8') as f:
            folder_paths = f.read().splitlines()
    except IOError as e:
        print(f"{Fore.RED}Error reading {paths_file}: {e}{Style.RESET_ALL}")
        return

    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            print(f"{Fore.RED}Directory not found: {folder_path}{Style.RESET_ALL}")
            continue
        
        # Process the directory and its subdirectories
        print(f"{Fore.YELLOW}Processing directory: {folder_path}{Style.RESET_ALL}")
        process_directories(folder_path, processed_ocred, processed_image, processed_doublecheck)

# Run the script
if __name__ == "__main__":
    process_pdfs('paths.txt')
