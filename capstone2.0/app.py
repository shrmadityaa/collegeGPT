import re

import streamlit as st

from retrieval.hybrid import hybrid_search

from llm.generator import generate_answer


st.set_page_config(page_title="CollegeGPT")

st.title("CollegeGPT")


def detect_semester_query(query):

    match = re.search(
        r"semester[- ]?(i|ii|iii|iv|v|vi|vii|viii|1|2|3|4|5|6|7|8)",
        query,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    return None


def format_subjects(docs, semester):

    subjects = []

    seen = set()

    for doc in docs:

        metadata = doc.metadata

        doc_semester = metadata.get(
            "semester",
            ""
        ).upper()

        if semester not in doc_semester:
            continue

        subject = metadata.get(
            "course_name",
            ""
        ).strip()

        if subject and subject not in seen:

            seen.add(subject)

            subjects.append(subject)

    return subjects


query = st.text_input("Ask a question")


if query:

    semester_query = detect_semester_query(query)

    docs = hybrid_search(query)

    # SPECIAL HANDLING FOR SEMESTER SUBJECTS
    if (
        semester_query
        and "subject" in query.lower()
    ):

        subjects = format_subjects(
            docs,
            semester_query
        )

        st.subheader(
            f"Subjects in Semester {semester_query}"
        )

        if subjects:

            for subject in subjects:
                st.write(f"• {subject}")

        else:
            st.warning(
                "No subjects found."
            )

    else:

        with st.spinner("Generating answer..."):

            answer = generate_answer(
                query,
                docs
            )

        st.subheader("Answer")

        st.write(answer)