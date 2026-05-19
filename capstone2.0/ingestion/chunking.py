import re

from langchain_core.documents import Document


SEMESTER_PATTERN = r"SEMESTER[- ]?(I|II|III|IV|V|VI|VII|VIII)"


COURSE_PATTERN = r"(U[A-Z]{2,5}\d{3})\s+([A-Z][A-Za-z &()-]+)"


def clean_text(text):

    text = re.sub(r"\s+", " ", text)

    text = text.replace(
        "THE SUGC and SPGC meetings held on 27th February, 2026",
        ""
    )

    return text.strip()


def split_documents(documents):

    chunks = []

    current_semester = None

    for doc in documents:

        text = clean_text(doc.page_content)

        semester_match = re.search(
            SEMESTER_PATTERN,
            text,
            re.IGNORECASE
        )

        if semester_match:
            current_semester = semester_match.group(0).upper()

        course_matches = list(
            re.finditer(COURSE_PATTERN, text)
        )

        for i, match in enumerate(course_matches):

            start = match.start()

            if i + 1 < len(course_matches):
                end = course_matches[i + 1].start()
            else:
                end = len(text)

            chunk_text = text[start:end]

            chunk_text = clean_text(chunk_text)

            if len(chunk_text) < 80:
                continue

            course_code = match.group(1)

            course_name = match.group(2).strip()

            metadata = {
                "semester": current_semester,
                "course_code": course_code,
                "course_name": course_name
            }

            chunks.append(
                Document(
                    page_content=chunk_text,
                    metadata=metadata
                )
            )

    print(f"Created {len(chunks)} structured chunks")

    return chunks