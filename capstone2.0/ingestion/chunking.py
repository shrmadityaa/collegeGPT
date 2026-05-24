import re
from langchain_core.documents import Document
from utils.syllabus import clean_course_name, detect_semester_header

HEADER_TEXT = "THE SUGC and SPGC meetings held on 27th February, 2026"
COURSE_CODE_PATTERN = r"\bU[A-Z]{2,5}\d{3}\b|\bU[A-Z]{2,5}XXX\b"


def clean_text(text: str) -> str:
    text = text.replace(HEADER_TEXT, " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_semester(text: str):
    return detect_semester_header(text)


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
                    },
                )
            )

        full_text_parts.append(f"\n\n[PAGE {page_no}] [SEMESTER {current_semester}]\n{page_text}")

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

        for part_no, part in enumerate(chunk_text(course_block), start=1):
            chunks.append(
                Document(
                    page_content=part,
                    metadata={
                        "type": "course",
                        "semester": semester,
                        "course_code": course_code,
                        "course_name": course_name,
                        "part": part_no,
                    },
                )
            )

    print(f"Created {len(chunks)} chunks")
    return chunks
