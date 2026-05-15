from pathlib import Path

from src.parser.detailed_syllabus_parser import (
    detect_detailed_courses,
    split_course_sections
)

text = Path(
    "data/extracted_text/syllabus.txt"
).read_text(encoding="utf-8")

courses = detect_detailed_courses(text)

print(f"Detected detailed courses: {len(courses)}")
print()

first_course = courses[0]

print("COURSE:")
print(first_course["course_title"])
print()

sections = split_course_sections(first_course)

for sec in sections:

    print("SECTION:", sec["section"])
    print()

    print(sec["content"][:800])

    print("\n" + "="*60 + "\n")