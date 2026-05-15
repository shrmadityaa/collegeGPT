import re

COURSE_BLOCK_PATTERN = re.compile(
    r'([A-Z]{2,3}\d{3})\s+([A-Z][A-Z\s&\-\(\)]+?)\s+L\s+T\s+P\s+Cr',
    re.MULTILINE
)

SECTION_SPLIT_PATTERNS = [
    "Course Objectives:",
    "Course learning outcomes",
    "Text Books:",
    "Reference Books:"
]


def detect_detailed_courses(text):

    matches = list(COURSE_BLOCK_PATTERN.finditer(text))

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


def split_course_sections(course):

    content = course["content"]

    chunks = []

    current_section = "general"

    current_text = ""

    lines = content.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        matched = False

        for section in SECTION_SPLIT_PATTERNS:

            if section.lower() in line.lower():

                if current_text:

                    chunks.append({
                        "course_code": course["course_code"],
                        "course_title": course["course_title"],
                        "section": current_section,
                        "content": current_text.strip()
                    })

                current_section = section

                current_text = line + "\n"

                matched = True

                break

        if not matched:
            current_text += line + "\n"

    if current_text:

        chunks.append({
            "course_code": course["course_code"],
            "course_title": course["course_title"],
            "section": current_section,
            "content": current_text.strip()
        })

    return chunks