"""
===============================================================================
                    Dharma AI - PDF Text Extraction
===============================================================================

Purpose:
--------
Extract raw text from all legal PDF documents stored in data/raw_pdfs/
using PyMuPDF and save:

1. Full extracted text (.txt)
2. Page-wise structured JSON (.json)

Project Structure
-----------------

AI-Legal-Chatbot/
│
├── data/
│   ├── raw_pdfs/
│   ├── extracted_text/
│   ├── cleaned_text/
│   ├── chunks/
│   ├── metadata/
│   ├── embeddings/
│   └── vector_db/
│
└── src/
    └── preprocessing/
        └── pdf_extractor.py

Author : Dharma AI
===============================================================================
"""

import json
import os
import re
from pathlib import Path

try:
    import fitz
except ModuleNotFoundError:
    fitz = None

# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"
OUTPUT_DIR = PROJECT_ROOT / "data" / "extracted_text"
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "test_data"

TARGET_PDF_FILES = [
    "Bharatiya_Nagarik_Suraksha_Sanhita_.pdf",
    "Bharatiya_Nyaya_Sanhita.pdf",
    "Bharatiya_Sakshya_Adhiniyam_2023.pdf",
    "Consumer_Protection_Act_2019.pdf",
    "Information_Technology_Act_2000.pdf",
    "Motor_Vehicles_Act_1988.pdf",
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# CLEAN TEXT
# =============================================================================

def clean_text(raw_text: str) -> str:
    """
    Performs basic cleaning while preserving legal formatting.
    """

    lines = raw_text.split("\n")
    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Remove page numbers like:
        # 10
        # -10-
        # — 10 —
        if re.fullmatch(r"[-–—]?\s*\d+\s*[-–—]?", line):
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Remove multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =============================================================================
# GET ALL PDF FILES
# =============================================================================

def get_pdf_files(folder: Path):
    """
    Returns the six selected PDFs inside data/raw_pdfs.
    """

    selected_files = []

    for filename in TARGET_PDF_FILES:
        pdf_path = folder / filename
        if pdf_path.exists():
            selected_files.append(pdf_path)

    return sorted(selected_files)


# =============================================================================
# EXTRACT ONE PDF
# =============================================================================

def extract_pdf(pdf_path: Path):

    if fitz is None:
        raise ModuleNotFoundError(
            "PyMuPDF is not installed. Install it using: pip install pymupdf"
        )

    document_name = pdf_path.stem

    print(f"\nProcessing : {document_name}")

    doc = fitz.open(pdf_path)

    pages = []
    full_text = []

    for page_number, page in enumerate(doc, start=1):

        raw_text = page.get_text("text")

        cleaned = clean_text(raw_text)

        if not cleaned:
            continue

        pages.append({

            "document": document_name,

            "page_number": page_number,

            "text": cleaned,

            "metadata": {}

        })

        full_text.append(cleaned)

    txt_output = OUTPUT_DIR / f"{document_name}.txt"
    test_txt_output = TEST_OUTPUT_DIR / f"{document_name}.txt"

    with open(txt_output, "w", encoding="utf-8") as f:
        f.write("\n\n".join(full_text))

    with open(test_txt_output, "w", encoding="utf-8") as f:
        f.write("\n\n".join(full_text))

    json_output = OUTPUT_DIR / f"{document_name}_pages.json"

    with open(json_output, "w", encoding="utf-8") as f:

        json.dump({

            "document": document_name,

            "source_file": pdf_path.name,

            "total_pages": len(pages),

            "pages": pages

        }, f, indent=4, ensure_ascii=False)

    doc.close()

    print("✓ Text File :", txt_output.name)
    print("✓ JSON File :", json_output.name)
    print("✓ Pages Extracted :", len(pages))


# =============================================================================
# MAIN
# =============================================================================

def main():

    pdf_files = get_pdf_files(RAW_PDF_DIR)

    if not pdf_files:

        print("No PDF files found.")

        print(f"Place PDFs inside:\n{RAW_PDF_DIR}")

        return

    print("=" * 70)
    print(" Dharma AI - PDF Extraction")
    print("=" * 70)

    print(f"\nFound {len(pdf_files)} PDF(s).\n")

    for pdf in pdf_files:

        extract_pdf(pdf)

    print("\n")
    print("=" * 70)
    print("Extraction Completed Successfully")
    print("=" * 70)


# =============================================================================

if __name__ == "__main__":

    main()