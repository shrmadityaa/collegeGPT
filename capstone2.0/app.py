import re
import pickle
import html
import streamlit as st
from datetime import datetime

# --- Import your local modules ---
from retrieval.hybrid import hybrid_search
from llm.generator import generate_answer
from guardrails import FALLBACK_MESSAGE
from utils.syllabus import (
    build_course_name_index,
    build_elective_catalog,
    build_semester_course_catalog,
    clean_course_name,
    collect_ai_related_subjects,
    detect_elective_slot,
    detect_elective_topic,
    detect_query_semester,
    filter_electives_for_query,
    filter_valid_subject_rows,
    format_focus_area_domain_summary,
    format_semester_label,
    is_ai_curriculum_query,
    is_credit_query,
    is_elective_query,
    is_focus_area_query,
    is_pcc_listing_row,
    is_pcc_list_query,
    is_valid_course_code,
    is_valid_semester_subject_row,
    match_query_to_courses,
    normalize_course_text,
)


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="CollegeGPT Syllabus Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# THEME CSS & SIDEBAR FIXES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

html, body, p, h1, h2, h3, h4, h5, h6, div, span, input, button, textarea { 
    font-family: 'Inter', sans-serif; 
}
[data-testid="stIconMaterial"], .stIcon {
    font-family: 'Material Symbols Rounded' !important;
}
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
    vertical-align: middle;
}

:root {
    --bg-background: #f7f8fa;
    --bg-surface: #ffffff;
    --bg-surface-low: #f1f3f5;
    --bg-surface-variant: #e9ecef;
    --border-outline: #d9dee5;
    --text-on-background: #20242a;
    --text-on-surface: #101418;
    --text-on-surface-variant: #667085;
    --color-primary: #146c5f;
    --color-primary-soft: #e4f4f1;
}

.stApp { background: var(--bg-background) !important; color: var(--text-on-background) !important; }

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] {
    visibility: visible !important;
    right: 0.75rem !important;
}
[data-testid="stToolbar"] [data-testid="stDeployButton"],
[data-testid="stToolbar"] [data-testid="stStatusWidget"],
[data-testid="stToolbar"] button[kind="header"] {
    display: none !important;
}

.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }

[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    color: var(--color-primary) !important;
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 50% !important;
    top: 0.7rem !important;
    left: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: none !important;
    z-index: 9999 !important;
}
[data-testid="collapsedControl"]::before {
    content: "keyboard_double_arrow_right";
    font-family: "Material Symbols Outlined";
    font-size: 20px;
    line-height: 1;
}
[data-testid="collapsedControl"]:hover {
    background-color: var(--color-primary-soft) !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] *,
[data-testid="stSidebarCollapseButton"] button {
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"] button {
    color: var(--color-primary) !important;
    background: var(--bg-surface) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarCollapseButton"] button::before {
    content: "keyboard_double_arrow_left";
    font-family: "Material Symbols Outlined";
    font-size: 20px;
    line-height: 1;
}

section[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border-outline) !important;
}
section[data-testid="stSidebar"] .block-container { padding: 22px 16px !important; }

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 8px !important;
    color: var(--text-on-background) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 11px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: var(--color-primary-soft) !important;
    border-color: var(--color-primary) !important;
    color: var(--color-primary) !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {
    margin: 0 !important; 
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 22px; }
.stat-card {
    background: var(--bg-surface-low); border: 1px solid transparent;
    border-radius: 8px; padding: 10px; display: flex; flex-direction: column;
}
.stat-lbl { font-size: 11px; color: var(--text-on-surface-variant); font-weight: 500; }
.stat-val { font-size: 15px; font-weight: 600; color: var(--text-on-surface); margin-top: 4px;}
.stat-val.primary { color: var(--color-primary); }

.slbl { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-on-surface-variant); margin-bottom: 10px; }
.feat { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-on-background); margin-bottom: 10px; }
.feat .icon { color: var(--color-primary); font-size: 16px; font-weight: bold;}
.history-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.history-item {
    border: 1px solid var(--border-outline);
    border-radius: 8px;
    padding: 8px 10px;
    color: var(--text-on-background);
    font-size: 12px;
    line-height: 1.35;
    background: var(--bg-surface);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.top-header {
    display: none; justify-content: space-between; padding: 0 32px; height: 56px; 
    border-bottom: 1px solid var(--border-outline); background: rgba(247, 248, 250, 0.94); 
    width: 100%; align-items: center; position: sticky; top: 0; z-index: 99;
    backdrop-filter: blur(10px);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left .icon { color: var(--color-primary); font-size: 19px; }
.header-left h2 { font-size: 14px; margin: 0; color: var(--text-on-surface); font-weight: 600; }
.header-left p { font-size: 12px; margin: 0; color: var(--text-on-surface-variant); }

.hero-container {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 22px 24px 20px; text-align: center; margin-top: 0;
}
.hero-icon-box {
    width: 44px; height: 44px; border-radius: 8px; background: var(--color-primary-soft); 
    border: 1px solid var(--border-outline); display: flex; align-items: center; 
    justify-content: center; margin-bottom: 18px;
}
.hero-icon-box .icon { font-size: 24px; color: var(--color-primary); }
.hero-title { font-size: 28px; font-weight: 700; color: var(--text-on-surface); margin-bottom: 8px; letter-spacing: 0; }
.hero-sub { font-size: 14px; color: var(--text-on-surface-variant); margin-bottom: 26px; }

div[data-testid="stMainBlockContainer"] div.stButton > button {
    background: transparent !important; border: 1px solid var(--border-outline) !important;
    border-radius: 8px !important; color: var(--text-on-background) !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 8px 12px !important; transition: all 0.2s ease !important; margin-bottom: 10px !important;
    box-shadow: none !important;
}
div[data-testid="stMainBlockContainer"] div.stButton > button:hover { 
    background: var(--bg-surface) !important; border-color: var(--color-primary) !important; color: var(--color-primary) !important; 
}
.sem-pills-row div.stButton > button { padding: 7px 8px !important; border-radius: 8px !important; }

div[data-testid="stExpander"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 8px !important;
    margin-top: 1rem !important;
    box-shadow: none !important;
}

div[data-testid="stChatMessage"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    padding: 4px 8px !important;
}
div[data-testid="stChatMessage"] * {
    color: var(--text-on-surface) !important;
}

div[data-testid="stBottom"] > div {
    background: var(--bg-background) !important;
}
div[data-testid="stChatInput"] { background: var(--bg-surface) !important; border: 1px solid var(--border-outline) !important; border-radius: 8px !important; box-shadow: none !important; }
div[data-testid="stChatInput"] div { background: var(--bg-surface) !important; color: var(--text-on-surface) !important; }
div[data-testid="stChatInput"] textarea { color: var(--text-on-surface) !important; caret-color: var(--text-on-surface) !important; }
div[data-testid="stChatInput"] textarea::placeholder { color: var(--text-on-surface-variant) !important; opacity: 1 !important; }
div[data-testid="stChatInput"] button { color: var(--color-primary) !important; }

.main-wrapper { padding: 16px 32px; max-width: 860px; margin: 0 auto; padding-bottom: 120px; }

@media (max-width: 760px) {
    .top-header { padding: 0 18px; }
    .main-wrapper { padding: 12px 18px 110px; }
    .hero-title { font-size: 24px; }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# BACKEND LOGIC & CONSTANTS
# =========================================================
@st.cache_data(show_spinner=False)
def load_all_chunks():
    try:
        with open("extracted/chunks.pkl", "rb") as f:
            return pickle.load(f)
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def load_catalog_data():
    chunks = load_all_chunks()
    semester_courses, course_lookup = build_semester_course_catalog(chunks)
    course_name_index = build_course_name_index(course_lookup)
    elective_catalog = build_elective_catalog(chunks)
    return semester_courses, course_lookup, course_name_index, elective_catalog

def detect_semester(query):
    return detect_query_semester(query)

def is_subject_list_query(query):
    q = query.lower()
    has_semester = detect_semester(query) is not None
    has_subject_word = any(word in q for word in ["subject", "subjects", "course", "courses", "paper", "papers", "list"])
    return has_semester and has_subject_word

def extract_courses_from_text(text):
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
        if len(name) < 3: continue
        courses.append((code, name))
    return courses


def is_elective_listing_query(query):
    q_norm = normalize_course_text(query)
    return is_elective_query(query) and any(
        phrase in q_norm for phrase in ["list", "subject", "subjects", "summarize", "summary", "related"]
    )


def answer_course_credit_query(query):
    _, course_lookup, course_name_index, _ = load_catalog_data()

    semester = detect_semester(query)
    matches = [
        match
        for match in match_query_to_courses(query, course_lookup, course_name_index)
        if match["score"] >= 80
    ]

    if semester:
        matches = [match for match in matches if match.get("semester") == semester]

    if not matches:
        return FALLBACK_MESSAGE

    course = matches[0]
    if not course.get("credits"):
        return FALLBACK_MESSAGE

    semester_label = format_semester_label(course.get("semester"))
    return (
        f"### Credit Structure for {course['course_name']}\n\n"
        f"- **Course Code:** {course['course_code']}\n"
        f"- **Semester:** {semester_label}\n"
        f"- **L-T-P:** {course.get('ltp') or 'Not mentioned'}\n"
        f"- **Credits:** {course.get('credits') or 'Not mentioned'}"
    )


def answer_elective_query(query):
    _, _, _, elective_catalog = load_catalog_data()
    entries = filter_electives_for_query(query, elective_catalog)
    if not entries:
        return FALLBACK_MESSAGE

    slot = detect_elective_slot(query)
    topic = detect_elective_topic(query)
    slot_order = {"I": 1, "II": 2, "III": 3, "IV": 4}
    entries = sorted(entries, key=lambda item: (slot_order.get(item["slot"], 99), item["course_code"]))

    if slot:
        heading = f"### Elective {slot} Subjects"
    elif topic == "ai":
        heading = "### AI-Related Electives"
    elif topic == "cyber_security":
        heading = "### Cyber Security Electives"
    else:
        heading = "### Professional Electives"

    lines = [heading, ""]
    for entry in entries:
        suffix = "" if slot else f" (Elective {entry['slot']})"
        lines.append(f"- **{entry['course_code']}** {entry['course_name']}{suffix}")

    return "\n".join(lines)


def answer_pcc_subjects(query):
    semester_courses, _, _, _ = load_catalog_data()
    semester = detect_semester(query)
    semester_order = [
        "SEMESTER-I",
        "SEMESTER-II",
        "SEMESTER-III",
        "SEMESTER-IV",
        "SEMESTER-V",
        "SEMESTER-VI",
        "SEMESTER-VII",
        "SEMESTER-VIII",
    ]

    target_semesters = [semester] if semester else semester_order
    lines = ["### PCC Subjects Semester-wise", ""]

    for sem in target_semesters:
        pcc_rows = [
            row for row in semester_courses.get(sem, [])
            if is_pcc_listing_row(sem, row)
        ]
        if not pcc_rows:
            continue

        lines.append(f"**{format_semester_label(sem)}**")
        for row in pcc_rows:
            lines.append(f"- **{row['course_code']}** {clean_course_name(row['course_name'])}")
        lines.append("")

    response = "\n".join(line for line in lines if line is not None).strip()
    return response if response != "### PCC Subjects Semester-wise" else FALLBACK_MESSAGE


def answer_ai_curriculum_subjects(query):
    semester_courses, _, _, elective_catalog = load_catalog_data()
    core_subjects, elective_subjects = collect_ai_related_subjects(semester_courses, elective_catalog)

    if not core_subjects and not elective_subjects:
        return FALLBACK_MESSAGE

    lines = ["### AI-Related Subjects in the Curriculum", ""]

    if core_subjects:
        lines.append("**Core Curriculum**")
        for row in core_subjects:
            lines.append(
                f"- **{row['course_code']}** {clean_course_name(row['course_name'])} ({format_semester_label(row['semester'])})"
            )
        lines.append("")

    if elective_subjects:
        lines.append("**Related Professional Electives**")
        for row in elective_subjects:
            lines.append(
                f"- **{row['course_code']}** {clean_course_name(row['course_name'])} (Elective {row['slot']})"
            )

    return "\n".join(lines).strip()


def answer_focus_areas(query):
    semester_courses, _, _, elective_catalog = load_catalog_data()
    return format_focus_area_domain_summary(semester_courses, elective_catalog)

def answer_semester_subjects(query):
    semester = detect_semester(query)
    if not semester:
        return FALLBACK_MESSAGE

    chunks = load_all_chunks()
    if not chunks:
        return FALLBACK_MESSAGE

    semester_courses, course_lookup = build_semester_course_catalog(chunks)
    course_rows = filter_valid_subject_rows(semester_courses.get(semester, []))
    if not course_rows:
        return FALLBACK_MESSAGE

    course_docs = {}
    for doc in chunks:
        meta = doc.metadata or {}
        if meta.get("type") != "course":
            continue

        course_code = str(meta.get("course_code") or "").upper()
        if not is_valid_course_code(course_code):
            continue

        resolved = course_lookup.get(course_code)
        if not resolved or resolved.get("semester") != semester:
            continue

        course_docs.setdefault(course_code, doc)

    subjects = []
    seen = set()

    for row in course_rows:
        course_code = row["course_code"]
        if course_code in seen or course_code not in course_docs:
            continue

        seen.add(course_code)
        subject_name = clean_course_name(row.get("course_name"))
        if subject_name and is_valid_semester_subject_row(row):
            subjects.append(f"- **{course_code}** {subject_name}")

    if not subjects:
        return FALLBACK_MESSAGE

    header = format_semester_label(semester)
    return f"### Subjects in {header}:\n\n" + "\n".join(subjects)

# =========================================================
# STATE MANAGEMENT
# =========================================================
for key, default in [("chat_history", []), ("query_count", 0), ("last_docs", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

def process_query(query):
    if is_subject_list_query(query):
        return answer_semester_subjects(query), []
    if is_ai_curriculum_query(query):
        return answer_ai_curriculum_subjects(query), []
    if is_focus_area_query(query):
        return answer_focus_areas(query), []
    if is_pcc_list_query(query):
        return answer_pcc_subjects(query), []
    if is_elective_listing_query(query):
        return answer_elective_query(query), []
    if is_credit_query(query):
        credit_answer = answer_course_credit_query(query)
        if credit_answer != FALLBACK_MESSAGE:
            return credit_answer, []

    docs = hybrid_search(query)
    answer = generate_answer(query, docs)
    return answer, docs

def fire_query(q):
    q = q.strip()
    if not q: return
    st.session_state.query_count += 1
    st.session_state.chat_history.append(("user", q))
    answer, docs = process_query(q)
    st.session_state.chat_history.append(("bot", answer))
    st.session_state.last_docs = docs

def go_home():
    st.session_state.chat_history = []
    st.session_state.last_docs = []


# =========================================================
# THE SIDEBAR
# =========================================================
with st.sidebar:
    # Brand Header
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 30px;">
        <div style="width: 32px; height: 32px; border-radius: 6px; background: var(--color-primary); display: flex; align-items: center; justify-content: center; color: #000;">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1; font-size: 20px;">school</span>
        </div>
        <div>
            <h1 style="font-size: 16px; font-weight: 700; color: var(--text-on-surface); margin: 0; line-height: 1.1;">CollegeGPT</h1>
            <p style="font-size: 11px; color: var(--text-on-surface-variant); margin: 0;">Syllabus Assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    user_questions = [
        message
        for role, message in st.session_state.chat_history
        if role == "user"
    ]
    if user_questions:
        st.markdown('<div class="slbl">CHAT HISTORY</div>', unsafe_allow_html=True)
        history_lines = [
            f'<div class="history-item">{html.escape(question)}</div>'
            for question in user_questions[-6:]
        ]
        st.markdown(
            '<div class="history-list">' + "".join(history_lines) + '</div>',
            unsafe_allow_html=True,
        )

    # Session Stats
    st.markdown('<div class="slbl">SESSION</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card"><span class="stat-lbl">Status</span><span class="stat-val primary">Active</span></div>
        <div class="stat-card"><span class="stat-lbl">Queries</span><span class="stat-val">{st.session_state.query_count}</span></div>
        <div class="stat-card"><span class="stat-lbl">Semesters</span><span class="stat-val">8</span></div>
        <div class="stat-card"><span class="stat-lbl">Mode</span><span class="stat-val">Hybrid</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Questions
    st.markdown('<div class="slbl">QUICK QUESTIONS</div>', unsafe_allow_html=True)
    
    if st.button("Subjects in semester 5", icon=":material/format_list_bulleted:", use_container_width=True):
        fire_query("Subjects in semester 5"); st.rerun()
    if st.button("Credits of DBMS", icon=":material/database:", use_container_width=True):
        fire_query("Credits of DBMS"); st.rerun()
    if st.button("Operating Systems syllabus", icon=":material/settings:", use_container_width=True):
        fire_query("Operating Systems syllabus"); st.rerun()
    if st.button("Courses in semester 3", icon=":material/school:", use_container_width=True):
        fire_query("Courses in semester 3"); st.rerun()
    if st.button("Computer Networks topics", icon=":material/public:", use_container_width=True):
        fire_query("Computer Networks topics"); st.rerun()
    if st.button("Data Structures in semester 3", icon=":material/code:", use_container_width=True):
        fire_query("Data Structures in semester 3"); st.rerun()

    # Capabilities
    st.markdown('<div class="slbl" style="margin-top: 30px;">CAPABILITIES</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="feat"><span class="material-symbols-outlined icon">check</span> Hybrid search</div>
    <div class="feat"><span class="material-symbols-outlined icon">check</span> Semester detection</div>
    <div class="feat"><span class="material-symbols-outlined icon">check</span> AI-generated answers</div>
    <div class="feat"><span class="material-symbols-outlined icon">check</span> Source attribution</div>
    """, unsafe_allow_html=True)


# =========================================================
# MAIN CANVAS (Hero + Chat)
# =========================================================
st.markdown("""
<div class="top-header">
    <div class="header-left">
        <span class="material-symbols-outlined icon">chat</span>
        <div>
            <h2>Ask your syllabus</h2>
            <p>Type a question or pick a quick question</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

if not st.session_state.chat_history:
    # EMPTY STATE
    st.markdown("""
    <div class="hero-container">
        <div class="hero-icon-box"><span class="material-symbols-outlined icon">school</span></div>
        <h2 class="hero-title">What do you want to know?</h2>
        <p class="hero-sub">Ask about any subject, semester, credits, or syllabus topic.</p>
    </div>
    """, unsafe_allow_html=True)

    # Wide Pill Buttons
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("Subjects in semester 5", use_container_width=True): fire_query("Subjects in semester 5"); st.rerun()
        if st.button("Operating Systems syllabus", use_container_width=True): fire_query("Operating Systems syllabus"); st.rerun()
        if st.button("Computer Networks topics", use_container_width=True): fire_query("Computer Networks topics"); st.rerun()
    with c2: 
        if st.button("Credits of DBMS", use_container_width=True): fire_query("Credits of DBMS"); st.rerun()
        if st.button("Courses in semester 3", use_container_width=True): fire_query("Courses in semester 3"); st.rerun()
        if st.button("Data Structures in semester 3", use_container_width=True): fire_query("Data Structures in semester 3"); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Semester Row 
    st.markdown('<div class="sem-pills-row">', unsafe_allow_html=True)
    sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8 = st.columns(8)
    sem_labels = ["Sem I", "Sem II", "Sem III", "Sem IV", "Sem V", "Sem VI", "Sem VII", "Sem VIII"]
    for idx, col in enumerate([sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8]):
        with col:
            if st.button(sem_labels[idx], use_container_width=True):
                fire_query(f"Subjects in {sem_labels[idx]}"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # CHAT HISTORY STATE
    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("Back", icon=":material/arrow_back:", use_container_width=True):
            go_home()
            st.rerun()

    for role, message in st.session_state.chat_history:
        with st.chat_message(role, avatar="🧑" if role == "user" else "🎓"):
            st.write(message)
            
    # Source attribution expander 
    if st.session_state.last_docs:
        col1, col2 = st.columns([3, 1]) 
        with col1:
            with st.expander("📄 Retrieved syllabus sources"):
                for doc in st.session_state.last_docs:
                    st.json(doc.metadata)
                    content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                    st.write(content[:500] + "...")
                    st.divider()

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PINNED CHAT INPUT
# =========================================================
prompt = st.chat_input("Ask anything from syllabus...")
if prompt:
    with st.spinner("Searching syllabus..."):
        fire_query(prompt)
    st.rerun()
