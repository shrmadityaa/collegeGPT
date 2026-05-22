import re
from typing import Iterable, List, Tuple

from langchain_core.documents import Document

FALLBACK_MESSAGE = "This information is not available in the syllabus document."

BLOCKED_KEYWORDS = [
    "hostel", "hostels", "hostel fee", "hostel fees",
    "fee", "fees", "tuition", "scholarship", "scholarships",
    "admission", "admissions", "eligibility", "cutoff", "cut off",
    "placement", "placements", "package", "salary", "highest package",
    "faculty", "teacher", "professor", "contact", "phone", "email",
    "timetable", "time table", "exam date", "exam dates", "date sheet",
    "event", "events", "holiday", "holidays", "attendance",
    "canteen", "transport", "bus", "library timing", "college ranking",
]

ALLOWED_SYLLABUS_INTENT_WORDS = [
    "syllabus", "course", "courses", "subject", "subjects", "semester",
    "sem", "credit", "credits", "objective", "objectives", "outcome", "outcomes",
    "module", "modules", "unit", "units", "topic", "topics", "lab", "practical",
    "lecture", "tutorial", "l t p", "elective", "curriculum", "programme", "program",
    "b.e", "coe", "computer engineering", "code", "course code", "minor",
    "project", "internship", "prerequisite", "prerequisites",
]

COURSE_CODE_PATTERN = r"\bU[A-Z]{2,5}\d{3}\b|\bU[A-Z]{2,5}XXX\b"


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9+.#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_course_name(name: str) -> str:
    name = str(name or "")
    name = re.sub(r"^[\s:;\-]+", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def tokenize(text: str) -> set:
    stopwords = {
        "what", "which", "where", "when", "who", "why", "how", "does", "do", "is", "are",
        "the", "a", "an", "in", "on", "of", "for", "to", "from", "with", "and", "or",
        "me", "show", "give", "tell", "list", "explain", "details", "detail", "about",
        "there", "have", "has", "this", "that", "we", "our", "i", "want", "study",
        "syllabus", "course", "subject", "semester", "sem", "topics", "topic",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", str(text).lower())
    return {w for w in words if w not in stopwords and len(w) >= 2}


def is_blocked_query(query: str) -> Tuple[bool, str]:
    q = normalize_text(query)
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(normalize_text(keyword))}\b", q):
            return True, FALLBACK_MESSAGE
    return False, ""


def has_syllabus_intent(query: str) -> bool:
    q = normalize_text(query)
    if re.search(COURSE_CODE_PATTERN, query, re.IGNORECASE):
        return True
    return any(word in q for word in ALLOWED_SYLLABUS_INTENT_WORDS)


def context_text(docs: Iterable[Document]) -> str:
    return "\n".join(doc.page_content for doc in docs)


def query_context_overlap(query: str, docs: Iterable[Document]) -> float:
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    c_tokens = tokenize(context_text(docs))
    if not c_tokens:
        return 0.0

    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)


def exact_topic_present(query: str, docs: Iterable[Document]) -> bool:
    q = normalize_text(query)
    ctx = normalize_text(context_text(docs))

    # exact course code support
    course_code = re.search(COURSE_CODE_PATTERN, query, re.IGNORECASE)
    if course_code and course_code.group(0).lower() in ctx:
        return True

    # semester subject list queries should pass
    semester_patterns = [
        r"\bsemester\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
        r"\bsem\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
    ]

    subject_words = [
        "subject",
        "subjects",
        "course",
        "courses",
        "paper",
        "papers",
    ]

    has_semester = any(re.search(p, q, re.IGNORECASE) for p in semester_patterns)
    has_subject_word = any(word in q for word in subject_words)

    if has_semester and has_subject_word:
        return True

    important_terms = tokenize(query)

    if not important_terms:
        return False

    return any(term in ctx for term in important_terms)

def filter_relevant_docs(query: str, docs: List[Document], max_docs: int = 8) -> List[Document]:
    if not docs:
        return []

    q_norm = normalize_text(query)
    q_tokens = tokenize(query)
    course_code = re.search(COURSE_CODE_PATTERN, query, re.IGNORECASE)
    course_code = course_code.group(0).upper() if course_code else None

    scored = []
    for doc in docs:
        content_norm = normalize_text(doc.page_content)
        metadata = doc.metadata or {}
        score = 0.0

        meta_course_code = str(metadata.get("course_code") or "").upper()
        course_name_raw = clean_course_name(metadata.get("course_name"))
        course_name_norm = normalize_text(course_name_raw)

        # Strongest rule: if user asks an exact course name, keep that course above topic-only matches.
        if course_name_norm and course_name_norm in q_norm:
            score += 100

        if course_code:
            if meta_course_code == course_code or course_code.lower() in content_norm:
                score += 100

        doc_tokens = tokenize(doc.page_content)
        if q_tokens:
            score += len(q_tokens.intersection(doc_tokens)) / len(q_tokens) * 5

        # Penalize page chunks that merely mention words like "operating systems" in another course.
        if metadata.get("type") == "page" and course_name_norm not in q_norm:
            score -= 1

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If there is an exact course/code match, discard unrelated courses/pages.
    exact_course_codes = {
        str(doc.metadata.get("course_code") or "").upper()
        for score, doc in scored
        if score >= 90 and doc.metadata.get("course_code")
    }
    if exact_course_codes:
        filtered = [
            doc for score, doc in scored
            if str(doc.metadata.get("course_code") or "").upper() in exact_course_codes
        ]
        return filtered[:max_docs]

    return [doc for _, doc in scored[:max_docs]]


def validate_query_and_docs(query: str, docs: List[Document]) -> Tuple[bool, str]:
    blocked, message = is_blocked_query(query)
    if blocked:
        return False, message

    if not has_syllabus_intent(query):
        return False, FALLBACK_MESSAGE

    if not docs:
        return False, FALLBACK_MESSAGE

    if not exact_topic_present(query, docs):
        return False, FALLBACK_MESSAGE

    overlap = query_context_overlap(query, docs)
    if overlap < 0.10:
        return False, FALLBACK_MESSAGE

    return True, ""
