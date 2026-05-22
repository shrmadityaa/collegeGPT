import re
import pickle
import streamlit as st

from retrieval.hybrid import hybrid_search
from llm.generator import generate_answer
from guardrails import FALLBACK_MESSAGE


st.set_page_config(
    page_title="CollegeGPT",
    page_icon="🎓",
    layout="wide"
)

st.title("CollegeGPT")
st.write("Ask questions only from the uploaded syllabus document.")


SEMESTER_MAP = {
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


def load_all_chunks():
    try:
        with open("extracted/chunks.pkl", "rb") as f:
            return pickle.load(f)
    except Exception:
        return []


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
    roman = SEMESTER_MAP.get(value)

    if not roman:
        return None

    return f"SEMESTER-{roman}"


def is_subject_list_query(query):
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


def clean_course_name(name):
    name = str(name or "")
    name = name.replace(":", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def extract_courses_from_text(text):
    """
    Extract course rows like:
    UCS303: OPERATING SYSTEMS L T P Cr 3 0 2 4.0
    """
    courses = []

    pattern = re.compile(
        r"\b(U[A-Z]{2,5}\d{3}|U[A-Z]{2,5}XXX)\s*[:\-]?\s*"
        r"([A-Z][A-Z0-9 &/().,\-]+?)\s+"
        r"(?:L\s*T\s*P\s*Cr|\d\s+\d\s+\d\s+\d)",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        code = match.group(1).upper()
        name = clean_course_name(match.group(2)).upper()

        if len(name) < 3:
            continue

        courses.append((code, name))

    return courses


def answer_semester_subjects(query):
    semester = detect_semester(query)

    if not semester:
        return FALLBACK_MESSAGE

    chunks = load_all_chunks()

    if not chunks:
        return FALLBACK_MESSAGE

    subjects = []
    seen = set()

    # First try metadata-based extraction
    for doc in chunks:
        meta = doc.metadata or {}

        if str(meta.get("semester")) != semester:
            continue

        course_code = meta.get("course_code")
        course_name = meta.get("course_name")

        if not course_code or not course_name:
            continue

        clean_name = clean_course_name(course_name)
        key = (course_code, clean_name)

        if key not in seen:
            seen.add(key)
            subjects.append(f"{course_code} - {clean_name}")

    # If metadata failed, fallback to text scan around semester pages
    if not subjects:
        semester_text = ""
        collecting = False

        next_semester_order = {
            "SEMESTER-I": "SEMESTER-II",
            "SEMESTER-II": "SEMESTER-III",
            "SEMESTER-III": "SEMESTER-IV",
            "SEMESTER-IV": "SEMESTER-V",
            "SEMESTER-V": "SEMESTER-VI",
            "SEMESTER-VI": "SEMESTER-VII",
            "SEMESTER-VII": "SEMESTER-VIII",
        }

        next_sem = next_semester_order.get(semester)

        for doc in chunks:
            text = doc.page_content or ""
            upper_text = text.upper()

            if semester in upper_text:
                collecting = True

            if collecting:
                semester_text += "\n" + text

            if collecting and next_sem and next_sem in upper_text:
                break

        extracted = extract_courses_from_text(semester_text)

        for code, name in extracted:
            key = (code, name)

            if key not in seen:
                seen.add(key)
                subjects.append(f"{code} - {name}")

    if not subjects:
        return FALLBACK_MESSAGE

    response = f"Subjects in {semester}:\n\n"

    for subject in subjects:
        response += f"- {subject}\n"

    return response.strip()


query = st.text_input("Ask a syllabus question")

if query:
    with st.spinner("Searching syllabus..."):

        if is_subject_list_query(query):
            answer = answer_semester_subjects(query)

            st.subheader("Answer")
            st.write(answer)
            st.stop()

        docs = hybrid_search(query)
        answer = generate_answer(query, docs)

    st.subheader("Answer")
    st.write(answer)

    with st.expander("Retrieved syllabus sources"):
        for doc in docs:
            st.json(doc.metadata)
            st.write(doc.page_content[:500])
            st.write("---")