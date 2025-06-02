#!/usr/bin/env python3
"""
Find PDFs containing 'agent' or 'tool' and move them to a subfolder.
Uses pypdfium2 for reliable PDF text extraction.
"""

import os
import shutil
from pathlib import Path
import pypdfium2 as pdfium

def contains_keywords(pdf_path, keywords):
    """Check if PDF contains any of the keywords."""
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            textpage.close()
            page.close()
            
            if text:
                text_lower = text.lower()
                for keyword in keywords:
                    if keyword in text_lower:
                        pdf.close()
                        return True
        pdf.close()
    except Exception as e:
        print(f"Error reading {pdf_path.name}: {e}")
    return False

def main():
    # Configuration
    source_dir = Path("2025-05-UKParliament-Evidence")
    target_dir = source_dir / "agent_tool_pdfs"
    keywords = ["agent"]
    
    # Verify we're in the right directory
    if not source_dir.exists():
        print(f"Error: Directory '{source_dir}' not found.")
        print(f"Current directory: {Path.cwd()}")
        print("Make sure you're in the uk-parliament-submissions directory")
        return
    
    # Create target directory
    target_dir.mkdir(exist_ok=True)
    
    # Get all PDF files
    pdf_files = list(source_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {source_dir}")
    print(f"Will move matching files to: {target_dir}\n")
    
    moved_count = 0
    
    # Process each PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Checking: {pdf_path.name}", end=" ... ")
        
        if contains_keywords(pdf_path, keywords):
            # Move file
            target_path = target_dir / pdf_path.name
            shutil.move(str(pdf_path), str(target_path))
            print("✓ Found keywords - Moved")
            moved_count += 1
        else:
            print("✗ No match")
    
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Total PDFs processed: {len(pdf_files)}")
    print(f"  PDFs with keywords: {moved_count}")
    print(f"  Moved to: {target_dir}")

if __name__ == "__main__":
    main()