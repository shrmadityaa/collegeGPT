import re
from collections import defaultdict

from retrieval.semantic import semantic_search_with_scores
from retrieval.bm25_retriever import bm25_search, get_all_chunks
from guardrails import filter_relevant_docs
from utils.syllabus import (
    build_semester_course_catalog,
    clean_course_name,
    detect_query_semester,
    is_valid_course_code,
    resolve_course_metadata,
)


ALL_CHUNKS = get_all_chunks()
SEMESTER_COURSES, COURSE_LOOKUP = build_semester_course_catalog(ALL_CHUNKS)


def doc_key(doc):
    meta = resolve_course_metadata(doc, COURSE_LOOKUP)
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
    return detect_query_semester(query)


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

    docs = []
    course_docs = {}

    for doc in ALL_CHUNKS:
        meta = doc.metadata or {}
        if meta.get("type") != "course":
            continue

        course_code = str(meta.get("course_code") or "").upper()
        if not is_valid_course_code(course_code):
            continue

        resolved = COURSE_LOOKUP.get(course_code)
        if not resolved or resolved.get("semester") != semester:
            continue

        course_docs.setdefault(course_code, doc)

    for row in SEMESTER_COURSES.get(semester, []):
        course_code = row["course_code"]
        if course_code in course_docs:
            docs.append(course_docs[course_code])

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

    semantic_results = semantic_search_with_scores(query, k=8)
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
        meta = resolve_course_metadata(doc, COURSE_LOOKUP)
        content = doc.page_content

        if course_code_query and meta.get("course_code") == course_code_query:
            scores[key] += 8

        if semester_query:
            semester = str(meta.get("semester", "")).upper()
            if semester_query.upper() == semester:
                scores[key] += 6

        scores[key] += lexical_overlap(query, content) * 5

        course_name = clean_course_name(meta.get("course_name")).lower()
        if course_name and course_name in query.lower():
            scores[key] += 5

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    docs = [docs_by_key[key] for key, score in ranked[:k]]

    return filter_relevant_docs(query, docs, max_docs=k, course_lookup=COURSE_LOOKUP)
