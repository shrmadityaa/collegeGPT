import fitz
import re
from pathlib import Path

def extract_text_with_layout(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages_data = []
    for page_no, page in enumerate(doc, start=1):
        text_blocks = page.get_text("blocks")  # preserves layout roughly
        page_text = "\n".join(block[4] for block in sorted(text_blocks, key=lambda b: (b[1], b[0])))
        pages_data.append({"page": page_no, "text": page_text})
    return pages_data

def clean_text(text: str):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'–', '-', text)
    return text.strip()

def run_extraction(input_pdf, output_txt):
    pages = extract_text_with_layout(input_pdf)
    for p in pages:
        p["text"] = clean_text(p["text"])
    Path(output_txt).write_text("\n\n".join([p["text"] for p in pages]), encoding='utf-8')
    return output_txt
