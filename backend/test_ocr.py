from pathlib import Path

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption
)

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions
)

# Enable OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

# Create converter
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

# Documents to test
pdf_files = [
    "Jeonbuk National Master_s.pdf",
    "Kyungpook National University Undergraduate.pdf"
]

input_folder = Path("data/pdfs")
output_folder = Path("data/ocr_output")

output_folder.mkdir(
    parents=True,
    exist_ok=True
)

for filename in pdf_files:

    pdf_path = input_folder / filename

    if not pdf_path.exists():
        print(f"File not found: {filename}")
        continue

    print(f"\nProcessing: {filename}")

    result = converter.convert(str(pdf_path))

    # Extract structured Markdown
    markdown_text = (
        result.document.export_to_markdown()
    )

    output_path = (
        output_folder /
        f"{pdf_path.stem}.md"
    )

    output_path.write_text(
        markdown_text,
        encoding="utf-8"
    )

    print(f"Saved: {output_path}")

print("\nOCR processing completed!")