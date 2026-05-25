import re
import ollama

from guardrails import (
    FALLBACK_MESSAGE,
    validate_query_and_docs,
    normalize_text,
    clean_course_name,
)
from llm.prompts import SYSTEM_PROMPT
from retrieval.bm25_retriever import get_all_chunks
from utils.syllabus import (
    build_course_name_index,
    build_elective_catalog,
    build_semester_course_catalog,
    collect_ai_related_subjects,
    detect_query_intents,
    format_lab_practical_answer,
    format_focus_area_domain_summary,
    format_semester_label,
    is_ai_curriculum_query,
    is_focus_area_query,
    resolve_course_metadata,
)

MODEL_NAME = "phi3:mini"
ALL_CHUNKS = get_all_chunks()
SEMESTER_COURSES, COURSE_LOOKUP = build_semester_course_catalog(ALL_CHUNKS)
COURSE_NAME_INDEX = build_course_name_index(COURSE_LOOKUP)
ELECTIVE_CATALOG = build_elective_catalog(ALL_CHUNKS)


def _answer_ai_curriculum_query():
    core_subjects, elective_subjects = collect_ai_related_subjects(
        SEMESTER_COURSES,
        ELECTIVE_CATALOG,
    )

    if not core_subjects and not elective_subjects:
        return FALLBACK_MESSAGE

    lines = ["### AI-Related Subjects in the Curriculum", ""]

    if core_subjects:
        lines.append("**Core Curriculum**")
        for row in core_subjects:
            lines.append(
                f"- **{row['course_code']}** {clean_course_name(row['course_name'])} "
                f"({format_semester_label(row['semester'])})"
            )
        lines.append("")

    if elective_subjects:
        lines.append("**Related Professional Electives**")
        for row in elective_subjects:
            lines.append(
                f"- **{row['course_code']}** {clean_course_name(row['course_name'])} "
                f"(Elective {row['slot']})"
            )

    return "\n".join(lines).strip()


def _answer_focus_area_query():
    return format_focus_area_domain_summary(SEMESTER_COURSES, ELECTIVE_CATALOG)


def _restrict_to_exact_course_if_possible(query, docs):
    """If query names a course/code exactly, send only that course's chunks to the LLM."""
    q_norm = normalize_text(query)

    exact_codes = set()

    for doc in docs:
        meta = resolve_course_metadata(doc, COURSE_LOOKUP)

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
        meta = resolve_course_metadata(doc, COURSE_LOOKUP)

        course_name = clean_course_name(meta.get("course_name"))
        course_code = meta.get("course_code")
        semester = meta.get("semester")
        credits = meta.get("credits")
        ltp = meta.get("ltp")

        header = (
            f"Source {i}\n"
            f"Type: {(doc.metadata or {}).get('type')}\n"
            f"Page: {(doc.metadata or {}).get('page')}\n"
            f"Semester: {semester}\n"
            f"Course Code: {course_code}\n"
            f"Course Name: {course_name}\n"
            f"L-T-P: {ltp or 'Not mentioned'}\n"
            f"Credits: {credits or 'Not mentioned'}"
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
    if is_ai_curriculum_query(query):
        return _answer_ai_curriculum_query()

    if is_focus_area_query(query):
        return _answer_focus_area_query()

    docs = _restrict_to_exact_course_if_possible(query, docs)

    if "lab" in detect_query_intents(query):
        lab_answer = format_lab_practical_answer(
            query,
            docs,
            all_chunks=ALL_CHUNKS,
            course_lookup=COURSE_LOOKUP,
            course_name_index=COURSE_NAME_INDEX,
        )
        if lab_answer:
            return lab_answer
        return FALLBACK_MESSAGE

    is_valid, message = validate_query_and_docs(
        query,
        docs,
        course_lookup=COURSE_LOOKUP,
        course_name_index=COURSE_NAME_INDEX,
    )
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
3. Never generate inferred academic content outside the retrieved syllabus context.
4. If information is missing, output only:
{FALLBACK_MESSAGE}
5. Source 1 is the most relevant source.
6. If the question asks for a course syllabus, answer from the matching course source only.
7. Do not combine information from another course that only mentions similar words.
8. Do not write one long paragraph.
9. Keep the answer clean, structured, and readable.
10. Fix only obvious PDF extraction spelling issues.
11. Do not invent unit names, books, labs, credits, or outcomes.
12. For lab, practical, or experiment questions, if explicit matching content is absent, output only:
{FALLBACK_MESSAGE}

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
        "it can be inferred",
        "reasonable inference",
        "likely includes",
        "based on common college structures",
        "based on common syllabus structures",
        "common syllabus structures",
    ]

    if any(phrase in lower for phrase in unsafe_phrases):
        return FALLBACK_MESSAGE

    return answer
