# %% Imports and Setup
import os
import glob
import pandas as pd
from PyPDF2 import PdfReader
import logging # For consistency with model_completions.py logging

# Assuming model_completions.py is in the same directory
try:
    from model_completions import process_df_prompts # Key function to use
except ImportError:
    print("ERROR: model_completions.py not found. Make sure it's in the same directory or accessible in PYTHONPATH.")
    exit()

# Configure basic logging for this script if desired, or rely on model_completions logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- Configuration ---
PDF_DOWNLOAD_DIR = "parliament_ai_evidence_pdfs_api" # From previous script
SUMMARIES_OUTPUT_CSV = "parliament_ai_evidence_summaries.csv"
CLAUDE_MAX_TOKENS_SUMMARY = 700 # Max tokens for the summary from Claude. Adjust as needed.
                                # The default in process_df_prompts is 100, which is too low for summaries.

# %% Helper Function - PDF Text Extraction (adapted from previous script)

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file path.
    Returns the extracted text as a string or None if extraction fails.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        logger.warning(f"PDF path invalid or file does not exist: {pdf_path}")
        return None
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            text = ""
            if len(reader.pages) == 0:
                logger.warning(f"No pages found in PDF: {pdf_path}")
                return None
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            logger.warning(f"No text extracted from {pdf_path}. The PDF might be image-based or scanned.")
            return None
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
    return None

# %% --- Main Execution ---

# %% 1. Check for ANTHROPIC_API_KEY
logger.info("Checking for ANTHROPIC_API_KEY environment variable...")
if not os.environ.get("ANTHROPIC_API_KEY"):
    logger.error("FATAL: ANTHROPIC_API_KEY environment variable not set.")
    logger.error("Please set this environment variable before running the script.")
    # exit() # Exiting might be too abrupt if running in blocks, let process_df_prompts handle it
    api_key_set = False
else:
    logger.info("ANTHROPIC_API_KEY seems to be set.")
    api_key_set = True

# %% 2. Prepare PDF Data for Summarization
if api_key_set:
    logger.info(f"Looking for PDF files in: {PDF_DOWNLOAD_DIR}")
    pdf_files = glob.glob(os.path.join(PDF_DOWNLOAD_DIR, "*.pdf"))
    pdf_files = pdf_files[:5]

    if not pdf_files:
        logger.warning(f"No PDF files found in {PDF_DOWNLOAD_DIR}. Ensure the previous script ran successfully and downloaded PDFs.")
        # exit()
        docs_to_process = []
    else:
        logger.info(f"Found {len(pdf_files)} PDF files to process.")
        
        documents_data = []
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            # Attempt to get a cleaner title (remove .pdf and potentially sanitize_filename remnants)
            title = filename.replace(".pdf", "").replace("_", " ").strip() # Basic cleaning
            
            logger.info(f"Extracting text from: {filename}")
            extracted_text = extract_text_from_pdf(pdf_path)
            
            if extracted_text:
                # Truncate very long texts if necessary, though Claude Sonnet handles large contexts
                # Max context for Sonnet 3.5 is 200K tokens. Let's be generous but mindful.
                # Average token is ~4 chars. 200K tokens ~ 800K chars.
                # The model used in model_completions.py is "claude-3-7-sonnet-20250219"
                # which may have different limits.
                # For now, we pass the full text. Claude API will truncate if needed or error.
                max_input_chars = 750000 # Heuristic limit, adjust if needed
                if len(extracted_text) > max_input_chars:
                    logger.warning(f"Text from {filename} is very long ({len(extracted_text)} chars), truncating to {max_input_chars} for summarization.")
                    extracted_text = extracted_text[:max_input_chars]

                documents_data.append({
                    'pdf_filename': filename,
                    'pdf_title': title,
                    'full_text_for_claude': extracted_text # This will be our "user prompt"
                })
            else:
                logger.warning(f"Skipping {filename} due to text extraction failure or empty content.")
        
        docs_to_process = documents_data

    # Create DataFrame
    if docs_to_process:
        df_for_summaries = pd.DataFrame(docs_to_process)
        logger.info(f"Created DataFrame with {len(df_for_summaries)} documents for summarization.")
    else:
        df_for_summaries = pd.DataFrame() # Empty dataframe
        logger.info("No documents to process for summarization.")
else:
    logger.warning("Skipping summarization process as ANTHROPIC_API_KEY is not set.")
    df_for_summaries = pd.DataFrame()

# %% 3. Define System Prompt and Call Claude for Summaries
if not df_for_summaries.empty and api_key_set:
    system_prompt_summarize = (
        "You are an expert research assistant. Your task is to analyze written evidence submitted to a UK Parliament committee "
        "regarding 'AI in Financial Services'. Based *only* on the provided text from a single piece of written evidence, "
        "please provide a concise summary covering the following aspects:\n"
        "1. The key organization or individual who likely submitted the evidence (if discernible from the text).\n"
        "2. The main arguments or points made concerning AI in financial services.\n"
        "3. Any specific technologies, applications, benefits, or risks of AI highlighted.\n"
        "4. Key recommendations or calls to action directed at the government, regulators, or industry.\n"
        "5. The overall sentiment or stance expressed (e.g., optimistic, cautious, critical, balanced).\n"
        "Focus on extracting factual information and clearly stated opinions from the text. Do not add external knowledge. "
        "The summary should be well-structured and easy to read."
    )

    logger.info("Starting summarization process using Claude via process_df_prompts...")
    # Ensure the 'user_prompt_col' matches the column name in df_for_summaries
    # Ensure the 'result_col' is what you want the summary column to be named
    
    # Note: model_completions.py uses max_workers=1 by default, so it will be sequential.
    # This is good for avoiding API rate limits initially.
    summarized_df = process_df_prompts(
        df=df_for_summaries,
        model_type="claude", # As requested
        system_prompt=system_prompt_summarize,
        user_prompt_col='full_text_for_claude', # Column containing the extracted PDF text
        result_col='claude_summary', # New column for the generated summary
        max_tokens=CLAUDE_MAX_TOKENS_SUMMARY, # Max tokens for the summary itself
        temperature=0.5, # Lower temperature for more factual summaries
        show_progress=True
    )

    logger.info("Summarization process completed.")

    # %% 4. Save Summaries
    if 'claude_summary' in summarized_df.columns:
        try:
            summarized_df.to_csv(SUMMARIES_OUTPUT_CSV, index=False, encoding='utf-8')
            logger.info(f"Summaries saved to: {SUMMARIES_OUTPUT_CSV}")
            # Display a sample of the results
            logger.info("\nSample of summaries (first 3 rows):")
            logger.info(summarized_df[['pdf_title', 'claude_summary']].head(3))
        except Exception as e:
            logger.error(f"Error saving summaries to CSV: {e}")
    else:
        logger.warning("No 'claude_summary' column found in the results. Cannot save summaries.")
        logger.info("Resulting DataFrame columns: " + str(summarized_df.columns))

elif not api_key_set:
    logger.info("Summarization skipped because ANTHROPIC_API_KEY was not set.")
else:
    logger.info("No documents were prepared for summarization. Output file will not be created.")

logger.info("\nScript finished.")