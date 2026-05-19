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
    # Fix: Normalizes 1-8 to I-VIII so it matches the metadata perfectly
    match = re.search(r"semester[- ]?(i{1,3}|iv|v|vi{0,3}|viii|[1-8])", query, re.IGNORECASE)
    if match:
        raw = match.group(1).upper()
        roman_map = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII"}
        return roman_map.get(raw, raw)
    return None


def hybrid_search(query):
    semantic_docs = semantic_search(query, k=8)
    bm25_docs = bm25_search(query)

    docs = remove_duplicates(semantic_docs + bm25_docs)
    semester_query = detect_semester(query)

    filtered_docs = []
    for doc in docs:
        metadata = doc.metadata
        
        # Base score of 1 ensures good semantic documents are NEVER deleted
        score = 1 

        # SEMESTER MATCH BOOST
        if semester_query:
            semester = metadata.get("semester", "").upper()
            if semester_query in semester:
                score += 15

        # COURSE CODE BOOST
        if metadata.get("course_code"):
            score += 3

        filtered_docs.append((score, doc))

    filtered_docs.sort(key=lambda x: x[0], reverse=True)

    # Return top 4 documents safely
    final_docs = [doc for score, doc in filtered_docs]
    return final_docs[:4]