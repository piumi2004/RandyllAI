
from pathlib import Path
import pymupdf

PDF_PATH = Path("data/pdfs/Korea Student Admission Information - chatbot - Copy.pdf")
OUTPUT_DIR = Path("data/report_pages")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not PDF_PATH.is_file():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

with pymupdf.open(PDF_PATH) as pdf:
    print(f"Total PDF pages: {len(pdf)}")

    for page_no, page in enumerate(pdf, start=1):
        text = page.get_text("text", sort=True).strip()

        content = (
            f"SOURCE: {PDF_PATH.name}\n"
            f"PHYSICAL_PDF_PAGE: {page_no}\n\n"
            f"{text}\n"
        )

        output_file = OUTPUT_DIR / f"page_{page_no:03d}.txt"
        output_file.write_text(content, encoding="utf-8")

        if len(text) < 40:
            print(f"CHECK PAGE {page_no}: Little or no text extracted")

    print("Page extraction completed.")
