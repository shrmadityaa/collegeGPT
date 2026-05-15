import re

COURSE_ROW_PATTERN = re.compile(
    r'([A-Z]{2,3}\d{3})\s+([A-Za-z &]+)\s+(\d)\s+(\d)\s+(\d)\s+([\d.]+)'
)

def table_to_sentences(text: str):
    lines = text.splitlines()
    sentences = []

    for line in lines:
        match = COURSE_ROW_PATTERN.search(line)
        if match:
            code, name, lec, tut, prac, credits = match.groups()
            sentence = (
                f"The course {name.strip().title()} ({code.strip()}) "
                f"has {lec} lecture hours, {tut} tutorial hours, "
                f"{prac} practical hours, and carries {credits} credits."
            )
            sentences.append({
                "course_code": code.strip(),
                "course_name": name.strip().title(),
                "text": sentence
            })
    return sentences
