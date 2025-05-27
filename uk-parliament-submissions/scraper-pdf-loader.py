# %% Imports and Setup
import os
import re
import time
import requests # Still useful for initial checks or non-PDF downloads if ever needed
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader # For text extraction after download
import urllib.parse # For joining relative URLs
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
# from selenium.webdriver.chrome.service import Service as ChromeService # Fallback
# from selenium.webdriver.firefox.service import Service as FirefoxService # Fallback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil # For moving/renaming files

# --- Configuration ---
BASE_URL = "https://committees.parliament.uk"
EVIDENCE_PAGE_URL = "https://committees.parliament.uk/work/8901/ai-in-financial-services/publications/written-evidence/"
DOWNLOAD_DIR_SCRAPER = os.path.abspath("parliament_ai_evidence_pdfs_scraper")
TARGET_PHRASE = "The paper explores how algorithmic high-frequency trading (HFT) in the credit risk market enables"
EXPECTED_PDF_COUNT = 82 # Target, for verification
HARDCODED_TOTAL_PAGES = 5

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR_SCRAPER, exist_ok=True)
print(f"Download directory set to: {DOWNLOAD_DIR_SCRAPER}")

# %% Helper Functions

def sanitize_filename(name):
    """Sanitizes a string to be used as a filename base (without extension)."""
    if not name:
        name = "unknown_document"
    name = str(name)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name).strip('-_')
    return name if name else "unnamed_document"

def extract_links_from_soup(soup, base_url_for_joining):
    """
    Helper function to extract PDF links and titles from a BeautifulSoup object.
    """
    page_links_with_titles = []
    # Regex to find links like /writtenevidence/12345/pdf or /writtenevidence/12345/pdf/
    pdf_link_pattern = re.compile(r"/writtenevidence/\d+/pdf/?$", re.IGNORECASE)
    all_matching_a_tags = soup.find_all('a', href=pdf_link_pattern)
    
    if not all_matching_a_tags and soup:
        print(f"    DEBUG: No links matching pattern '/writtenevidence/.../pdf/' found on current page/soup.")

    for link_tag in all_matching_a_tags:
        href = link_tag['href']
        full_url = urllib.parse.urljoin(base_url_for_joining, href)
        
        item_block = None
        current_ancestor = link_tag
        for _ in range(5): 
            parent = current_ancestor.find_parent()
            if not parent: break
            if parent.name in ['div', 'li', 'article', 'tr', 'section']: # Common block tags
                # Check if this parent contains text like "Published [date]"
                if parent.find(string=re.compile(r'Published \d{1,2} \w+ \d{4}', re.IGNORECASE)):
                    item_block = parent
                    break
            current_ancestor = parent
        
        if not item_block: 
            item_block = link_tag.find_parent(['div', 'li', 'article']) # Broader search

        title = f"Evidence_for_PDF_{os.path.basename(urllib.parse.urlparse(href).path).replace('/pdf','')}" 
        if item_block:
            # Try to find a heading (h3, h4) with 'title' in its class
            title_tag = item_block.find(['h3', 'h4'], class_=lambda x: x and 'title' in x.lower())
            if not title_tag:
                # Look for text with (AIFSXXXX) pattern as a strong indicator of the title line
                title_text_element = item_block.find(string=re.compile(r'\([A-Z0-9]{4,10}\)')) 
                if title_text_element:
                    title_container = title_text_element.find_parent()
                    # Try to get text from a sensible container, not the whole item_block if it's too large
                    if title_container and len(title_container.get_text(strip=True)) < 300 : 
                       title = title_container.get_text(separator=' ', strip=True)
                    else: # If container is too broad or no good parent, use the text node itself
                        title = title_text_element.strip()
                else: 
                    # Fallback: get first few prominent text nodes as potential title
                    all_text_nodes = item_block.find_all(string=True, recursive=False) # Prefer direct children text
                    if not all_text_nodes: all_text_nodes = item_block.find_all(string=True)
                    
                    candidate_titles = []
                    for t_node in all_text_nodes:
                        stripped_node = t_node.strip()
                        # Filter out common irrelevant short texts or known non-titles
                        if len(stripped_node) > 10 and \
                           not stripped_node.lower().startswith(('open pdf', 'open html', 'get file', 'published', 'total results', 'written evidence')):
                            candidate_titles.append(stripped_node)
                    
                    if candidate_titles:
                        title = candidate_titles[0] # Take the first plausible candidate
                    else: # Last resort: find any heading or paragraph
                        first_prominent_tag = item_block.find(['h3','h4','p', 'strong', 'b'])
                        title = first_prominent_tag.get_text(strip=True) if first_prominent_tag else title
            else: # title_tag was found
                title = title_tag.get_text(strip=True)
        
            # Clean up generic titles
            if "written evidence" in title.lower() and len(title) < 30: 
                 title = f"Evidence_for_PDF_{os.path.basename(urllib.parse.urlparse(href).path).replace('/pdf','')}"

        page_links_with_titles.append({'title': sanitize_filename(title), 'url': full_url})
    return page_links_with_titles

def download_pdf_with_selenium(driver, pdf_url, sanitized_filename_base, download_dir):
    """
    Navigates to the PDF URL using Selenium to trigger download and waits for it.
    Renames the downloaded file.
    """
    target_filename = f"{sanitized_filename_base}.pdf"
    target_filepath = os.path.join(download_dir, target_filename)

    if os.path.exists(target_filepath):
        print(f"File already exists: {target_filepath}. Skipping download.")
        return target_filepath

    print(f"  Attempting Selenium download for: {pdf_url} to {target_filename}")
    
    # List files before download to identify the new file later
    files_before = set(os.listdir(download_dir))
    
    try:
        driver.get(pdf_url)
        # Wait for the download to complete. This is the tricky part.
        # Strategy: wait for a new file to appear and stop changing size, or for temp file to disappear.
        download_wait_timeout = 120  # seconds to wait for download
        check_interval = 2       # seconds between checks
        time_waited = 0
        
        downloaded_file_path = None
        temp_download_extension = ".crdownload" # For Edge/Chrome

        while time_waited < download_wait_timeout:
            time.sleep(check_interval)
            time_waited += check_interval
            files_after = set(os.listdir(download_dir))
            new_files = files_after - files_before
            
            if not new_files:
                # print(f"    Still waiting for download... ({time_waited}s)")
                continue

            for fname in new_files:
                if fname.endswith(".pdf") and not fname.endswith(temp_download_extension):
                    # Check if file size is stable (optional, simple check here)
                    # More robust would be to check size multiple times.
                    downloaded_file_path = os.path.join(download_dir, fname)
                    print(f"    Detected downloaded PDF: {fname}")
                    break # Found a .pdf file
                elif fname.endswith(temp_download_extension):
                    # print(f"    Download in progress (temp file: {fname})... ({time_waited}s)")
                    pass # Continue waiting if temp file exists

            if downloaded_file_path: # A .pdf file (not .crdownload) has appeared
                # Wait a bit more to ensure writing is finished
                time.sleep(3)
                break 
        
        if downloaded_file_path:
            # Rename the downloaded file to our sanitized name
            if os.path.exists(downloaded_file_path) and downloaded_file_path != target_filepath:
                try:
                    # If target_filepath already exists (e.g. from a previous partial run), remove it first
                    if os.path.exists(target_filepath):
                        print(f"    Target file {target_filepath} exists, removing before rename.")
                        os.remove(target_filepath)
                    shutil.move(downloaded_file_path, target_filepath)
                    print(f"  Successfully downloaded and renamed to: {target_filepath}")
                    return target_filepath
                except Exception as e_rename:
                    print(f"  Error renaming downloaded file {downloaded_file_path} to {target_filepath}: {e_rename}")
                    return downloaded_file_path # Return original path if rename fails
            elif downloaded_file_path == target_filepath:
                 print(f"  Successfully downloaded: {target_filepath} (filename matched).")
                 return target_filepath
            else: # Should not happen if downloaded_file_path is set
                print(f"  Downloaded file path {downloaded_file_path} does not exist after download.")


        else:
            print(f"  Download timed out or failed to detect completed PDF for {pdf_url} after {download_wait_timeout}s.")
            # Check if there are any .crdownload files left that might indicate issues
            files_after_timeout = set(os.listdir(download_dir))
            new_files_after_timeout = files_after_timeout - files_before
            for fname_timeout in new_files_after_timeout:
                if fname_timeout.endswith(temp_download_extension):
                    print(f"    Found lingering temp file: {fname_timeout}. Download may have failed or stalled.")
            return None

    except Exception as e:
        print(f"  An error occurred during Selenium PDF download navigation for {pdf_url}: {e}")
        return None
    return None # Fallback

def get_and_download_all_pdfs(initial_page_url):
    """
    Main orchestrating function.
    Initializes Selenium, navigates pages, extracts links, and downloads PDFs using Selenium.
    """
    all_extracted_pdf_infos = []
    driver = None
    
    try:
        print("Initializing EdgeDriver for the scraping session...")
        edge_options = EdgeOptions()
        edge_options.add_argument('--headless')
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62")
        
        prefs = {
            "download.default_directory": DOWNLOAD_DIR_SCRAPER,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        edge_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Edge(options=edge_options)
        print("EdgeDriver initialized successfully with download preferences.")

        total_pages_to_scrape = HARDCODED_TOTAL_PAGES
        print(f"Hardcoded to scrape {total_pages_to_scrape} pages for PDF links.")

        for current_page_num in range(1, total_pages_to_scrape + 1):
            page_url_to_load = f"{initial_page_url}?page={current_page_num}" if current_page_num > 1 else initial_page_url
            print(f"\nFetching content from page: {page_url_to_load}")
            try:
                driver.get(page_url_to_load)
                # Wait for PDF links to be present on the page
                wait_condition = EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/writtenevidence/') and contains(@href, '/pdf/')]"))
                WebDriverWait(driver, 25).until(wait_condition) # Increased wait
                print(f"  Page {current_page_num} PDF links likely loaded.")
            except Exception as e_wait:
                print(f"  Timed out waiting for PDF links on page {current_page_num}, or no such links found: {str(e_wait).splitlines()[0]}")
                print(f"  Proceeding to parse current page source for page {current_page_num} anyway.")

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            page_links = extract_links_from_soup(soup, BASE_URL)
            
            if page_links:
                print(f"  Found {len(page_links)} PDF links on page {current_page_num}.")
                all_extracted_pdf_infos.extend(page_links)
            else:
                print(f"  No PDF links found on page {current_page_num} using the pattern.")
            
            if current_page_num < total_pages_to_scrape:
                time.sleep(1.5) # Increased politeness delay between page navigations

        # Deduplicate all found links before starting downloads
        unique_pdf_infos = []
        seen_urls = set()
        for item in all_extracted_pdf_infos:
            if item['url'] not in seen_urls:
                unique_pdf_infos.append(item)
                seen_urls.add(item['url'])
        
        print(f"\nTotal unique PDF links found across all pages: {len(unique_pdf_infos)}")
        all_extracted_pdf_infos = unique_pdf_infos # Use the deduplicated list

        # Now download each PDF using the same driver instance
        downloaded_pdf_details = []
        for i, pdf_info in enumerate(all_extracted_pdf_infos):
            print(f"\n--- Downloading PDF {i+1}/{len(all_extracted_pdf_infos)}: {pdf_info['title']} ---")
            pdf_path = download_pdf_with_selenium(driver, pdf_info['url'], pdf_info['title'], DOWNLOAD_DIR_SCRAPER)
            if pdf_path:
                downloaded_pdf_details.append({'title': pdf_info['title'], 'url': pdf_info['url'], 'local_path': pdf_path})
            else:
                print(f"Failed to download: {pdf_info['title']} from {pdf_info['url']}")
            time.sleep(1) # Small delay between initiating downloads

        return downloaded_pdf_details # Return list of dicts with local paths

    except Exception as e:
        print(f"A major error occurred in get_and_download_all_pdfs: {e}")
        import traceback
        traceback.print_exc()
        return [] # Return empty list on major failure
    finally:
        if driver:
            print("Closing Selenium WebDriver at the end of the session.")
            driver.quit()


def extract_text_from_pdf_path(pdf_path):
    """Extracts text from a PDF file path."""
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"PDF path invalid for text extraction: {pdf_path}")
        return None
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            if not reader.pages:
                print(f"Warning: No pages found in PDF {pdf_path}.")
                return None
            text = "".join(page.extract_text() + "\n" for page in reader.pages if page.extract_text())
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return None

# %% --- Main Execution ---

# %% 1. Get PDF Links and Download PDFs using Selenium
print("Starting the process to fetch PDF links and download them using Selenium...")
# This function now handles both link extraction and downloads
downloaded_pdfs_info = get_and_download_all_pdfs(EVIDENCE_PAGE_URL) 

if not downloaded_pdfs_info:
    print("No PDFs were successfully downloaded. Exiting.")
else:
    print(f"\nSuccessfully processed and attempted download for {len(downloaded_pdfs_info)} PDF items.")

# %% 2. Verify Count (based on successfully downloaded and processed items)
    # Note: This count is now based on what was actually downloaded and has a local_path.
    # The `EXPECTED_PDF_COUNT` might be compared against `len(downloaded_pdfs_info)` if all downloads are expected to succeed.
    # Or against the number of links initially found if that's the metric.
    # For now, let's use the count of items for which download was attempted.
    
    # Let's count how many actually have a valid local_path (meaning download was successful)
    successfully_downloaded_files = [item for item in downloaded_pdfs_info if item.get('local_path')]
    print(f"Number of PDFs successfully downloaded: {len(successfully_downloaded_files)}")

    if len(successfully_downloaded_files) == EXPECTED_PDF_COUNT:
        print(f"\nSUCCESS: Exactly {EXPECTED_PDF_COUNT} PDFs appear to have been successfully downloaded.")
    else:
        print(f"\nWARNING: {len(successfully_downloaded_files)} PDFs were successfully downloaded, but expected {EXPECTED_PDF_COUNT}. Please verify.")

# %% 3. Extract Text and Check for Specific Phrase from downloaded files
    phrase_found_in_files = []
    processed_for_text_count = 0

    print(f"\nExtracting text from {len(successfully_downloaded_files)} downloaded PDF items...")
    for i, pdf_item_info in enumerate(successfully_downloaded_files):
        print(f"\n--- Extracting text from PDF {i+1}/{len(successfully_downloaded_files)}: {pdf_item_info['title']} ---")
        
        text_content = extract_text_from_pdf_path(pdf_item_info['local_path'])
        if text_content:
            processed_for_text_count += 1
            if TARGET_PHRASE in text_content:
                print(f"SUCCESS: Target phrase FOUND in: {pdf_item_info['title']} ({pdf_item_info['local_path']})")
                phrase_found_in_files.append({'title': pdf_item_info['title'], 'path': pdf_item_info['local_path']})
        else:
            print(f"Could not extract text (or text was empty) from: {pdf_item_info['title']} ({pdf_item_info['local_path']})")
        
# %% 4. Report Findings
    print("\n--- Final Scraping Report ---")
    print(f"Total unique PDF links targeted for download: {len(downloaded_pdfs_info)}") # Number of items get_and_download_all_pdfs returned
    print(f"Total PDFs successfully downloaded (verified by path): {len(successfully_downloaded_files)}")
    print(f"Total PDFs processed for text extraction: {processed_for_text_count}")

    # Adjusting count check based on links found vs. expected
    # The `downloaded_pdfs_info` contains all items for which download was ATTEMPTED.
    # `len(successfully_downloaded_files)` is a better measure for actual downloads.
    
    # Let's assume initial_links_found is what we want to compare with EXPECTED_PDF_COUNT
    # This info is implicitly len(downloaded_pdfs_info) before filtering for successful downloads
    initial_links_found = len(downloaded_pdfs_info) # Or pass this from the link extraction step if separated
    
    if initial_links_found == EXPECTED_PDF_COUNT:
        print(f"Count Check (Links Found): Successfully identified {EXPECTED_PDF_COUNT} PDF links for download attempt.")
    else:
        print(f"Count Check (Links Found): Identified {initial_links_found} PDF links for download attempt, target was {EXPECTED_PDF_COUNT}.")


    if phrase_found_in_files:
        print(f"\nTarget phrase '{TARGET_PHRASE}' was FOUND in the following {len(phrase_found_in_files)} file(s):")
        for finding in phrase_found_in_files:
            print(f"  - Title: {finding['title']}, Path: {finding['path']}")
    else:
        print(f"\nTarget phrase '{TARGET_PHRASE}' was NOT FOUND in any of the successfully processed PDFs.")

print("\nScraping script finished.")

# %%
