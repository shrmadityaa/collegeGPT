import re

SECTION_HEADINGS = {
    "objectives": re.compile(r'\b(course\s+objectives|objectives)\b', re.I),
    "clo": re.compile(r'\b(course\s+learning\s+outcomes|clos?)\b', re.I),
    "labs": re.compile(r'\blabs?\b', re.I),
    "textbooks": re.compile(r'\btext\s*books?\b', re.I),
    "electives": re.compile(r'\belective\s+courses?\b', re.I)
}

SEMESTER_PATTERN = re.compile(r'(first|second|third|fourth|fifth|sixth|seventh|eighth)\s+semester', re.I)
COURSE_TITLE_PATTERN = re.compile(r'([A-Z]{2,3}\d{3})\s+(\b[A-Za-z].+)', re.I)
