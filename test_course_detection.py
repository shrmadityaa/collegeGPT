from pathlib import Path
from src.parser.syllabus_parser import detect_courses

text = Path(
    "data/extracted_text/syllabus.txt"
).read_text(encoding="utf-8")

courses = detect_courses(text)

print(f"Detected courses: {len(courses)}")
print()

for course in courses[:3]:

    print("COURSE CODE:", course["course_code"])
    print("COURSE TITLE:", course["course_title"])

    print("\nCONTENT PREVIEW:\n")

    print(course["content"][:1000])

    print("\n" + "="*60 + "\n")