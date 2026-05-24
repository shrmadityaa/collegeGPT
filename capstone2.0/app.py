import re
import pickle
import streamlit as st
from datetime import datetime

# --- Import your local modules ---
from retrieval.hybrid import hybrid_search
from llm.generator import generate_answer
from guardrails import FALLBACK_MESSAGE


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="CollegeGPT Syllabus Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded", # Forces sidebar open on load
)


# =========================================================
# THEME CSS & SIDEBAR FIXES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* ---- Safe Font Reset ---- */
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

/* ---- Palette Variables ---- */
:root {
    --bg-background: #0e1117;
    --bg-surface-low: #161b22;
    --bg-surface: #0e1117;
    --bg-surface-variant: #21262d;
    --border-outline: #30363d;
    --border-outline-variant: #21262d;
    --text-on-background: #c9d1d9;
    --text-on-surface: #ffffff;
    --text-on-surface-variant: #8b949e;
    --color-primary: #57f1db;
}

.stApp { background: var(--bg-background) !important; color: var(--text-on-background) !important; }

/* FIX: Only hide the top right menu, NOT the whole header (which holds the sidebar toggle) */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0rem !important; }

/* =========================================================
   THE PULL-OUT SYMBOL (COLLAPSED CONTROL)
   ========================================================= */
[data-testid="collapsedControl"] {
    color: var(--color-primary) !important;
    background-color: var(--bg-surface-variant) !important;
    border: 1px solid var(--color-primary) !important;
    border-radius: 50% !important;
    top: 0.5rem !important;
    left: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(87, 241, 219, 0.15) !important;
    z-index: 9999 !important;
}
[data-testid="collapsedControl"]:hover {
    background-color: var(--color-primary) !important;
    color: #000 !important;
}

/* ---- Sidebar Styling ---- */
section[data-testid="stSidebar"] {
    background: var(--bg-surface-low) !important;
    border-right: 1px solid var(--border-outline) !important;
}
section[data-testid="stSidebar"] .block-container { padding: 24px 16px !important; }

/* Sidebar Buttons (Quick Questions) */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 0.5rem !important;
    color: var(--text-on-background) !important;
    font-size: 13px !important;
    padding: 10px 12px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    margin-bottom: 8px !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: var(--bg-surface-variant) !important;
    border-color: var(--color-primary) !important;
    color: var(--text-on-surface) !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {
    margin: 0 !important; 
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

/* Stat Cards */
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 24px; }
.stat-card {
    background: transparent; border: 1px solid var(--border-outline);
    border-radius: 0.5rem; padding: 10px; display: flex; flex-direction: column;
}
.stat-lbl { font-size: 11px; color: var(--text-on-surface-variant); font-weight: 500; }
.stat-val { font-size: 15px; font-weight: 600; color: var(--text-on-surface); margin-top: 4px;}
.stat-val.primary { color: var(--color-primary); }

.slbl { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-on-surface-variant); margin-bottom: 12px; }
.feat { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-on-background); margin-bottom: 10px; }
.feat .icon { color: var(--color-primary); font-size: 16px; font-weight: bold;}

/* ---- Main Header ---- */
.top-header {
    display: flex; justify-content: space-between; padding: 0 32px; height: 60px; 
    border-bottom: 1px solid var(--border-outline); background: var(--bg-background); 
    width: 100%; align-items: center; position: sticky; top: 0; z-index: 99;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left .icon { color: var(--text-on-surface-variant); font-size: 20px; }
.header-left h2 { font-size: 14px; margin: 0; color: var(--text-on-surface); font-weight: 600; }
.header-left p { font-size: 12px; margin: 0; color: var(--text-on-surface-variant); }

/* ---- Empty State Hero ---- */
.hero-container {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 30px 24px 20px; text-align: center; margin-top: 10px;
}
.hero-icon-box {
    width: 56px; height: 56px; border-radius: 50%; background: var(--bg-surface-variant); 
    border: 1px solid var(--border-outline); display: flex; align-items: center; 
    justify-content: center; margin-bottom: 20px;
}
.hero-icon-box .icon { font-size: 28px; color: var(--text-on-surface); }
.hero-title { font-size: 32px; font-weight: 700; color: var(--text-on-surface); margin-bottom: 8px; letter-spacing: -0.01em; }
.hero-sub { font-size: 15px; color: var(--text-on-background); margin-bottom: 30px; }

/* ---- Pill Buttons (Hero center area) ---- */
div[data-testid="stMainBlockContainer"] div.stButton > button {
    background: transparent !important; border: 1px solid var(--border-outline) !important;
    border-radius: 9999px !important; color: var(--text-on-background) !important; font-size: 13px !important;
    padding: 6px 16px !important; transition: all 0.2s ease !important; margin-bottom: 12px !important;
}
div[data-testid="stMainBlockContainer"] div.stButton > button:hover { 
    background: var(--bg-surface-variant) !important; border-color: var(--text-on-surface-variant) !important; 
}
.sem-pills-row div.stButton > button { padding: 4px 12px !important; border-radius: 0.5rem !important; }

/* ---- Source Expander styling ---- */
div[data-testid="stExpander"] {
    background-color: var(--bg-surface-low) !important;
    border: 1px solid var(--border-outline) !important;
    border-radius: 0.75rem !important;
    margin-top: 1rem !important;
}

/* ---- Chat Input ---- */
div[data-testid="stChatInput"] { background: var(--bg-surface-low) !important; border: 1px solid var(--border-outline) !important; border-radius: 0.5rem !important; }
div[data-testid="stChatInput"] textarea { color: var(--text-on-surface) !important; }
div[data-testid="stChatInput"] button { color: var(--color-primary) !important; }

/* Main wrapper padding adjusted */
.main-wrapper { padding: 10px 40px; max-width: 900px; margin: 0 auto; padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# BACKEND LOGIC & CONSTANTS
# =========================================================
SEMESTER_MAP = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII",
    "i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V", "vi": "VI", "vii": "VII", "viii": "VIII",
}

@st.cache_data(show_spinner=False)
def load_all_chunks():
    try:
        with open("extracted/chunks.pkl", "rb") as f:
            return pickle.load(f)
    except Exception:
        return []

def detect_semester(query):
    q = query.lower()
    match = re.search(r"\b(?:semester|sem)\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b", q, re.IGNORECASE)
    if not match: return None
    value = match.group(1).lower()
    roman = SEMESTER_MAP.get(value)
    if not roman: return None
    return f"SEMESTER-{roman}"

def is_subject_list_query(query):
    q = query.lower()
    has_semester = detect_semester(query) is not None
    has_subject_word = any(word in q for word in ["subject", "subjects", "course", "courses", "paper", "papers", "list"])
    return has_semester and has_subject_word

def clean_course_name(name):
    name = str(name or "")
    name = name.replace(":", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip()

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

def answer_semester_subjects(query):
    semester = detect_semester(query)
    if not semester: return FALLBACK_MESSAGE
    chunks = load_all_chunks()
    if not chunks: return FALLBACK_MESSAGE
    
    subjects, seen = [], set()
    for doc in chunks:
        meta = doc.metadata or {}
        if str(meta.get("semester")) != semester: continue
        course_code, course_name = meta.get("course_code"), meta.get("course_name")
        if not course_code or not course_name: continue
        clean_name = clean_course_name(course_name)
        key = (course_code, clean_name)
        if key not in seen:
            seen.add(key)
            subjects.append(f"**{course_code}** - {clean_name}")
            
    if not subjects:
        semester_text, collecting = "", False
        next_semester_order = {
            "SEMESTER-I": "SEMESTER-II", "SEMESTER-II": "SEMESTER-III", "SEMESTER-III": "SEMESTER-IV",
            "SEMESTER-IV": "SEMESTER-V", "SEMESTER-V": "SEMESTER-VI", "SEMESTER-VI": "SEMESTER-VII",
            "SEMESTER-VII": "SEMESTER-VIII",
        }
        next_sem = next_semester_order.get(semester)
        
        for doc in chunks:
            text = doc.page_content or ""
            upper_text = text.upper()
            if semester in upper_text: collecting = True
            if collecting: semester_text += "\n" + text
            if collecting and next_sem and next_sem in upper_text: break
            
        extracted = extract_courses_from_text(semester_text)
        for code, name in extracted:
            key = (code, name)
            if key not in seen:
                seen.add(key)
                subjects.append(f"**{code}** - {name}")
                
    if not subjects: return FALLBACK_MESSAGE
    
    response = f"### Subjects in {semester.replace('-', ' ')}:\n\n"
    for subject in subjects: response += f"- {subject}\n"
    return response.strip()

# =========================================================
# STATE MANAGEMENT
# =========================================================
for key, default in [("chat_history", []), ("query_count", 0), ("last_docs", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

def process_query(query):
    if is_subject_list_query(query):
        return answer_semester_subjects(query), []
    else:
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