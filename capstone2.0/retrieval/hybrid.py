import re

from retrieval.semantic import semantic_search
from retrieval.bm25_retriever import bm25_search


def remove_duplicates(documents):

    unique_docs = []

    seen = set()

    for doc in documents:

        content = doc.page_content.strip()

        if content not in seen:

            seen.add(content)

            unique_docs.append(doc)

    return unique_docs


def detect_semester(query):

    match = re.search(
        r"semester[- ]?(i|ii|iii|iv|v|vi|vii|viii|1|2|3|4|5|6|7|8)",
        query,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    return None


def hybrid_search(query):

    semantic_docs = semantic_search(query, k=8)

    bm25_docs = bm25_search(query)

    docs = remove_duplicates(
        semantic_docs + bm25_docs
    )

    semester_query = detect_semester(query)

    filtered_docs = []

    for doc in docs:

        metadata = doc.metadata

        score = 0

        # SEMESTER MATCH BOOST
        if semester_query:

            semester = metadata.get(
                "semester",
                ""
            ).upper()

            if semester_query in semester:
                score += 15

        # EXACT QUERY MATCH
        if query.lower() in doc.page_content.lower():
            score += 10

        # COURSE CODE BOOST
        if metadata.get("course_code"):
            score += 3

        filtered_docs.append((score, doc))

    filtered_docs.sort(
        key=lambda x: x[0],
        reverse=True
    )

    final_docs = [
        doc for score, doc in filtered_docs
        if score > 0
    ]

    return final_docs[:4]