import re
from collections import defaultdict


SEMESTER_ROMAN_MAP = {
    "1": "I",
    "2": "II",
    "3": "III",
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "i": "I",
    "ii": "II",
    "iii": "III",
    "iv": "IV",
    "v": "V",
    "vi": "VI",
    "vii": "VII",
    "viii": "VIII",
}

SEMESTER_QUERY_PATTERN = re.compile(
    r"\b(?:semester|sem)\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
    re.IGNORECASE,
)
SEMESTER_HEADER_PATTERN = re.compile(
    r"\bSEMESTER[-\s]*(VIII|VII|VI|V|IV|III|II|I|8|7|6|5|4|3|2|1)\b",
    re.IGNORECASE,
)
VALID_COURSE_CODE_PATTERN = re.compile(r"^U[A-Z]{2,5}\d{3}$")
COURSE_CODE_PATTERN = re.compile(r"\bU[A-Z]{2,5}(?:\d{3}|XXX)\b", re.IGNORECASE)
COURSE_ROW_PATTERN = re.compile(
    r"\b\d+\.?\s+"
    r"(U[A-Z]{2,5}(?:\d{3}|XXX))\s+"
    r"(.+?)\s+"
    r"(BSC|ESC|PCC|PEC|OEC|HSS|PRJ|OTH)\s+"
    r"([0-9*-]+)\s+([0-9*-]+)\s+([0-9*-]+)\s+([0-9.]+)",
    re.IGNORECASE,
)
CREDITS_PATTERN = re.compile(
    r"\bL\s*T\s*P\s*Cr\s*([0-9*-]+)\s+([0-9*-]+)\s+([0-9*-]+)\s+([0-9.]+)\b",
    re.IGNORECASE,
)


def normalize_semester_token(value):
    key = str(value or "").strip().lower()
    roman = SEMESTER_ROMAN_MAP.get(key)
    return f"SEMESTER-{roman}" if roman else None


def detect_query_semester(text):
    match = SEMESTER_QUERY_PATTERN.search(str(text or ""))
    if not match:
        return None
    return normalize_semester_token(match.group(1))


def detect_semester_header(text):
    match = SEMESTER_HEADER_PATTERN.search(str(text or ""))
    if not match:
        return None
    return normalize_semester_token(match.group(1))


def clean_course_name(name):
    name = str(name or "")
    name = re.sub(r"^[\s:;\-]+", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def is_valid_course_code(course_code):
    return bool(VALID_COURSE_CODE_PATTERN.fullmatch(str(course_code or "").upper()))


def normalize_overview_text(text):
    text = str(text or "")
    text = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)
    return re.sub(r"\s+", " ", text).strip()


def split_semester_sections(text):
    normalized = normalize_overview_text(text)
    matches = list(SEMESTER_HEADER_PATTERN.finditer(normalized))
    sections = []

    for index, match in enumerate(matches):
        semester = normalize_semester_token(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        sections.append((semester, normalized[start:end]))

    return sections


def extract_semester_courses(section_text):
    normalized = normalize_overview_text(section_text)
    total_match = re.search(r"\bTOTAL\b", normalized, re.IGNORECASE)
    if total_match:
        normalized = normalized[:total_match.start()]

    courses = []
    seen = set()

    for match in COURSE_ROW_PATTERN.finditer(normalized):
        course_code = match.group(1).upper()
        course_name = clean_course_name(match.group(2))
        if not is_valid_course_code(course_code) or not course_name:
            continue

        key = (course_code, course_name)
        if key in seen:
            continue
        seen.add(key)

        l_val, t_val, p_val, credits = (match.group(i).strip() for i in range(4, 8))
        courses.append(
            {
                "course_code": course_code,
                "course_name": course_name,
                "ltp": f"{l_val}-{t_val}-{p_val}",
                "credits": credits,
            }
        )

    return courses


def build_semester_course_catalog(docs):
    semester_courses = defaultdict(list)
    course_lookup = {}
    seen = set()

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        if metadata.get("type") != "page":
            continue

        for semester, section in split_semester_sections(getattr(doc, "page_content", "")):
            for course in extract_semester_courses(section):
                key = (semester, course["course_code"])
                if key in seen:
                    continue
                seen.add(key)

                entry = {**course, "semester": semester}
                semester_courses[semester].append(entry)
                course_lookup.setdefault(course["course_code"], entry)

    return dict(semester_courses), course_lookup


def extract_credit_details(text):
    match = CREDITS_PATTERN.search(str(text or ""))
    if not match:
        return None

    l_val, t_val, p_val, credits = (match.group(i).strip() for i in range(1, 5))
    return {
        "ltp": f"{l_val}-{t_val}-{p_val}",
        "credits": credits,
    }


def resolve_course_metadata(doc, course_lookup):
    metadata = getattr(doc, "metadata", {}) or {}
    course_code = str(metadata.get("course_code") or "").upper()
    resolved = course_lookup.get(course_code, {})

    course_name = clean_course_name(resolved.get("course_name") or metadata.get("course_name"))
    semester = resolved.get("semester") or metadata.get("semester")
    credit_details = extract_credit_details(getattr(doc, "page_content", "")) or {}

    return {
        "course_code": course_code or None,
        "course_name": course_name or None,
        "semester": semester,
        "ltp": credit_details.get("ltp") or resolved.get("ltp"),
        "credits": credit_details.get("credits") or resolved.get("credits"),
    }
