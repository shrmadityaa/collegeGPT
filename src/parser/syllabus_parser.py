import re
from src.parser.regex_patterns import SECTION_HEADINGS, SEMESTER_PATTERN, COURSE_TITLE_PATTERN

def detect_sections(text: str):
    sections = []
    for key, pattern in SECTION_HEADINGS.items():
        for match in pattern.finditer(text):
            sections.append({"section_name": key, "start": match.start()})
    sections.sort(key=lambda s: s["start"])
    return sections

def segment_by_sections(text):
    sections = detect_sections(text)
    segmented = []

    for i, sec in enumerate(sections):
        start = sec['start']
        end = sections[i+1]['start'] if i+1 < len(sections) else len(text)
        chunk = text[start:end].strip()
        segmented.append({
            "section": sec["section_name"],
            "content": chunk
        })
    return segmented

def detect_semester(text):
    match = SEMESTER_PATTERN.search(text)
    return match.group(1).capitalize() if match else None
def detect_courses(text):

    matches = list(COURSE_TITLE_PATTERN.finditer(text))

    courses = []

    for i, match in enumerate(matches):

        code = match.group(1).strip()
        title = match.group(2).strip()

        start = match.start()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        content = text[start:end].strip()

        courses.append({
            "course_code": code,
            "course_title": title.title(),
            "content": content
        })

    return courses