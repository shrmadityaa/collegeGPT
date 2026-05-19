import re
from langchain_core.documents import Document

# FIX 1: Order matters in regex OR (|) clauses. Longest matches must come first!
# Added \b to prevent matching "I" inside "II"
SEMESTER_PATTERN = r"SEMESTER[- ]?(VIII|VII|VI|IV|V|III|II|I)\b"
COURSE_PATTERN = r"(U[A-Z]{2,5}\d{3})\s+([A-Z][A-Za-z &()-]+)"

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = text.replace("THE SUGC and SPGC meetings held on 27th February, 2026", "")
    return text.strip()

def split_documents(documents):
    chunks = []
    current_semester = None

    for doc in documents:
        text = clean_text(doc.page_content)
        
        # FIX 2: Find ALL semester mentions on the page and their exact locations
        semester_matches = list(re.finditer(SEMESTER_PATTERN, text, re.IGNORECASE))
        course_matches = list(re.finditer(COURSE_PATTERN, text))

        for i, match in enumerate(course_matches):
            start = match.start()
            end = course_matches[i + 1].start() if i + 1 < len(course_matches) else len(text)
            
            chunk_text = clean_text(text[start:end])
            if len(chunk_text) < 80:
                continue
            
            # FIX 3: Assign the semester that appears *immediately before* this specific course
            # This prevents a Semester 3 header at the top of the page from ruining Semester 4 courses below it
            valid_semesters_before_course = [sm for sm in semester_matches if sm.start() < start]
            if valid_semesters_before_course:
                # Extract just the roman numeral to make it perfectly uniform
                raw_sem = valid_semesters_before_course[-1].group(1).upper()
                current_semester = f"SEMESTER {raw_sem}"

            course_code = match.group(1)
            course_name = match.group(2).strip()

            metadata = {
                "semester": current_semester,
                "course_code": course_code,
                "course_name": course_name
            }

            chunks.append(Document(page_content=chunk_text, metadata=metadata))

    print(f"Created {len(chunks)} structured chunks")
    return chunks