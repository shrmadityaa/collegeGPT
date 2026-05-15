from src.extractor.text_extraction import run_extraction

output = run_extraction(
    "data/raw_pdfs/syllabus.pdf",
    "data/extracted_text/syllabus.txt"
)

print(f"Extraction completed: {output}")