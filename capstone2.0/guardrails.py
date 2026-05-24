import re
from typing import Iterable, List, Tuple

from langchain_core.documents import Document
from utils.syllabus import (
    clean_course_name,
    detect_query_intents,
    doc_mentions_course,
    is_elective_query,
    match_query_to_courses,
    normalize_course_text,
    resolve_course_metadata,
    section_match_score,
)

FALLBACK_MESSAGE = "This information is not explicitly present in the uploaded syllabus."

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
LAB_SECTION_TERMS = [
    "laboratory work",
    "lab experiment",
    "lab experiments",
    "laboratory experiment",
    "laboratory experiments",
    "practical work",
    "practical",
    "practicals",
    "experiment",
    "experiments",
]
LAB_QUERY_STOPWORDS = {
    "lab",
    "labs",
    "laboratory",
    "experiment",
    "experiments",
    "practical",
    "practicals",
    "work",
    "included",
    "include",
}


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9+.#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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

    if is_elective_query(query) and docs:
        return True

    important_terms = tokenize(query)

    if not important_terms:
        return False

    return any(term in ctx for term in important_terms)


def has_explicit_lab_grounding(
    query: str,
    docs: List[Document],
    course_lookup=None,
    course_name_index=None,
) -> bool:
    query_intents = detect_query_intents(query)
    if "lab" not in query_intents:
        return True

    lab_docs = [
        doc
        for doc in docs
        if any(term in normalize_course_text(doc.page_content) for term in LAB_SECTION_TERMS)
    ]
    if not lab_docs:
        return False

    course_matches = match_query_to_courses(query, course_lookup or {}, course_name_index)
    exact_course_matches = [course for course in course_matches if course["score"] >= 80]
    if exact_course_matches:
        return any(
            any(doc_mentions_course(doc, course_match) for course_match in exact_course_matches[:2])
            for doc in lab_docs
        )

    explicit_context = normalize_course_text(context_text(lab_docs))
    context_words = set(explicit_context.split())
    topical_tokens = {
        token
        for token in tokenize(query)
        if token not in LAB_QUERY_STOPWORDS
    }
    if not topical_tokens:
        return True

    return all(token in context_words for token in topical_tokens)

def filter_relevant_docs(
    query: str,
    docs: List[Document],
    max_docs: int = 8,
    course_lookup=None,
    course_name_index=None,
) -> List[Document]:
    if not docs:
        return []

    q_norm = normalize_text(query)
    q_course_norm = normalize_course_text(query)
    q_tokens = tokenize(query)
    query_intents = detect_query_intents(query)
    elective_query = is_elective_query(query)
    course_matches = match_query_to_courses(query, course_lookup or {}, course_name_index)
    exact_course_matches = [course for course in course_matches if course["score"] >= 80]
    exact_course_codes = {course["course_code"] for course in exact_course_matches[:2]}
    semester_match = re.search(
        r"\b(?:semester|sem)\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
        q_norm,
        re.IGNORECASE,
    )

    semester_query = None

    if semester_match:
        value = semester_match.group(1).upper()

        roman_map = {
            "1": "I",
            "2": "II",
            "3": "III",
            "4": "IV",
            "5": "V",
            "6": "VI",
            "7": "VII",
            "8": "VIII",
        }

        value = roman_map.get(value, value)

        semester_query = f"SEMESTER-{value}"

    course_code = re.search(COURSE_CODE_PATTERN, query, re.IGNORECASE)
    course_code = course_code.group(0).upper() if course_code else None

    scored = []
    for doc in docs:
        resolved = resolve_course_metadata(doc, course_lookup or {})

        if semester_query:
            doc_sem = str(resolved.get("semester") or "").upper()

            if doc_sem != semester_query:
                continue

        content_norm = normalize_text(doc.page_content)
        metadata = doc.metadata or {}
        score = 0.0
        section_type = str(metadata.get("section_type") or "").lower()

        meta_course_code = str(resolved.get("course_code") or metadata.get("course_code") or "").upper()
        course_name_raw = clean_course_name(resolved.get("course_name") or metadata.get("course_name"))
        course_name_norm = normalize_text(course_name_raw)
        course_page_match = any(doc_mentions_course(doc, match) for match in exact_course_matches[:2])

        if elective_query and metadata.get("type") == "course" and resolved.get("code_type") != "PEC":
            continue

        if "pcc" in query_intents and metadata.get("type") == "course" and resolved.get("code_type") != "PCC":
            continue

        if exact_course_codes:
            if meta_course_code in exact_course_codes:
                score += 120
            elif metadata.get("type") == "page" and course_page_match:
                score += 60
            else:
                continue

        # Strongest rule: if user asks an exact course name, keep that course above topic-only matches.
        if course_name_norm and normalize_course_text(course_name_raw) in q_course_norm:
            score += 100

        if course_code:
            if meta_course_code == course_code or course_code.lower() in content_norm:
                score += 100

        doc_tokens = tokenize(doc.page_content)
        if q_tokens:
            score += len(q_tokens.intersection(doc_tokens)) / len(q_tokens) * 5

        score += section_match_score(doc.page_content, query_intents)

        if section_type == "lab" and "lab" in query_intents:
            score += 12
        if section_type == "evaluation" and "evaluation" in query_intents:
            score += 12
        if section_type == "clo" and "clo" in query_intents:
            score += 10
        if section_type == "overview" and query_intents.intersection({"overview", "credits"}):
            score += 8
        if section_type == "syllabus" and "syllabus" in query_intents:
            score += 10

        # Penalize page chunks that merely mention words like "operating systems" in another course.
        if metadata.get("type") == "page" and not course_page_match and course_name_norm not in q_norm:
            score -= 1

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If there is an exact course/code match, discard unrelated courses/pages.
    if exact_course_codes:
        filtered = [
            doc for score, doc in scored
            if str((resolve_course_metadata(doc, course_lookup or {}).get("course_code") or "")).upper() in exact_course_codes
            or any(doc_mentions_course(doc, match) for match in exact_course_matches[:2])
        ]
        return filtered[:max_docs]

    return [doc for _, doc in scored[:max_docs]]


def validate_query_and_docs(
    query: str,
    docs: List[Document],
    course_lookup=None,
    course_name_index=None,
) -> Tuple[bool, str]:
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

    if not has_explicit_lab_grounding(
        query,
        docs,
        course_lookup=course_lookup,
        course_name_index=course_name_index,
    ):
        return False, FALLBACK_MESSAGE

    return True, ""
