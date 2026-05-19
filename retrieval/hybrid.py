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


def normalize_query(query):
    """Converts Roman numeral semesters to numeric so retrievers handle them consistently."""
    roman_to_num = [
        ('VIII', '8'), ('VII', '7'), ('VI', '6'),
        ('IV', '4'),                              # ← must come before 'I' and 'V'
        ('V', '5'),
        ('III', '3'), ('II', '2'), ('I', '1'),
    ]
    result = query
    for roman, num in roman_to_num:
        result = re.sub(rf'(?<![A-Z]){roman}(?![A-Z])', num, result, flags=re.IGNORECASE)
    return result


def detect_semester(query):
    match = re.search(r"semester[- ]?(viii|vii|vi|iv|v|iii|ii|i|[1-8])", query, re.IGNORECASE)
    if match:
        raw = match.group(1).upper()
        roman_map = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII"}
        return roman_map.get(raw, raw)
    return None


def hybrid_search(query):
    semester_query = detect_semester(query)        # detect from original query
    normalized = normalize_query(query)            # normalize before retrieval

    semantic_docs = semantic_search(normalized, k=8)
    bm25_docs = bm25_search(normalized)

    docs = remove_duplicates(semantic_docs + bm25_docs)

    filtered_docs = []
    for doc in docs:
        metadata = doc.metadata
        score = 1

        if semester_query:
            semester = metadata.get("semester", "").upper()
            if semester_query == semester:          # exact match instead of `in`
                score += 15

        if metadata.get("course_code"):
            score += 3

        filtered_docs.append((score, doc))

    filtered_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in filtered_docs][:4]