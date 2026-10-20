from pathlib import Path
import fitz
import json

PDF_DIR = Path("data/pdfs")
OUTPUT = Path("data/extracted.json")

documents = []

for pdf_path in PDF_DIR.glob("*.pdf"):
    print(f"Processing: {pdf_path.name}")

    with fitz.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if not text:
                print(
                    f"WARNING: No text found on "
                    f"{pdf_path.name}, page {page_number}"
                )
                continue

            documents.append({
                "filename": pdf_path.name,
                "page": page_number,
                "text": text
            })

OUTPUT.write_text(
    json.dumps(documents, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"Extracted {len(documents)} pages")