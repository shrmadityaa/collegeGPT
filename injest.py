from src.extractor.text_extraction import run_extraction
from src.parser.table_parser import table_to_sentences
from src.parser.syllabus_parser import segment_by_sections, detect_semester
from src.chunker.chunker import semantic_chunk
import json
from pathlib import Path

def process_pdf(pdf_path):
    txt_path = Path("data/extracted_text") / (Path(pdf_path).stem + ".txt")
    run_extraction(pdf_path, txt_path)

    raw_text = Path(txt_path).read_text()
    semester = detect_semester(raw_text)
    table_sentences = table_to_sentences(raw_text)
    sectioned = segment_by_sections(raw_text)

    final_chunks = []
    for sec in sectioned:
        section = sec["section"]
        for course_info in table_sentences:
            chunks = semantic_chunk(
                sec["content"],
                course_name=course_info["course_name"],
                section=section,
                semester=semester
            )
            final_chunks.extend(chunks)

    output_json = Path("data/processed_chunks") / (Path(pdf_path).stem + ".json")
    json.dump(final_chunks, open(output_json, "w", encoding="utf-8"), indent=2)
    print(f"✅ Processed chunks stored at {output_json}")

if __name__ == "__main__":
    process_pdf("data/raw_pdfs/syllabus.pdf")
