import re
from collections import defaultdict

from retrieval.semantic import semantic_search_with_scores
from retrieval.bm25_retriever import bm25_search, get_all_chunks
from guardrails import filter_relevant_docs
from utils.syllabus import (
    build_course_name_index,
    build_elective_catalog,
    build_semester_course_catalog,
    clean_course_name,
    collect_ai_related_subjects,
    detect_query_intents,
    detect_query_semester,
    doc_mentions_course,
    filter_electives_for_query,
    get_focus_area_page_docs,
    is_ai_curriculum_query,
    is_elective_query,
    is_focus_area_query,
    is_valid_course_code,
    match_query_to_courses,
    normalize_course_text,
    resolve_course_metadata,
    section_match_score,
)


ALL_CHUNKS = get_all_chunks()
SEMESTER_COURSES, COURSE_LOOKUP = build_semester_course_catalog(ALL_CHUNKS)
COURSE_NAME_INDEX = build_course_name_index(COURSE_LOOKUP)
ELECTIVE_CATALOG = build_elective_catalog(ALL_CHUNKS)


def doc_key(doc):
    meta = resolve_course_metadata(doc, COURSE_LOOKUP)
    return (
        meta.get("course_code"),
        meta.get("course_name"),
        meta.get("semester"),
        doc.page_content[:120],
    )


def add_candidate(scores, docs_by_key, doc, base_score=0.0):
    key = doc_key(doc)
    docs_by_key[key] = doc
    scores[key] += base_score


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


def is_elective_table_query(query):
    q_norm = normalize_course_text(query)
    if not is_elective_query(query):
        return False

    return any(
        phrase in q_norm
        for phrase in [
            "list",
            "summarize",
            "summary",
            "related",
            "subject",
            "slot",
        ]
    )


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


def elective_query_docs(query):
    entries = filter_electives_for_query(query, ELECTIVE_CATALOG)
    if not entries:
        return []

    wanted_codes = {entry["course_code"] for entry in entries}
    docs = []
    seen = set()

    for doc in ALL_CHUNKS:
        meta = doc.metadata or {}
        if meta.get("type") != "page":
            continue

        text_upper = str(doc.page_content or "").upper()
        if any(code in text_upper for code in wanted_codes):
            key = doc_key(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)

    return docs


def ai_curriculum_docs(query):
    core_subjects, elective_subjects = collect_ai_related_subjects(SEMESTER_COURSES, ELECTIVE_CATALOG)
    if not core_subjects and not elective_subjects:
        return []

    core_codes = {row["course_code"] for row in core_subjects}
    elective_codes = {row["course_code"] for row in elective_subjects}
    docs = []
    seen = set()

    for doc in ALL_CHUNKS:
        meta = doc.metadata or {}
        course_code = str(meta.get("course_code") or "").upper()

        if course_code in core_codes:
            key = doc_key(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)
            continue

        if meta.get("type") != "page":
            continue

        text_upper = str(doc.page_content or "").upper()
        if any(code in text_upper for code in elective_codes):
            key = doc_key(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)

    return docs


def focus_area_docs(query):
    docs = []
    seen = set()

    for doc in get_focus_area_page_docs(ALL_CHUNKS):
        key = doc_key(doc)
        if key not in seen:
            seen.add(key)
            docs.append(doc)

    return docs


def lexical_overlap(query, text):
    q_words = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    t_words = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))

    if not q_words:
        return 0

    return len(q_words.intersection(t_words)) / len(q_words)


def exact_course_candidate_docs(course_matches, query_intents):
    if not course_matches:
        return []

    target_matches = course_matches[:2]
    target_codes = {course["course_code"] for course in target_matches}
    docs = []
    seen = set()

    for doc in ALL_CHUNKS:
        meta = doc.metadata or {}
        resolved = resolve_course_metadata(doc, COURSE_LOOKUP)

        if resolved.get("course_code") in target_codes:
            key = doc_key(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)
            continue

        if meta.get("type") != "page":
            continue

        if not any(doc_mentions_course(doc, course_match) for course_match in target_matches):
            continue

        if section_match_score(doc.page_content, query_intents) > 0 or query_intents.intersection(
            {"credits", "syllabus", "overview", "clo"}
        ):
            key = doc_key(doc)
            if key not in seen:
                seen.add(key)
                docs.append(doc)

    return docs


def hybrid_search(query, k=8):
    if is_semester_subject_query(query):
        docs = semester_subject_docs(query)
        if docs:
            return docs[:k]

    if is_elective_table_query(query):
        docs = elective_query_docs(query)
        if docs:
            return docs[:k]

    if is_ai_curriculum_query(query):
        docs = ai_curriculum_docs(query)
        if docs:
            return docs[:k]

    if is_focus_area_query(query):
        docs = focus_area_docs(query)
        if docs:
            return docs[:k]

    query_intents = detect_query_intents(query)
    query_norm = normalize_course_text(query)
    semester_query = detect_semester(query)
    course_code_query = detect_course_code(query)
    course_matches = match_query_to_courses(query, COURSE_LOOKUP, COURSE_NAME_INDEX)
    exact_course_matches = [course for course in course_matches if course["score"] >= 80]
    exact_course_codes = {course["course_code"] for course in exact_course_matches[:2]}

    semantic_results = semantic_search_with_scores(query, k=8)
    bm25_results = bm25_search(query)

    scores = defaultdict(float)
    docs_by_key = {}

    for rank, (doc, distance) in enumerate(semantic_results, start=1):
        similarity_score = 1 / (1 + distance)
        add_candidate(scores, docs_by_key, doc, similarity_score * 3 + 1 / rank)

    for rank, doc in enumerate(bm25_results, start=1):
        add_candidate(scores, docs_by_key, doc, 2 / rank)

    for doc in exact_course_candidate_docs(exact_course_matches, query_intents):
        add_candidate(scores, docs_by_key, doc, 8)

    for key, doc in docs_by_key.items():
        meta = resolve_course_metadata(doc, COURSE_LOOKUP)
        metadata = doc.metadata or {}
        content = doc.page_content or ""
        content_norm = normalize_course_text(content)
        course_name = clean_course_name(meta.get("course_name")).lower()
        section_score = section_match_score(content, query_intents)
        section_type = str(metadata.get("section_type") or "").lower()

        if course_code_query:
            if meta.get("course_code") == course_code_query:
                scores[key] += 90
            elif metadata.get("type") == "page" and course_code_query.lower() in content.lower():
                scores[key] += 28

        if exact_course_codes:
            if meta.get("course_code") in exact_course_codes:
                scores[key] += 60
                if metadata.get("type") == "course" and metadata.get("part") == 1:
                    scores[key] += 10
            elif metadata.get("type") == "page" and any(
                doc_mentions_course(doc, match) for match in exact_course_matches[:2]
            ):
                scores[key] += 30
            elif meta.get("course_code") and not is_elective_table_query(query):
                scores[key] -= 25

        if semester_query:
            semester = str(meta.get("semester") or "").upper()
            if semester_query.upper() == semester:
                scores[key] += 10
            elif semester:
                scores[key] -= 8

        if course_name and normalize_course_text(course_name) in query_norm:
            scores[key] += 20

        if meta.get("code_type") == "PCC" and "pcc" in query_intents:
            scores[key] += 35

        if meta.get("code_type") == "PEC" and exact_course_codes and not is_elective_query(query):
            scores[key] -= 12

        scores[key] += lexical_overlap(query, content) * 5
        scores[key] += section_score

        if section_type == "lab" and "lab" in query_intents:
            scores[key] += 14
        if section_type == "evaluation" and "evaluation" in query_intents:
            scores[key] += 14
        if section_type == "clo" and "clo" in query_intents:
            scores[key] += 10
        if section_type == "overview" and query_intents.intersection({"overview", "credits"}):
            scores[key] += 8
        if section_type == "syllabus" and "syllabus" in query_intents:
            scores[key] += 10

        if metadata.get("type") == "course":
            scores[key] += 4
            if metadata.get("part") == 1 and query_intents.intersection(
                {"credits", "syllabus", "overview", "clo", "evaluation", "lab"}
            ):
                scores[key] += 8

        if metadata.get("type") == "page":
            if exact_course_matches and any(doc_mentions_course(doc, match) for match in exact_course_matches[:2]):
                scores[key] += 12
            elif exact_course_matches and section_score == 0:
                scores[key] -= 5

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    docs = [docs_by_key[key] for key, _ in ranked[:k]]

    return filter_relevant_docs(
        query,
        docs,
        max_docs=k,
        course_lookup=COURSE_LOOKUP,
        course_name_index=COURSE_NAME_INDEX,
    )
