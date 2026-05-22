import re
from collections import defaultdict

from retrieval.semantic import semantic_search_with_scores
from retrieval.bm25_retriever import bm25_search, get_all_chunks
from guardrails import filter_relevant_docs


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


def doc_key(doc):
    meta = doc.metadata or {}
    return (
        meta.get("course_code"),
        meta.get("course_name"),
        meta.get("semester"),
        doc.page_content[:120],
    )


def detect_course_code(query):
    match = re.search(
        r"\bU[A-Z]{2,5}\d{3}\b|\bU[A-Z]{2,5}XXX\b",
        query,
        re.IGNORECASE,
    )
    if match:
        return match.group(0).upper()
    return None


def detect_semester(query):
    q = query.lower()

    match = re.search(
        r"\b(?:semester|sem)\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
        q,
        re.IGNORECASE,
    )

    if not match:
        return None

    value = match.group(1).lower()
    roman = SEMESTER_ROMAN_MAP.get(value)

    if not roman:
        return None

    return f"SEMESTER-{roman}"


def is_semester_subject_query(query):
    q = query.lower()

    has_semester = detect_semester(query) is not None

    has_subject_word = any(
        word in q
        for word in [
            "subject",
            "subjects",
            "course",
            "courses",
            "paper",
            "papers",
            "list",
        ]
    )

    return has_semester and has_subject_word


def semester_subject_docs(query):
    semester = detect_semester(query)

    if not semester:
        return []

    all_chunks = get_all_chunks()

    docs = []
    seen = set()

    for doc in all_chunks:
        meta = doc.metadata or {}

        if meta.get("type") != "course":
            continue

        if str(meta.get("semester")) != semester:
            continue

        course_code = meta.get("course_code")
        course_name = meta.get("course_name")

        if not course_code or not course_name:
            continue

        key = (course_code, course_name)

        if key in seen:
            continue

        seen.add(key)
        docs.append(doc)

    return docs


def lexical_overlap(query, text):
    q_words = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    t_words = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))

    if not q_words:
        return 0

    return len(q_words.intersection(t_words)) / len(q_words)


def hybrid_search(query, k=8):
    # Direct handler for semester subject-list questions.
    # This prevents semantic search from missing table-style semester queries.
    if is_semester_subject_query(query):
        docs = semester_subject_docs(query)
        if docs:
            return docs[:k]

    semantic_results = semantic_search_with_scores(query, k=15)
    bm25_results = bm25_search(query)

    scores = defaultdict(float)
    docs_by_key = {}

    for rank, (doc, distance) in enumerate(semantic_results, start=1):
        key = doc_key(doc)
        docs_by_key[key] = doc

        similarity_score = 1 / (1 + distance)
        scores[key] += similarity_score * 3
        scores[key] += 1 / rank

    for rank, doc in enumerate(bm25_results, start=1):
        key = doc_key(doc)
        docs_by_key[key] = doc
        scores[key] += 2 / rank

    semester_query = detect_semester(query)
    course_code_query = detect_course_code(query)

    for key, doc in docs_by_key.items():
        meta = doc.metadata or {}
        content = doc.page_content

        if course_code_query and meta.get("course_code") == course_code_query:
            scores[key] += 8

        if semester_query:
            semester = str(meta.get("semester", "")).upper()
            if semester_query.upper() == semester:
                scores[key] += 6

        scores[key] += lexical_overlap(query, content) * 5

        course_name = str(meta.get("course_name") or "").lower()
        if course_name and course_name in query.lower():
            scores[key] += 5

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    docs = [docs_by_key[key] for key, score in ranked[:k]]

    return filter_relevant_docs(query, docs, max_docs=k)