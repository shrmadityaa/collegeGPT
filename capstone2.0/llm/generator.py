import re
import ollama

from guardrails import (
    FALLBACK_MESSAGE,
    validate_query_and_docs,
    normalize_text,
    clean_course_name,
)
from llm.prompts import SYSTEM_PROMPT

MODEL_NAME = "phi3:mini"


def _restrict_to_exact_course_if_possible(query, docs):
    """If query names a course/code exactly, send only that course's chunks to the LLM."""
    q_norm = normalize_text(query)

    exact_codes = set()

    for doc in docs:
        meta = doc.metadata or {}

        raw_course_name = meta.get("course_name")
        course_name = normalize_text(clean_course_name(raw_course_name))
        course_code = str(meta.get("course_code") or "").upper()

        if course_name and course_name in q_norm and course_code:
            exact_codes.add(course_code)

    code_match = re.search(
        r"\bU[A-Z]{2,5}\d{3}\b|\bU[A-Z]{2,5}XXX\b",
        query,
        re.IGNORECASE,
    )

    if code_match:
        exact_codes.add(code_match.group(0).upper())

    if exact_codes:
        filtered = [
            doc
            for doc in docs
            if str((doc.metadata or {}).get("course_code") or "").upper() in exact_codes
        ]

        if filtered:
            return filtered

    return docs


def _format_context(docs):
    context_blocks = []

    for i, doc in enumerate(docs[:4], start=1):
        meta = doc.metadata or {}

        course_name = clean_course_name(meta.get("course_name"))
        course_code = meta.get("course_code")
        semester = meta.get("semester")

        header = (
            f"Source {i}\n"
            f"Type: {meta.get('type')}\n"
            f"Page: {meta.get('page')}\n"
            f"Semester: {semester}\n"
            f"Course Code: {course_code}\n"
            f"Course Name: {course_name}"
        )

        context_blocks.append(
            f"{header}\n\nCONTENT:\n{doc.page_content[:2500]}"
        )

    return "\n\n---\n\n".join(context_blocks)


def _clean_answer(answer):
    answer = answer.strip()

    # Remove accidental markdown headings if model overdoes it
    answer = re.sub(r"\n{3,}", "\n\n", answer)

    # Fix common PDF extraction noise seen in your output
    replacements = {
        "ach0mevaling": "achieving",
        "ach0meval": "achieve",
        "Pro tection": "Protection",
        "Computer -System": "Computer-System",
        "Operating-System": "Operating System",
        "filesystems": "file systems",
    }

    for wrong, right in replacements.items():
        answer = answer.replace(wrong, right)

    return answer


def generate_answer(query, docs):
    docs = _restrict_to_exact_course_if_possible(query, docs)

    is_valid, message = validate_query_and_docs(query, docs)
    if not is_valid:
        return message or FALLBACK_MESSAGE

    context = _format_context(docs)

    prompt = f"""
{SYSTEM_PROMPT}

You are a college syllabus assistant.

Use ONLY the syllabus context below.

Strict rules:
1. Do not use outside knowledge.
2. Do not guess or infer beyond the given context.
3. If information is missing, output only:
{FALLBACK_MESSAGE}
4. Source 1 is the most relevant source.
5. If the question asks for a course syllabus, answer from the matching course source only.
6. Do not combine information from another course that only mentions similar words.
7. Do not write one long paragraph.
8. Keep the answer clean, structured, and readable.
9. Fix only obvious PDF extraction spelling issues.
10. Do not invent unit names, books, labs, credits, or outcomes.

Required answer format:

Course:
- <course code and course name if available>

Credits:
- <L T P Cr if available>

Course Objective:
- <objective if available>

Syllabus Topics:
- <topic/module 1>: <brief details>
- <topic/module 2>: <brief details>
- <topic/module 3>: <brief details>

Lab / Practical Work:
- <mention only if available in context>

Books / References:
- <mention only if available in context>

If any section is not available in the context, write:
- Not mentioned in the syllabus context.

SYLLABUS CONTEXT:
{context}

QUESTION:
{query}

FINAL ANSWER:
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0,
            "top_p": 0.2,
            "repeat_penalty": 1.1,
        },
    )

    answer = _clean_answer(response["message"]["content"])

    lower = answer.lower()

    unsafe_phrases = [
        "based on my knowledge",
        "generally",
        "typically",
        "not in the context but",
        "outside the context",
        "as an ai",
        "i don't have access",
    ]

    if any(phrase in lower for phrase in unsafe_phrases):
        return FALLBACK_MESSAGE

    return answer