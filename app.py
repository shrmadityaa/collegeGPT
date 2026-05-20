import re
import streamlit as st

from retrieval.hybrid import hybrid_search
from llm.generator import generate_answer

# ------------------ CONFIG ------------------ #
st.set_page_config(
    page_title="CollegeGPT",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------ STYLING ------------------ #
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ---- RESET & BASE ---- */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], .main {
    background-color: #080c14 !important;
    color: #e8eaf0;
    font-family: 'DM Mono', monospace;
}

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(ellipse 60% 40% at 20% 10%, rgba(56, 108, 255, 0.12) 0%, transparent 70%),
        radial-gradient(ellipse 40% 50% at 80% 85%, rgba(99, 50, 200, 0.10) 0%, transparent 70%);
}

[data-testid="stHeader"] { background: transparent !important; }

/* ---- SIDEBAR ---- */
[data-testid="stSidebar"] {
    background: #0d1120 !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ---- MAIN CONTENT WRAPPER ---- */
.block-container {
    max-width: 1100px !important;
    padding: 2.5rem 2rem !important;
}

/* ---- HEADER ---- */
.cgpt-header {
    display: flex;
    align-items: flex-end;
    gap: 18px;
    margin-bottom: 6px;
}

.cgpt-logo {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #5b8aff 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}

.cgpt-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #5b8aff;
    background: rgba(91, 138, 255, 0.10);
    border: 1px solid rgba(91, 138, 255, 0.25);
    border-radius: 4px;
    padding: 3px 10px;
    margin-bottom: 10px;
}

.cgpt-tagline {
    font-size: 0.82rem;
    color: rgba(232, 234, 240, 0.40);
    letter-spacing: 0.04em;
    margin-bottom: 2rem;
}

/* ---- DIVIDER ---- */
.cgpt-divider {
    height: 1px;
    background: linear-gradient(90deg, rgba(91,138,255,0.4) 0%, rgba(167,139,250,0.2) 50%, transparent 100%);
    margin-bottom: 2rem;
}

/* ---- CARDS ---- */
.card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 24px 26px;
    margin-bottom: 16px;
    backdrop-filter: blur(6px);
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(232,234,240,0.45);
    margin-bottom: 16px;
}

/* ---- INSTRUCTION PILLS ---- */
.pill-row {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.pill {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.8rem;
    color: rgba(232,234,240,0.65);
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 9px 14px;
    transition: border-color 0.2s;
}

.pill-icon {
    font-size: 1rem;
    flex-shrink: 0;
}

/* ---- QUICK EXAMPLES ---- */
.example-chip {
    display: inline-block;
    font-size: 0.73rem;
    color: #5b8aff;
    background: rgba(91,138,255,0.08);
    border: 1px solid rgba(91,138,255,0.18);
    border-radius: 20px;
    padding: 5px 12px;
    margin: 4px 4px 0 0;
    cursor: default;
}

/* ---- INPUT ---- */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(91,138,255,0.5) !important;
    box-shadow: 0 0 0 3px rgba(91,138,255,0.08) !important;
    outline: none !important;
}

.stTextInput > div > div > input::placeholder { color: rgba(232,234,240,0.28) !important; }

/* ---- ANSWER BLOCK ---- */
.answer-block {
    background: rgba(91,138,255,0.05);
    border: 1px solid rgba(91,138,255,0.15);
    border-radius: 12px;
    padding: 20px 22px;
    margin-top: 14px;
    font-size: 0.87rem;
    line-height: 1.75;
    color: #c9cfe8;
}

.answer-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #5b8aff;
    margin-bottom: 10px;
}

/* ---- SUBJECT LIST ---- */
.subject-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 12px;
    margin-top: 14px;
}

.subject-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: rgba(167,139,250,0.05);
    border: 1px solid rgba(167,139,250,0.12);
    border-radius: 8px;
    margin-bottom: 7px;
    font-size: 0.84rem;
    color: #d0d4f0;
}

.subject-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #a78bfa;
    flex-shrink: 0;
}

.subject-num {
    font-size: 0.65rem;
    color: rgba(167,139,250,0.5);
    margin-left: auto;
    font-variant-numeric: tabular-nums;
}

/* ---- WARNING / EMPTY STATE ---- */
.empty-state {
    text-align: center;
    padding: 30px 0 20px;
    color: rgba(232,234,240,0.30);
    font-size: 0.82rem;
}

.empty-icon { font-size: 2rem; margin-bottom: 8px; }

/* ---- SPINNER ---- */
.stSpinner > div {
    border-top-color: #5b8aff !important;
}

/* ---- STREAMLIT OVERRIDES ---- */
[data-testid="stMarkdownContainer"] p { color: #c9cfe8; }
.stAlert { border-radius: 10px !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ------------------ HELPERS ------------------ #
ROMAN_MAP = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}

def detect_semester_query(query):
    match = re.search(
        r"semester[- ]?(ix|viii|vii|vi|iv|v|iii|ii|i|[1-9])",
        query,
        re.IGNORECASE
    )
    if not match:
        return None
    raw = match.group(1).upper()
    # Normalise to roman numeral string
    if raw.isdigit():
        reverse = {v: k for k, v in ROMAN_MAP.items()}
        return reverse.get(int(raw), raw)
    return raw


def format_subjects(docs, semester):
    subjects = []
    seen = set()
    for doc in docs:
        metadata = doc.metadata
        doc_semester = metadata.get("semester", "").upper()
        if semester not in doc_semester:
            continue
        subject = metadata.get("course_name", "").strip()
        if subject and subject not in seen:
            seen.add(subject)
            subjects.append(subject)
    return subjects


# ------------------ HEADER ------------------ #
st.markdown("""
<div class="cgpt-header">
    <div class="cgpt-logo">CollegeGPT</div>
    <div class="cgpt-badge">Beta</div>
</div>
<div class="cgpt-tagline">AI-powered syllabus assistant for your college curriculum</div>
<div class="cgpt-divider"></div>
""", unsafe_allow_html=True)


# ------------------ LAYOUT ------------------ #
col1, col2 = st.columns([1, 2.2], gap="large")

# ===== LEFT PANEL =====
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">How to use</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="pill-row">
        <div class="pill"><span class="pill-icon">📅</span>Ask for semester-wise subjects</div>
        <div class="pill"><span class="pill-icon">📖</span>Explore any topic in the syllabus</div>
        <div class="pill"><span class="pill-icon">🔍</span>Compare subjects across semesters</div>
        <div class="pill"><span class="pill-icon">💡</span>Ask concept or unit-level questions</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Try asking</div>', unsafe_allow_html=True)
    st.markdown("""
    <div>
        <span class="example-chip">Subjects in semester 3</span>
        <span class="example-chip">What is DBMS?</span>
        <span class="example-chip">OS syllabus sem 4</span>
        <span class="example-chip">Explain CN unit 2</span>
        <span class="example-chip">Semester 6 subjects</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===== RIGHT PANEL =====
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Ask anything</div>', unsafe_allow_html=True)

    query = st.text_input(
        label="question",
        placeholder="e.g. What are the subjects in semester 5?",
        label_visibility="collapsed"
    )
    VALID_SEMESTERS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}
    if query:
        semester_query = detect_semester_query(query)

        if semester_query and semester_query not in VALID_SEMESTERS:
            raw_match = re.search(r"semester[- ]?(ix|viii|vii|vi|iv|v|iii|ii|i|[1-9])", query, re.IGNORECASE)
            raw_display = raw_match.group(1) if raw_match else semester_query
            st.markdown(
                f'<div class="answer-block">The syllabus does not contain information about courses offered specifically in Semester {raw_display}.</div>',
            unsafe_allow_html=True
            )
        else:
            with st.spinner("Searching knowledge base…"):
                docs = hybrid_search(query)

            # ---------- SEMESTER SUBJECTS ----------
            if semester_query and "subject" in query.lower():
                subjects = format_subjects(docs, semester_query)
                num = ROMAN_MAP.get(semester_query, semester_query)

                st.markdown(
                    f'<div class="subject-label">📘 Semester {num} — {len(subjects)} subject{"s" if len(subjects) != 1 else ""}</div>',
                    unsafe_allow_html=True
                )

                if subjects:
                    for i, subject in enumerate(subjects, 1):
                        st.markdown(f"""
                        <div class="subject-item">
                            <div class="subject-dot"></div>
                            <span>{subject}</span>
                            <span class="subject-num">{i:02d}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="empty-state">
                        <div class="empty-icon">🔎</div>
                        No subjects found for this semester.
                    </div>
                    """, unsafe_allow_html=True)

        # ---------- NORMAL QA ----------
            else:
                with st.spinner("Generating answer…"):
                    answer = generate_answer(query, docs)

                st.markdown('<div class="answer-label">🧠 Answer</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-block">{answer}</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty-state" style="padding:40px 0 30px;">
            <div class="empty-icon">🎓</div>
            Type a question above to get started
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)