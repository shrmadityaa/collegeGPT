import re
from langchain_core.documents import Document
from utils.syllabus import (
    build_semester_course_catalog,
    clean_course_name,
    detect_elective_slot,
    detect_semester_header,
)

HEADER_TEXT = "THE SUGC and SPGC meetings held on 27th February, 2026"
COURSE_CODE_PATTERN = r"\bU[A-Z]{2,5}\d{3}\b|\bU[A-Z]{2,5}XXX\b"


def clean_text(text: str) -> str:
    text = text.replace(HEADER_TEXT, " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_semester(text: str):
    return detect_semester_header(text)


def infer_section_type(text: str) -> str:
    text_lower = str(text or "").lower()

    if "evaluation scheme" in text_lower:
        return "evaluation"
    if any(
        phrase in text_lower
        for phrase in [
            "laboratory work",
            "lab experiment",
            "lab experiments",
            "laboratory experiment",
            "laboratory experiments",
            "practical work",
            "practicals",
            "experiment",
            "experiments",
        ]
    ):
        return "lab"
    if "course learning objectives" in text_lower or "course learning outcomes" in text_lower:
        return "clo"
    if "course objective" in text_lower or "course objectives" in text_lower:
        return "overview"
    if "syllabus" in text_lower:
        return "syllabus"

    return "general"


def infer_page_type(text: str) -> str:
    text_lower = str(text or "").lower()

    if "elective focus" in text_lower:
        return "focus_area"
    if "elective i" in text_lower or "elective ii" in text_lower or "elective iii" in text_lower or "elective iv" in text_lower:
        return "elective_table"
    if "generic elective" in text_lower:
        return "generic_elective_table"
    if "semester-" in text_lower and "course code" in text_lower:
        return "semester_overview"
    if "nature of the course code" in text_lower:
        return "course_type_summary"

    return "course_page"


def chunk_text(text, size=450, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunks.append(" ".join(words[start:end]))
        start += size - overlap
    return chunks


def extract_course_name(text_after_code: str):
    stop_words = [
        "BSC", "ESC", "PCC", "PEC", "OEC", "HSS", "PRJ", "OTH",
        "L T P", "CODE", "COURSE OBJECTIVE", "COURSE OUTCOMES", "SYLLABUS",
        "CONTACT HOURS", "CREDITS", "[PAGE", "[SEMESTER"
    ]
    name = text_after_code[:140]
    for stop in stop_words:
        idx = name.upper().find(stop)
        if idx != -1:
            name = name[:idx]
    name = re.sub(r"[:\-]+$", "", name).strip()
    return clean_course_name(name)


def split_documents(documents):
    chunks = []
    current_semester = None
    full_text_parts = []

    for page_no, doc in enumerate(documents, start=1):
        page_text = clean_text(doc.page_content)
        sem = detect_semester(page_text)
        if sem:
            current_semester = sem

        # Page chunks preserve tables, elective lists, credit structures, and semester summaries.
        if len(page_text) > 80:
            chunks.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "type": "page",
                        "page": page_no,
                        "semester": current_semester,
                        "course_code": None,
                        "course_name": None,
                        "table_type": infer_page_type(page_text),
                        "elective_slot": detect_elective_slot(page_text),
                    },
                )
            )

        full_text_parts.append(f"\n\n[PAGE {page_no}] [SEMESTER {current_semester}]\n{page_text}")

    _, course_lookup = build_semester_course_catalog(chunks)
    full_text = "\n".join(full_text_parts)
    course_matches = list(re.finditer(COURSE_CODE_PATTERN, full_text))

    for i, match in enumerate(course_matches):
        start = match.start()

        next_match_start = (
            course_matches[i + 1].start()
            if i + 1 < len(course_matches)
            else len(full_text)
        )

        # LIMIT COURSE BLOCK SIZE
        end = min(start + 3500, next_match_start)
        course_code = match.group(0)
        course_block = clean_text(full_text[start:end])
        if len(course_block) < 100:
            continue

        semester_match = re.search(r"\[SEMESTER (.*?)\]", course_block)
        semester = semester_match.group(1) if semester_match else None
        after_code = course_block[len(course_code):]
        course_name = extract_course_name(after_code)
        catalog_entry = course_lookup.get(course_code, {})

        for part_no, part in enumerate(chunk_text(course_block), start=1):
            chunks.append(
                Document(
                    page_content=part,
                    metadata={
                        "type": "course",
                        "semester": catalog_entry.get("semester") or semester,
                        "course_code": course_code,
                        "course_name": catalog_entry.get("course_name") or course_name,
                        "code_type": catalog_entry.get("code_type"),
                        "part": part_no,
                        "section_type": infer_section_type(part),
                    },
                )
            )

    print(f"Created {len(chunks)} chunks")
    return chunks
