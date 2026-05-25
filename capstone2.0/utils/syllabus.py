import re
from collections import defaultdict


SEMESTER_ROMAN_MAP = {
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

SEMESTER_QUERY_PATTERN = re.compile(
    r"\b(?:semester|sem)\s*(1|2|3|4|5|6|7|8|i|ii|iii|iv|v|vi|vii|viii)\b",
    re.IGNORECASE,
)
SEMESTER_HEADER_PATTERN = re.compile(
    r"\bSEMESTER[-\s]*(VIII|VII|VI|V|IV|III|II|I|8|7|6|5|4|3|2|1)\b",
    re.IGNORECASE,
)
ELECTIVE_SLOT_PATTERN = re.compile(r"\bElective\s*(I|II|III|IV|1|2|3|4)\b", re.IGNORECASE)
VALID_COURSE_CODE_PATTERN = re.compile(r"^U[A-Z]{2,5}\d{3}$")
COURSE_CODE_OR_PLACEHOLDER_PATTERN = re.compile(r"^U[A-Z]{2,5}(?:\d{3}|XXX)$")
COURSE_CODE_PATTERN = re.compile(r"\bU[A-Z]{2,5}(?:\d{3}|XXX)\b", re.IGNORECASE)
COURSE_ROW_PATTERN = re.compile(
    r"\b\d+\.?\s+"
    r"(U[A-Z]{2,5}(?:\d{3}|XXX))\s+"
    r"(.+?)\s+"
    r"(BSC|ESC|PCC|PEC|OEC|HSS|PRJ|OTH)\s+"
    r"([0-9*-]+)\s+([0-9*-]+)\s+([0-9*-]+)\s+([0-9.]+)",
    re.IGNORECASE,
)
CREDITS_PATTERN = re.compile(
    r"\bL\s*T\s*P\s*Cr\s*([0-9*-]+)\s+([0-9*-]+)\s+([0-9*-]+)\s+([0-9.]+)\b",
    re.IGNORECASE,
)

COURSE_ALIAS_MAP = {
    "UCS303": ["operating systems", "os"],
    "UCS310": ["dbms", "database management system"],
    "UCS414": ["computer network", "cn"],
    "UML501": ["ml"],
    "UTA018": ["oop", "oops"],
}

COURSE_TEXT_STOPWORDS = {
    "the",
    "and",
    "for",
    "of",
    "to",
    "in",
    "with",
    "on",
    "an",
    "a",
}

ELECTIVE_TOPIC_KEYWORDS = {
    "ai": [
        "ai",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "computer vision",
        "nlp",
        "natural language processing",
        "conversational ai",
        "generative ai",
        "agentic ai",
        "speech processing",
        "robotics",
        "edge ai",
        "reinforcement learning",
        "data science",
    ],
    "cyber_security": [
        "cyber security",
        "cybersecurity",
        "security",
        "ethical hacking",
        "secure coding",
        "cyber forensics",
        "forensic",
        "blockchain",
        "network defence",
        "network defense",
        "computer network security",
        "hacking",
    ],
}

FOCUS_AREA_QUERY_TERMS = [
    "focus area",
    "focus areas",
    "specialization",
    "specializations",
    "domain",
    "domains",
    "pathway",
    "pathways",
    "track",
    "tracks",
    "elective focus",
]

FOCUS_AREA_AFTER_SEMESTER_IV_TERMS = [
    "after semester iv",
    "after semester 4",
    "after sem iv",
    "after sem 4",
    "semester iv",
    "semester 4",
    "sem iv",
    "sem 4",
]

FOCUS_DOMAIN_KEYWORDS = [
    (
        "AI / Machine Learning",
        [
            "machine learning",
            "artificial intelligence",
            " ai",
            "agentic ai",
            "computer vision",
            "image processing",
            "deep learning",
            "natural language processing",
            "nlp",
            "speech processing",
            "generative ai",
            "conversational ai",
            "robotics",
            "reinforcement learning",
        ],
    ),
    (
        "Cyber Security",
        [
            "cyber",
            "security",
            "secure coding",
            "ethical hacking",
            "hacking",
            "forensic",
            "blockchain",
            "network defence",
            "network defense",
        ],
    ),
    (
        "Data Analytics",
        [
            "data analytics",
            "data science",
            "predictive analytics",
            "statistics",
            "statistical",
            "analytics",
            "database",
            "matrix computation",
            "numerical optimization",
        ],
    ),
    (
        "Networking",
        [
            "network",
            "communication",
            "connected vehicles",
        ],
    ),
    (
        "Intelligent Transportation",
        [
            "intelligent transportation",
            "automobile",
            "mobility systems",
            "connected vehicles",
        ],
    ),
    (
        "Software Systems",
        [
            "software engineering",
            "enterprise web",
            "source code management",
            "build and release",
            "continuous integration",
            "continuous deployment",
            "test automation",
            "compiler",
            "cloud",
            "devops",
            "system provisioning",
            "configuration management",
            "database engineer",
            "computer architecture",
            "theory of computation",
            "parallel",
            "distributed computing",
            "gpu computing",
        ],
    ),
    (
        "Emerging Technologies",
        [
            "augmented",
            "virtual reality",
            "3d modelling",
            "animation",
            "game design",
            "simulation",
            "modelling",
            "modeling",
            "ui",
            "ux",
            "edge ai",
            "robotics",
        ],
    ),
]

AI_CURRICULUM_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "agentic ai",
    "intelligent systems",
    "nlp",
    "natural language processing",
    "robotics",
    "computer vision",
    "data science",
    "data analytics",
    "deep learning",
    "generative ai",
    "conversational ai",
]

SEMESTER_SUBJECT_INVALID_PATTERNS = [
    "STARTS PRJ",
    "GENERIC ELECTIVE",
    "START-UP",
    "PROJECT SEMESTER",
]

SEMESTER_SUBJECT_TABLE_FRAGMENTS = [
    "TOTAL",
    "GENERIC ELECTIVE",
    "STARTS PRJ",
    "L T P",
    "PRJ",
    "PEC",
    "OEC",
]


def normalize_semester_token(value):
    key = str(value or "").strip().lower()
    roman = SEMESTER_ROMAN_MAP.get(key)
    return f"SEMESTER-{roman}" if roman else None


def detect_query_semester(text):
    match = SEMESTER_QUERY_PATTERN.search(str(text or ""))
    if not match:
        return None
    return normalize_semester_token(match.group(1))


def detect_semester_header(text):
    match = SEMESTER_HEADER_PATTERN.search(str(text or ""))
    if not match:
        return None
    return normalize_semester_token(match.group(1))


def clean_course_name(name):
    name = str(name or "")
    name = re.sub(r"^[\s:;\-]+", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def normalize_course_text(text):
    text = clean_course_name(text).lower()
    text = text.replace("&", " and ")
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9+]+", " ", text)
    words = []

    for word in text.split():
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 4 and not word.endswith("ss"):
            word = word[:-1]
        words.append(word)

    return " ".join(words)


def tokenize_course_text(text):
    return {
        word
        for word in normalize_course_text(text).split()
        if len(word) >= 2 and word not in COURSE_TEXT_STOPWORDS
    }


def is_valid_course_code(course_code):
    return bool(VALID_COURSE_CODE_PATTERN.fullmatch(str(course_code or "").upper()))


def is_course_code_or_placeholder(course_code):
    return bool(COURSE_CODE_OR_PLACEHOLDER_PATTERN.fullmatch(str(course_code or "").upper()))


def normalize_overview_text(text):
    text = str(text or "")
    text = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_query_intents(query):
    q_norm = normalize_course_text(query)
    q_tokens = set(q_norm.split())
    intents = set()

    if any(word in q_norm for word in ["credit", "ltp", "credit structure", "credit of"]):
        intents.add("credits")
    if any(word in q_norm for word in ["lab", "laboratory", "practical", "experiment"]):
        intents.add("lab")
    if any(word in q_norm for word in ["evaluation", "weightage", "marks", "mst", "est", "assessment"]):
        intents.add("evaluation")
    if any(word in q_norm for word in ["outcome", "outcomes", "objective", "objectives"]) or {"clo", "clos", "cos"} & q_tokens:
        intents.add("clo")
    if any(word in q_norm for word in ["syllabus", "topic", "topics", "module", "modules"]):
        intents.add("syllabus")
    if any(word in q_norm for word in ["overview", "summary", "summarize", "short overview"]):
        intents.add("overview")
    if "elective" in q_norm:
        intents.add("elective")
    if "pcc" in q_norm or "professional core" in q_norm:
        intents.add("pcc")

    if not intents:
        intents.add("overview")

    return intents


def detect_elective_slot(query):
    match = ELECTIVE_SLOT_PATTERN.search(str(query or ""))
    if not match:
        return None

    raw_value = match.group(1).upper()
    numeric_map = {"1": "I", "2": "II", "3": "III", "4": "IV"}
    return numeric_map.get(raw_value, raw_value)


def detect_elective_topic(query):
    q_norm = normalize_course_text(query)

    for topic, keywords in ELECTIVE_TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if text_matches_keyword(q_norm, normalize_course_text(keyword)):
                return topic

    return None


def is_elective_query(query):
    return "elective" in normalize_course_text(query)


def is_pcc_list_query(query):
    q_norm = normalize_course_text(query)
    has_pcc = "pcc" in q_norm or "professional core" in q_norm
    has_list_intent = any(word in q_norm for word in ["list", "subject", "course", "semester wise", "semester wise"])
    return has_pcc and has_list_intent


def is_credit_query(query):
    q_norm = normalize_course_text(query)
    return "credit" in q_norm or "ltp" in q_norm


def is_ai_curriculum_query(query):
    q_norm = normalize_course_text(query)
    has_curriculum_intent = any(
        phrase in q_norm
        for phrase in [
            "curriculum",
            "subject",
            "subjects",
            "course",
            "courses",
        ]
    )
    has_ai_term = any(
        text_matches_keyword(q_norm, normalize_course_text(keyword))
        for keyword in AI_CURRICULUM_KEYWORDS
    )
    return has_curriculum_intent and has_ai_term


def is_focus_area_query(query):
    q_norm = normalize_course_text(query)
    has_focus_intent = any(
        text_matches_keyword(q_norm, normalize_course_text(phrase))
        for phrase in FOCUS_AREA_QUERY_TERMS
    )
    has_semester_iv = any(
        text_matches_keyword(q_norm, normalize_course_text(phrase))
        for phrase in FOCUS_AREA_AFTER_SEMESTER_IV_TERMS
    )
    return has_focus_intent and has_semester_iv


def format_semester_label(semester):
    semester = str(semester or "").strip().upper()
    if not semester.startswith("SEMESTER-"):
        return semester.title()

    roman = semester.split("-", 1)[1].upper()
    return f"Semester {roman}"


def is_pcc_listing_row(semester, row):
    code_type = str((row or {}).get("code_type") or "").upper()
    semester = str(semester or "").upper()

    if code_type == "PCC":
        return True

    if semester in {"SEMESTER-I", "SEMESTER-II"} and code_type in {"BSC", "ESC", "HSS", "OTH"}:
        return True

    return False


def is_valid_semester_subject_row(row):
    row = row or {}
    course_name = clean_course_name(row.get("course_name"))
    course_name_upper = course_name.upper()

    if not course_name:
        return False

    if any(pattern in course_name_upper for pattern in SEMESTER_SUBJECT_INVALID_PATTERNS):
        return False

    numeric_tokens = re.findall(r"\b\d+(?:\.\d+)?\b", course_name)
    word_tokens = re.findall(r"[A-Za-z][A-Za-z&'\-]*", course_name)
    fragment_hits = sum(
        1 for fragment in SEMESTER_SUBJECT_TABLE_FRAGMENTS
        if fragment in course_name_upper
    )

    if len(numeric_tokens) >= 4:
        return False

    if len(word_tokens) > 8 and (len(numeric_tokens) >= 2 or fragment_hits >= 2):
        return False

    if fragment_hits >= 2 and numeric_tokens:
        return False

    return True


def filter_valid_subject_rows(rows):
    return [row for row in rows if is_valid_semester_subject_row(row)]


def split_semester_sections(text):
    normalized = normalize_overview_text(text)
    matches = list(SEMESTER_HEADER_PATTERN.finditer(normalized))
    sections = []

    for index, match in enumerate(matches):
        semester = normalize_semester_token(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        sections.append((semester, normalized[start:end]))

    return sections


def extract_semester_courses(section_text):
    normalized = normalize_overview_text(section_text)
    total_match = re.search(r"\bTOTAL\b", normalized, re.IGNORECASE)
    if total_match:
        normalized = normalized[:total_match.start()]

    courses = []
    seen = set()

    for match in COURSE_ROW_PATTERN.finditer(normalized):
        course_code = match.group(1).upper()
        course_name = clean_course_name(match.group(2))
        code_type = match.group(3).upper()

        if not is_valid_course_code(course_code) or not course_name:
            continue

        key = (course_code, course_name)
        if key in seen:
            continue
        seen.add(key)

        l_val, t_val, p_val, credits = (match.group(i).strip() for i in range(4, 8))
        courses.append(
            {
                "course_code": course_code,
                "course_name": course_name,
                "code_type": code_type,
                "ltp": f"{l_val}-{t_val}-{p_val}",
                "credits": credits,
            }
        )

    return courses


def build_semester_course_catalog(docs):
    semester_courses = defaultdict(list)
    course_lookup = {}
    seen = set()

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        if metadata.get("type") != "page":
            continue

        for semester, section in split_semester_sections(getattr(doc, "page_content", "")):
            for course in extract_semester_courses(section):
                key = (semester, course["course_code"])
                if key in seen:
                    continue
                seen.add(key)

                entry = {**course, "semester": semester}
                semester_courses[semester].append(entry)
                course_lookup.setdefault(course["course_code"], entry)

    return dict(semester_courses), course_lookup


def split_elective_sections(text):
    normalized = normalize_overview_text(text)
    matches = list(ELECTIVE_SLOT_PATTERN.finditer(normalized))
    sections = []

    for index, match in enumerate(matches):
        slot = detect_elective_slot(match.group(0))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        sections.append((slot, normalized[start:end]))

    return sections


def build_elective_catalog(docs):
    electives = []
    seen = set()

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        if metadata.get("type") != "page":
            continue

        page_text = getattr(doc, "page_content", "")
        for slot, section in split_elective_sections(page_text):
            for match in COURSE_ROW_PATTERN.finditer(section):
                course_code = match.group(1).upper()
                course_name = clean_course_name(match.group(2))
                code_type = match.group(3).upper()

                if code_type != "PEC" or not is_course_code_or_placeholder(course_code) or not course_name:
                    continue

                key = (slot, course_code)
                if key in seen:
                    continue
                seen.add(key)

                l_val, t_val, p_val, credits = (match.group(i).strip() for i in range(4, 8))
                electives.append(
                    {
                        "slot": slot,
                        "course_code": course_code,
                        "course_name": course_name,
                        "code_type": code_type,
                        "semester": metadata.get("semester"),
                        "ltp": f"{l_val}-{t_val}-{p_val}",
                        "credits": credits,
                    }
                )

    return electives


def is_ai_related_name(name):
    name_norm = normalize_course_text(name)
    return any(
        text_matches_keyword(name_norm, normalize_course_text(keyword))
        for keyword in AI_CURRICULUM_KEYWORDS
    )


def collect_ai_related_subjects(semester_courses, elective_catalog):
    core_subjects = []
    elective_subjects = []
    seen_core = set()
    seen_elective = set()
    semester_order = {
        "SEMESTER-I": 1,
        "SEMESTER-II": 2,
        "SEMESTER-III": 3,
        "SEMESTER-IV": 4,
        "SEMESTER-V": 5,
        "SEMESTER-VI": 6,
        "SEMESTER-VII": 7,
        "SEMESTER-VIII": 8,
    }
    slot_order = {"I": 1, "II": 2, "III": 3, "IV": 4}

    for semester, rows in semester_courses.items():
        for row in rows:
            if not is_valid_semester_subject_row(row):
                continue
            if not is_ai_related_name(row.get("course_name")):
                continue

            key = row["course_code"]
            if key in seen_core:
                continue
            seen_core.add(key)
            core_subjects.append({**row, "semester": semester})

    for row in elective_catalog:
        if not is_ai_related_name(row.get("course_name")):
            continue

        key = (row["slot"], row["course_code"])
        if key in seen_elective:
            continue
        seen_elective.add(key)
        elective_subjects.append(row)

    core_subjects.sort(key=lambda row: (semester_order.get(row["semester"], 99), row["course_code"]))
    elective_subjects.sort(key=lambda row: (slot_order.get(row["slot"], 99), row["course_code"]))
    return core_subjects, elective_subjects


def format_course_display_name(name):
    name = clean_course_name(name)
    if not name:
        return ""

    if name.upper() == name:
        name = name.title()

    for word in ["And", "For", "In", "Of", "The", "Using"]:
        name = re.sub(rf"\b{word}\b", word.lower(), name)

    replacements = {
        " Ai": " AI",
        "Al AI": "al AI",
        "Conversation al AI": "Conversational AI",
        "Ui": "UI",
        "Ux": "UX",
        "Gpu": "GPU",
        "Nlp": "NLP",
        "Devops": "DevOps",
        "3D": "3D",
        "Iot": "IoT",
        "Ii": "II",
        "Iii": "III",
        "Iv": "IV",
        "Configuration Management Mana": "Configuration Management",
    }

    for wrong, right in replacements.items():
        name = name.replace(wrong, right)

    return name


def _focus_domain_for_course(course_name):
    name_norm = normalize_course_text(course_name)

    for domain, keywords in FOCUS_DOMAIN_KEYWORDS:
        if any(text_matches_keyword(name_norm, normalize_course_text(keyword)) for keyword in keywords):
            return domain

    return None


def build_focus_area_domains(semester_courses, elective_catalog):
    semester_order = {
        "SEMESTER-I": 1,
        "SEMESTER-II": 2,
        "SEMESTER-III": 3,
        "SEMESTER-IV": 4,
        "SEMESTER-V": 5,
        "SEMESTER-VI": 6,
        "SEMESTER-VII": 7,
        "SEMESTER-VIII": 8,
    }
    slot_order = {"I": 1, "II": 2, "III": 3, "IV": 4}
    domain_names = [domain for domain, _ in FOCUS_DOMAIN_KEYWORDS]
    grouped = {domain: [] for domain in domain_names}
    seen = set()

    candidates = []
    for semester, rows in semester_courses.items():
        if semester_order.get(semester, 0) <= 4:
            continue

        for index, row in enumerate(rows):
            if not is_valid_semester_subject_row(row):
                continue

            candidates.append(
                {
                    **row,
                    "source_order": (semester_order.get(semester, 99), index, row.get("course_code") or ""),
                }
            )

    for index, row in enumerate(elective_catalog):
        candidates.append(
            {
                **row,
                "source_order": (20 + slot_order.get(row.get("slot"), 99), index, row.get("course_code") or ""),
            }
        )

    for row in sorted(candidates, key=lambda item: item["source_order"]):
        course_name = format_course_display_name(row.get("course_name"))
        if not course_name:
            continue

        domain = _focus_domain_for_course(course_name)
        if not domain:
            continue

        key = (domain, row.get("course_code"), normalize_course_text(course_name))
        if key in seen:
            continue

        seen.add(key)
        grouped[domain].append(course_name)

    return {domain: grouped[domain] for domain in domain_names if grouped[domain]}


def format_focus_area_domain_summary(semester_courses, elective_catalog):
    grouped = build_focus_area_domains(semester_courses, elective_catalog)
    lines = ["### Focus Areas After Semester IV", ""]

    if not grouped:
        lines.append("No higher-semester focus-area courses were found in the syllabus catalog.")
        return "\n".join(lines)

    for domain, courses in grouped.items():
        lines.append(f"**{domain}:**")
        for course in courses:
            lines.append(f"- {course}")
        lines.append("")

    return "\n".join(lines).strip()


def get_focus_area_page_docs(docs):
    page_docs = [
        doc for doc in docs
        if (getattr(doc, "metadata", {}) or {}).get("type") == "page"
    ]
    start_page = None

    for doc in page_docs:
        text_lower = str(getattr(doc, "page_content", "")).lower()
        if "elective focus" in text_lower:
            start_page = (getattr(doc, "metadata", {}) or {}).get("page")
            break

    if start_page is not None:
        return [
            doc for doc in page_docs
            if (getattr(doc, "metadata", {}) or {}).get("page") in {start_page, start_page + 1}
        ]

    return [
        doc for doc in page_docs
        if "elective focus" in str(getattr(doc, "page_content", "")).lower()
    ]


def clean_focus_area_name(name):
    name = clean_course_name(name)
    replacements = {
        "High Performan Computing": "High Performance Computing",
    }
    return replacements.get(name, name)


def extract_focus_areas(docs):
    focus_docs = get_focus_area_page_docs(docs)
    if not focus_docs:
        return []

    focus_text = " ".join(str(getattr(doc, "page_content", "")) for doc in focus_docs)
    pattern = re.compile(r"(?:^|\s)(\d{1,2})\.\s(.+?)(?=\s\d{1,2}\.\d)", re.IGNORECASE)
    seen = set()
    focus_areas = []

    for match in pattern.finditer(focus_text):
        index = match.group(1)
        name = clean_focus_area_name(match.group(2))
        key = (index, name)
        if key in seen:
            continue
        seen.add(key)
        focus_areas.append({"index": index, "name": name})

    focus_areas.sort(key=lambda item: int(item["index"]))
    return focus_areas


def build_course_name_index(course_lookup):
    index = []

    for course_code, course in course_lookup.items():
        course_name = clean_course_name(course.get("course_name"))
        normalized_name = normalize_course_text(course_name)
        if not normalized_name:
            continue

        variants = {normalized_name}
        for alias in COURSE_ALIAS_MAP.get(course_code, []):
            alias_norm = normalize_course_text(alias)
            if alias_norm:
                variants.add(alias_norm)

        index.append(
            {
                "course_code": course_code,
                "course_name": course_name,
                "semester": course.get("semester"),
                "code_type": course.get("code_type"),
                "normalized_name": normalized_name,
                "tokens": tokenize_course_text(course_name),
                "variants": sorted(variants, key=lambda item: (-len(item), item)),
            }
        )

    return index


def match_query_to_courses(query, course_lookup, course_name_index=None):
    q_norm = normalize_course_text(query)
    q_tokens = tokenize_course_text(query)
    semester_query = detect_query_semester(query)
    course_name_index = course_name_index or build_course_name_index(course_lookup)

    matches = []

    for course in course_name_index:
        score = 0
        matched_variant = None

        for variant in course["variants"]:
            if variant and text_matches_keyword(q_norm, variant):
                matched_variant = variant
                score = 120 + len(variant.split())
                break

        if not score and course["tokens"]:
            overlap = len(course["tokens"].intersection(q_tokens))
            token_ratio = overlap / len(course["tokens"])

            if overlap >= 2 and token_ratio >= 0.75:
                score = 80 + overlap
                matched_variant = course["normalized_name"]

        if score:
            if semester_query and course.get("semester") == semester_query:
                score += 5

            matches.append(
                {
                    **course,
                    "score": score,
                    "matched_variant": matched_variant,
                }
            )

    matches.sort(key=lambda item: (-item["score"], item["course_code"]))
    return matches


def filter_electives_for_query(query, electives):
    slot = detect_elective_slot(query)
    topic = detect_elective_topic(query)
    q_norm = normalize_course_text(query)
    filtered = []

    for elective in electives:
        if slot and elective.get("slot") != slot:
            continue

        if topic:
            name_norm = normalize_course_text(elective.get("course_name"))
            keywords = [normalize_course_text(keyword) for keyword in ELECTIVE_TOPIC_KEYWORDS[topic]]
            if not any(text_matches_keyword(name_norm, keyword) for keyword in keywords):
                continue

        if not slot and not topic and "related to" in q_norm:
            continue

        filtered.append(elective)

    return filtered if filtered else electives if not slot and not topic else []


def extract_credit_details(text):
    match = CREDITS_PATTERN.search(str(text or ""))
    if not match:
        return None

    l_val, t_val, p_val, credits = (match.group(i).strip() for i in range(1, 5))
    return {
        "ltp": f"{l_val}-{t_val}-{p_val}",
        "credits": credits,
    }


def text_matches_keyword(text_norm, keyword_norm):
    if not keyword_norm:
        return False

    if " " in keyword_norm:
        return keyword_norm in text_norm

    return keyword_norm in set(text_norm.split())


def resolve_course_metadata(doc, course_lookup):
    metadata = getattr(doc, "metadata", {}) or {}
    course_code = str(metadata.get("course_code") or "").upper()
    resolved = course_lookup.get(course_code, {})
    credit_details = extract_credit_details(getattr(doc, "page_content", "")) or {}

    course_name = clean_course_name(resolved.get("course_name") or metadata.get("course_name"))
    semester = resolved.get("semester") or metadata.get("semester")
    code_type = resolved.get("code_type") or metadata.get("code_type")

    return {
        "course_code": course_code or None,
        "course_name": course_name or None,
        "semester": semester,
        "code_type": code_type,
        "ltp": credit_details.get("ltp") or resolved.get("ltp"),
        "credits": credit_details.get("credits") or resolved.get("credits"),
    }


def doc_mentions_course(doc, course_match):
    if not course_match:
        return False

    text = normalize_course_text(getattr(doc, "page_content", ""))
    course_code = str(course_match.get("course_code") or "").upper()

    if course_code and course_code.lower() in text:
        return True

    for variant in course_match.get("variants", []):
        if variant and variant in text:
            return True

    return False


def is_lab_practical_query(query):
    return "lab" in detect_query_intents(query)


def _doc_sort_key(doc):
    metadata = getattr(doc, "metadata", {}) or {}
    page = metadata.get("page")
    part = metadata.get("part")
    return (
        page if isinstance(page, int) else 9999,
        part if isinstance(part, int) else 9999,
        str(metadata.get("course_code") or ""),
    )


def _dedupe_docs(docs):
    seen = set()
    unique_docs = []

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        key = (
            metadata.get("type"),
            metadata.get("page"),
            metadata.get("course_code"),
            metadata.get("part"),
            getattr(doc, "page_content", "")[:80],
        )
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)

    return sorted(unique_docs, key=_doc_sort_key)


def _course_lab_source_docs(query, docs, all_chunks, course_lookup, course_name_index):
    source_docs = list(docs or [])
    course_matches = [
        course
        for course in match_query_to_courses(query, course_lookup or {}, course_name_index)
        if course.get("score", 0) >= 80
    ]

    if not all_chunks or not course_matches:
        return _dedupe_docs(source_docs)

    page_docs = [
        doc
        for doc in all_chunks
        if (getattr(doc, "metadata", {}) or {}).get("type") == "page"
    ]
    page_by_number = {
        (getattr(doc, "metadata", {}) or {}).get("page"): doc
        for doc in page_docs
    }
    pages_to_add = set()

    for course in course_matches[:2]:
        course_code = str(course.get("course_code") or "").upper()
        course_name = normalize_course_text(course.get("course_name"))

        for doc in page_docs:
            metadata = getattr(doc, "metadata", {}) or {}
            text = str(getattr(doc, "page_content", "") or "")
            text_norm = normalize_course_text(text)
            page = metadata.get("page")

            if not page:
                continue

            matches_course = (
                course_code and course_code in text.upper()
            ) or (
                course_name and course_name in text_norm
            )

            if not matches_course:
                continue

            pages_to_add.add(page)

            for offset in (1, 2):
                next_doc = page_by_number.get(page + offset)
                if not next_doc:
                    break

                next_text = str(getattr(next_doc, "page_content", "") or "")
                next_starts_course = re.match(r"\s*U[A-Z]{2,5}(?:\d{3}|XXX)\s*:", next_text, re.IGNORECASE)
                if next_starts_course and course_code not in next_text.upper()[:40]:
                    break

                pages_to_add.add(page + offset)

    source_docs.extend(
        doc
        for doc in page_docs
        if (getattr(doc, "metadata", {}) or {}).get("page") in pages_to_add
    )
    return _dedupe_docs(source_docs)


def _extract_lab_practical_span(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    header_match = re.search(
        r"\b(?:Laboratory Work|Practical Work|Lab(?:oratory)? Experiments?)\b\s*:?",
        text,
        re.IGNORECASE,
    )
    if not header_match:
        return ""

    start = header_match.end()
    tail = text[start:]
    stop_match = re.search(
        r"\b(?:Course Learning Objectives?|Course Learning Outcomes?|Course Outcomes?|"
        r"Text Books?|Reference Books?|Evaluation Scheme|Course Objectives?|Syllabus)\b",
        tail,
        re.IGNORECASE,
    )
    if stop_match:
        tail = tail[:stop_match.start()]

    return tail.strip()


def _clean_lab_item(item):
    item = re.sub(r"\s+", " ", str(item or "")).strip(" .;")
    item = item.replace(" -", "-")
    return item


def extract_lab_practical_items(query, docs, all_chunks=None, course_lookup=None, course_name_index=None):
    if not is_lab_practical_query(query):
        return []

    source_docs = _course_lab_source_docs(
        query,
        docs,
        all_chunks,
        course_lookup,
        course_name_index,
    )
    combined_text = " ".join(str(getattr(doc, "page_content", "") or "") for doc in source_docs)
    lab_span = _extract_lab_practical_span(combined_text)
    if not lab_span:
        return []

    items = []
    seen = set()
    numbered_pattern = re.compile(r"(?:^|\s)(\d{1,2})[.)]\s*(.*?)(?=\s\d{1,2}[.)]\s|$)")

    for match in numbered_pattern.finditer(lab_span):
        item = _clean_lab_item(match.group(2))
        if not item:
            continue

        micro_project_split = re.search(r"\bMicro Project\s*:\s*", item, re.IGNORECASE)
        if micro_project_split:
            before = _clean_lab_item(item[:micro_project_split.start()])
            after = _clean_lab_item(item[micro_project_split.start():])
            for candidate in [before, after]:
                key = normalize_course_text(candidate)
                if candidate and key not in seen:
                    seen.add(key)
                    items.append(candidate)
            continue

        key = normalize_course_text(item)
        if key not in seen:
            seen.add(key)
            items.append(item)

    if not items:
        micro_match = re.search(r"\bMicro Project\s*:\s*.*", lab_span, re.IGNORECASE)
        if micro_match:
            items.append(_clean_lab_item(micro_match.group(0)))

    return items


def format_lab_practical_answer(query, docs, all_chunks=None, course_lookup=None, course_name_index=None):
    items = extract_lab_practical_items(
        query,
        docs,
        all_chunks=all_chunks,
        course_lookup=course_lookup,
        course_name_index=course_name_index,
    )
    if not items:
        return ""

    return "\n".join(f"- {item}" for item in items)


def section_match_score(text, intents):
    score = 0
    text_norm = normalize_course_text(text)

    if "credits" in intents and "l t p cr" in text_norm:
        score += 16
    if "syllabus" in intents and "syllabus" in text_norm:
        score += 14
    if "overview" in intents and ("course objective" in text_norm or "course objectives" in text_norm):
        score += 10
    if "clo" in intents and any(
        phrase in text_norm
        for phrase in [
            "course learning objective",
            "course learning outcome",
            "course objective",
            "course objectives",
        ]
    ):
        score += 14
    if "lab" in intents and any(
        phrase in text_norm
        for phrase in [
            "laboratory work",
            "lab experiment",
            "practical work",
            "laboratory experiment",
        ]
    ):
        score += 18
    if "evaluation" in intents and any(
        phrase in text_norm
        for phrase in [
            "evaluation scheme",
            "weightage",
            "sessional",
            "mst",
            "est",
        ]
    ):
        score += 18

    return score
