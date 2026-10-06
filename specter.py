# ============================================================
# SPECTER CYBER v2 - SINGLE FILE
# Authorized Cybersecurity / OSINT Investigation Platform
# ============================================================

# Install first:
# pip install streamlit pandas numpy networkx plotly pillow
# pip install duckduckgo-search sentence-transformers transformers
# pip install accelerate faiss-cpu pytesseract pypdf
#
# Run:
# streamlit run specter.py

import os
import io
import re
import json
import uuid
import sqlite3
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go

try:
    import torch
except Exception:
    torch = None

try:
    import faiss
except Exception:
    faiss = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    from PIL import Image, ImageEnhance, ExifTags
except Exception:
    Image = None

try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    from transformers import pipeline
except Exception:
    pipeline = None


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "SPECTER CYBER"

DATA_DIR = Path("specter_data")
EVIDENCE_DIR = DATA_DIR / "evidence"
INDEX_DIR = DATA_DIR / "indices"

DATA_DIR.mkdir(exist_ok=True)
EVIDENCE_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

DB_FILE = DATA_DIR / "specter.db"
FAISS_FILE = INDEX_DIR / "text.index"
FAISS_META = INDEX_DIR / "text_metadata.json"

EMBEDDING_DIM = 384


st.set_page_config(
    page_title=APP_NAME,
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# DARK UI
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #080b0d;
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d1115;
    }

    h1, h2, h3 {
        color: #00ff88;
    }

    .stButton > button {
        background-color: #101820;
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 6px;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #123326;
        color: white;
    }

    div[data-testid="stMetric"] {
        background-color: #10161b;
        border-left: 3px solid #00ff88;
        border-radius: 5px;
        padding: 8px;
    }

    code {
        color: #00ff88;
    }

    /* Better mobile / tunnel rendering */
    .stSelectbox, .stTextInput, .stTextArea {
        margin-bottom: 0.4rem;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #1a2a22;
        border-radius: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATABASE
# ============================================================

class SpecterDB:

    def __init__(self, path=DB_FILE):
        self.path = str(path)
        self.initialize()

    def connection(self):
        return sqlite3.connect(self.path)

    def initialize(self):

        conn = self.connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS targets (
                target_id TEXT PRIMARY KEY,
                case_id TEXT,
                target_type TEXT,
                value TEXT,
                label TEXT,
                created_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                case_id TEXT,
                target_id TEXT,
                category TEXT,
                title TEXT,
                source TEXT,
                url TEXT,
                indicator TEXT,
                redacted_indicator TEXT,
                confidence REAL,
                first_seen TEXT,
                last_seen TEXT,
                sha256 TEXT,
                notes TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                case_id TEXT,
                filename TEXT,
                path TEXT,
                sha256 TEXT,
                mime TEXT,
                created_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                case_id TEXT,
                event_type TEXT,
                data TEXT,
                created_at TEXT
            )
            """
        )

        conn.commit()
        conn.close()

    def execute(self, query, params=(), fetch=False):

        conn = self.connection()
        cur = conn.cursor()

        cur.execute(query, params)

        result = cur.fetchall() if fetch else None

        conn.commit()
        conn.close()

        return result

    def create_case(self, name, description):

        case_id = "CASE-" + uuid.uuid4().hex[:10].upper()

        now = datetime.utcnow().isoformat()

        self.execute(
            """
            INSERT INTO cases
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                case_id,
                name,
                description,
                now,
                now
            )
        )

        return case_id

    def get_cases(self):

        return self.execute(
            """
            SELECT
                case_id,
                name,
                description,
                created_at
            FROM cases
            ORDER BY created_at DESC
            """,
            fetch=True
        )

    def add_target(
        self,
        case_id,
        target_type,
        value,
        label=""
    ):

        target_id = "TGT-" + uuid.uuid4().hex[:10].upper()

        self.execute(
            """
            INSERT INTO targets
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                target_id,
                case_id,
                target_type,
                value,
                label,
                datetime.utcnow().isoformat()
            )
        )

        return target_id

    def get_targets(self, case_id):

        return self.execute(
            """
            SELECT
                target_id,
                target_type,
                value,
                label,
                created_at
            FROM targets
            WHERE case_id=?
            """,
            (case_id,),
            fetch=True
        )

    def add_finding(self, data):

        finding_id = "F-" + uuid.uuid4().hex[:12].upper()

        now = datetime.utcnow().isoformat()

        self.execute(
            """
            INSERT INTO findings
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding_id,
                data.get("case_id"),
                data.get("target_id"),
                data.get("category"),
                data.get("title"),
                data.get("source"),
                data.get("url"),
                data.get("indicator"),
                data.get("redacted_indicator"),
                data.get("confidence", 0),
                data.get("first_seen", now),
                data.get("last_seen", now),
                data.get("sha256", ""),
                data.get("notes", "")
            )
        )

        return finding_id

    def get_findings(self, case_id):

        return self.execute(
            """
            SELECT
                finding_id,
                category,
                title,
                source,
                url,
                COALESCE(NULLIF(indicator, ''), redacted_indicator) AS indicator,
                confidence,
                first_seen,
                last_seen,
                notes
            FROM findings
            WHERE case_id=?
            ORDER BY last_seen DESC
            """,
            (case_id,),
            fetch=True
        )

    def add_evidence(
        self,
        case_id,
        filename,
        path,
        sha256,
        mime
    ):

        evidence_id = "E-" + uuid.uuid4().hex[:12].upper()

        self.execute(
            """
            INSERT INTO evidence
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                case_id,
                filename,
                str(path),
                sha256,
                mime,
                datetime.utcnow().isoformat()
            )
        )

        return evidence_id

    def add_event(
        self,
        case_id,
        event_type,
        data
    ):

        event_id = "EV-" + uuid.uuid4().hex[:12].upper()

        self.execute(
            """
            INSERT INTO events
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_id,
                case_id,
                event_type,
                json.dumps(data, default=str),
                datetime.utcnow().isoformat()
            )
        )


DB = SpecterDB()


# ============================================================
# REGEX / IOC ENGINE
# ============================================================

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

URL_REGEX = re.compile(
    r"https?://[^\s<>\"]+"
)

IP_REGEX = re.compile(
    r"\b(?:"
    r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\."
    r"){3}"
    r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\b"
)

SHA256_REGEX = re.compile(
    r"\b[a-fA-F0-9]{64}\b"
)

SHA1_REGEX = re.compile(
    r"\b[a-fA-F0-9]{40}\b"
)

MD5_REGEX = re.compile(
    r"\b[a-fA-F0-9]{32}\b"
)

CVE_REGEX = re.compile(
    r"\bCVE-\d{4}-\d{4,7}\b",
    re.I
)

PHONE_REGEX = re.compile(
    r"(?<!\w)"
    r"(?:\+\d{1,3}[\s.-]?)?"
    r"(?:\d[\s.-]?){7,14}\d"
    r"(?!\w)"
)

CRYPTO_REGEX = re.compile(
    r"\b(?:"
    r"bc1[a-z0-9]{20,90}"
    r"|"
    r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}"
    r"|"
    r"0x[a-fA-F0-9]{40}"
    r")\b"
)


SIGNAL_TERMS = {

    "leak": [
        "data leak",
        "leaked data",
        "breach",
        "database dump",
        "exposed database",
        "stolen data"
    ],

    "ransomware": [
        "ransomware",
        "extortion",
        "victim list",
        "leak site"
    ],

    "credential_exposure": [
        "credential",
        "password",
        "login",
        "stealer",
        "combo list",
        "session token",
        "access token"
    ],

    "crime": [
        "arrested",
        "crime",
        "fraud",
        "scam",
        "investigation",
        "indicted",
        "convicted",
        "police",
        "court"
    ],

    "trafficking_exploitation": [
        "trafficking",
        "exploitation",
        "non-consensual",
        "sextortion",
        "coercion"
    ],

    "adult_service_signal": [
        "escort",
        "prostitution",
        "adult service"
    ]
}


def redact(value, kind="generic"):

    if not value:
        return ""

    if kind == "email" and "@" in value:

        user, domain = value.split("@", 1)

        if len(user) <= 2:
            return "***@" + domain

        return user[:2] + "***@" + domain

    if kind == "phone":

        digits = re.sub(
            r"\D",
            "",
            value
        )

        if len(digits) >= 4:
            return "***" + digits[-4:]

        return "***"

    if len(value) <= 6:
        return "***"

    return (
        value[:3]
        + "***"
        + value[-3:]
    )


def extract_indicators(text):

    indicators = []

    for value in set(
        EMAIL_REGEX.findall(text)
    ):

        indicators.append(
            (
                "email",
                value,
                redact(value, "email")
            )
        )

    for value in set(
        URL_REGEX.findall(text)
    ):

        indicators.append(
            (
                "url",
                value,
                redact(value)
            )
        )

    for value in set(
        IP_REGEX.findall(text)
    ):

        indicators.append(
            (
                "ip",
                value,
                value
            )
        )

    for regex, kind in [
        (SHA256_REGEX, "sha256"),
        (SHA1_REGEX, "sha1"),
        (MD5_REGEX, "md5"),
        (CVE_REGEX, "cve"),
        (CRYPTO_REGEX, "crypto")
    ]:

        for value in set(
            regex.findall(text)
        ):

            indicators.append(
                (
                    kind,
                    value,
                    value
                )
            )

    for value in set(
        PHONE_REGEX.findall(text)
    ):

        digits = re.sub(
            r"\D",
            "",
            value
        )

        if 8 <= len(digits) <= 15:

            indicators.append(
                (
                    "phone",
                    value,
                    redact(value, "phone")
                )
            )

    return indicators


def classify_signals(text):

    text_lower = text.lower()

    result = {}

    for category, terms in SIGNAL_TERMS.items():

        hits = [
            term
            for term in terms
            if term in text_lower
        ]

        if hits:

            result[category] = {
                "score": min(
                    1.0,
                    0.25 + len(hits) * 0.12
                ),
                "matched_terms": hits
            }

    return result


# ============================================================
# SEARCH ENGINE
# ============================================================

class DiscoveryEngine:

    def queries(
        self,
        target_type,
        target
    ):

        target = target.strip()

        if target_type == "domain":

            return [

                f'"{target}" security',

                f'"{target}" breach',

                f'"{target}" leaked data',

                f'"{target}" ransomware',

                f'"{target}" vulnerability',

                f'"{target}" CVE',

                f'"{target}" exposed database',

                f'site:github.com "{target}"',

                f'site:gitlab.com "{target}"',

                f'"{target}" filetype:pdf',

                f'"{target}" filetype:json',

                f'"{target}" filetype:yaml'
            ]

        if target_type == "organization":

            return [

                f'"{target}" cyber attack',

                f'"{target}" data breach',

                f'"{target}" ransomware',

                f'"{target}" security incident',

                f'"{target}" vulnerability',

                f'"{target}" leaked data',

                f'site:github.com "{target}"'
            ]

        if target_type in (
            "email",
            "phone",
            "username",
            "name",
            "dob"
        ):

            return [

                f'"{target}" breach',

                f'"{target}" leak',

                f'"{target}" fraud',

                f'"{target}" scam',

                f'"{target}" security incident'
            ]

        if target_type == "ip":

            return [

                f'"{target}" abuse',

                f'"{target}" malware',

                f'"{target}" CVE',

                f'"{target}" threat intelligence'
            ]

        return [
            f'"{target}" cybersecurity'
        ]

    def search(
        self,
        query,
        max_results=10
    ):

        if DDGS is None:

            return []

        results = []

        try:

            with DDGS() as ddgs:

                for item in ddgs.text(
                    query,
                    max_results=max_results
                ):

                    url = (
                        item.get("href")
                        or item.get("url")
                        or ""
                    )

                    results.append({

                        "title":
                            item.get(
                                "title",
                                ""
                            ),

                        "url":
                            url,

                        "snippet":
                            item.get(
                                "body",
                                ""
                            ),

                        "domain":
                            urlparse(url).netloc,

                        "query":
                            query
                    })

        except Exception:
            return []

        return results


DISCOVERY = DiscoveryEngine()


# ============================================================
# EMBEDDINGS
# ============================================================

@st.cache_resource(
    show_spinner=False
)
def load_encoder():

    if SentenceTransformer is None:
        return None

    return SentenceTransformer(
        "all-MiniLM-L6-v2",
        device="cpu"
    )


@st.cache_resource(
    show_spinner=False
)
def load_ner():

    if pipeline is None:
        return None

    gpu = -1

    if (
        torch is not None
        and torch.cuda.is_available()
    ):
        gpu = 0

    return pipeline(
        "ner",
        model="dslim/bert-base-NER",
        aggregation_strategy="simple",
        device=gpu
    )


def encode_text(text):

    encoder = load_encoder()

    if encoder is None:
        return None

    return encoder.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    ).astype("float32")


# ============================================================
# FAISS
# ============================================================

class VectorStore:

    def __init__(self):

        self.index = None
        self.metadata = []

        self.load()

    def load(self):

        if faiss is None:
            return

        if FAISS_FILE.exists():

            try:

                self.index = faiss.read_index(
                    str(FAISS_FILE)
                )

                if FAISS_META.exists():

                    self.metadata = json.loads(
                        FAISS_META.read_text()
                    )

            except Exception:

                self.index = None
                self.metadata = []

    def add(
        self,
        text,
        metadata
    ):

        vector = encode_text(text)

        if vector is None:
            return False

        if self.index is None:

            self.index = faiss.IndexFlatIP(
                EMBEDDING_DIM
            )

        self.index.add(vector)

        self.metadata.append(
            metadata
        )

        faiss.write_index(
            self.index,
            str(FAISS_FILE)
        )

        FAISS_META.write_text(
            json.dumps(
                self.metadata,
                indent=2,
                default=str
            )
        )

        return True

    def search(
        self,
        query,
        top_k=10
    ):

        if (
            self.index is None
            or self.index.ntotal == 0
        ):
            return []

        vector = encode_text(query)

        if vector is None:
            return []

        k = min(
            top_k,
            self.index.ntotal
        )

        scores, indices = (
            self.index.search(
                vector,
                k
            )
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if (
                index >= 0
                and index < len(self.metadata)
            ):

                results.append({

                    "similarity":
                        float(score),

                    **self.metadata[index]
                })

        return results


VECTORS = VectorStore()


# ============================================================
# KNOWLEDGE GRAPH
# ============================================================

class KnowledgeGraph:

    def __init__(self):

        self.graph = nx.MultiDiGraph()

    def clear(self):

        self.graph.clear()

    def add_finding(
        self,
        finding
    ):

        source = (
            finding.get("source")
            or "unknown"
        )

        category = (
            finding.get("category")
            or "unknown"
        )

        indicator = (
            finding.get(
                "redacted_indicator"
            )
        )

        self.graph.add_node(
            source,
            node_type="source"
        )

        self.graph.add_node(
            category,
            node_type="category"
        )

        self.graph.add_edge(
            source,
            category,
            relation="REPORTS",
            confidence=finding.get(
                "confidence",
                0.5
            )
        )

        if indicator:

            self.graph.add_node(
                indicator,
                node_type="indicator"
            )

            self.graph.add_edge(
                category,
                indicator,
                relation="CONTAINS",
                confidence=finding.get(
                    "confidence",
                    0.5
                )
            )

    def centrality(self):

        if len(self.graph) == 0:
            return []

        graph = (
            self.graph
            .to_undirected()
        )

        if len(graph) > 1:

            pagerank = nx.pagerank(
                graph
            )

        else:

            pagerank = {
                node: 1.0
                for node in graph.nodes
            }

        results = []

        for node in graph.nodes:

            results.append({

                "node":
                    node,

                "type":
                    self.graph.nodes[
                        node
                    ].get(
                        "node_type"
                    ),

                "score":
                    round(
                        float(
                            pagerank.get(
                                node,
                                0
                            )
                        ),
                        6
                    ),

                "degree":
                    graph.degree(node)
            })

        return sorted(
            results,
            key=lambda x: x["score"],
            reverse=True
        )


GRAPH = KnowledgeGraph()


# ============================================================
# FILE / EVIDENCE PROCESSING
# ============================================================

def sha256(data):

    return hashlib.sha256(
        data
    ).hexdigest()


def extract_exif(image):

    output = {}

    try:

        data = image.getexif()

        for key, value in data.items():

            name = ExifTags.TAGS.get(
                key,
                str(key)
            )

            output[name] = str(value)

    except Exception:
        pass

    return output


def perform_ocr(image):

    if (
        pytesseract is None
        or image is None
    ):
        return ""

    try:

        enhanced = (
            ImageEnhance
            .Contrast(
                image.convert("RGB")
            )
            .enhance(2.0)
        )

        first = pytesseract.image_to_string(
            enhanced
        )

        second = pytesseract.image_to_string(
            image.convert("RGB")
        )

        return (
            first
            if len(first) >= len(second)
            else second
        )

    except Exception:

        return ""


def process_uploaded_file(
    uploaded,
    case_id
):

    raw = uploaded.getvalue()

    digest = sha256(raw)

    filename = Path(
        uploaded.name
    ).name

    stored = (
        EVIDENCE_DIR
        /
        f"{digest[:16]}_{filename}"
    )

    stored.write_bytes(raw)

    mime = (
        uploaded.type
        or "application/octet-stream"
    )

    evidence_id = DB.add_evidence(
        case_id,
        filename,
        stored,
        digest,
        mime
    )

    extension = (
        Path(filename)
        .suffix
        .lower()
    )

    text = ""
    exif = {}

    if extension in {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".log"
    }:

        text = raw.decode(
            "utf-8",
            errors="ignore"
        )

    elif extension in {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".webp"
    }:

        if Image:

            try:

                image = Image.open(
                    io.BytesIO(raw)
                )

                exif = extract_exif(
                    image
                )

                text = perform_ocr(
                    image
                )

            except Exception:
                pass

    elif extension == ".pdf":

        try:

            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(raw)
            )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception:
            text = ""

    return {

        "evidence_id":
            evidence_id,

        "filename":
            filename,

        "sha256":
            digest,

        "text":
            text,

        "exif":
            exif,

        "path":
            str(stored)
    }


# ============================================================
# REPORT GENERATOR
# ============================================================

def create_report(case_id):

    cases = DB.get_cases()

    case = next(
        (
            item
            for item in cases
            if item[0] == case_id
        ),
        None
    )

    targets = DB.get_targets(
        case_id
    )

    findings = DB.get_findings(
        case_id
    )

    lines = [

        "# SPECTER CYBER REPORT",

        "",

        f"Case: `{case_id}`",

        f"Generated: `{datetime.utcnow().isoformat()} UTC`",

        "",

        "## Targets",

    ]

    for target in targets:

        lines.append(
            f"- `{target[1]}` — "
            f"{target[2]}"
        )

    lines.extend([
        "",
        "## Findings",
        ""
    ])

    for finding in findings:

        lines.extend([

            f"### {finding[2]}",

            f"- Category: `{finding[1]}`",

            f"- Source: `{finding[3]}`",

            f"- URL: {finding[4]}",

            f"- Indicator: `{finding[5]}`",

            f"- Confidence: "
            f"{float(finding[6]):.0%}",

            f"- First seen: {finding[7]}",

            f"- Last seen: {finding[8]}",

            ""
        ])

    return "\n".join(lines)


# ============================================================
# SESSION STATE
# ============================================================

if "active_case" not in st.session_state:

    st.session_state.active_case = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div style="text-align:center">

    <h1>👁️ SPECTER CYBER</h1>

    <p>
    Multimodal OSINT • Threat Intelligence •
    PII • Exposure • Investigation
    </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CASE MANAGEMENT (main page — no sidebar)
# ============================================================

st.markdown("### 🗂️ Case Management")

cases = DB.get_cases()

col_a, col_b = st.columns([1, 1])

with col_a:
    st.markdown("**Select existing case**")
    if cases:
        case_options = {
            f"{x[1]} [{x[0]}]": x[0]
            for x in cases
        }
        selected_case = st.selectbox(
            "Active Case",
            list(case_options),
            label_visibility="collapsed"
        )
        st.session_state.active_case = case_options[selected_case]
    else:
        st.info("No cases yet. Create one on the right →")

with col_b:
    st.markdown("**➕ Create New Case**")
    new_name = st.text_input(
        "Case Name",
        placeholder="e.g. Subject Investigation 01",
        label_visibility="collapsed"
    )
    new_description = st.text_input(
        "Description (optional)",
        placeholder="Short notes about this case",
        label_visibility="collapsed"
    )
    if st.button("Create Case", type="primary", use_container_width=True):
        if new_name.strip():
            st.session_state.active_case = DB.create_case(
                new_name.strip(),
                new_description.strip()
            )
            st.success("Case created.")
            st.rerun()
        else:
            st.warning("Please enter a Case Name.")

if st.session_state.active_case:
    active = st.session_state.active_case
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Case", active)
    m2.metric("Targets", len(DB.get_targets(active)))
    m3.metric("Findings", len(DB.get_findings(active)))
    st.divider()
else:
    st.warning(
        "Create or select a Case above to begin. "
        "After that you will see Targets, Discovery, Evidence and other tabs."
    )
    st.stop()


CASE_ID = (
    st.session_state.active_case
)


# ============================================================
# MAIN TABS
# ============================================================

tabs = st.tabs(
    [
        "🎯 Targets",
        "🔎 Discovery",
        "📥 Evidence",
        "🧠 Intelligence",
        "🕸️ Network",
        "📊 Report"
    ]
)


# ============================================================
# TARGET TAB
# ============================================================

with tabs[0]:

    st.subheader(
        "🎯 Add Investigation Targets"
    )

    st.markdown(
        "Add people, accounts, phone numbers, emails, domains, or other identifiers to investigate."
    )

    left, right = st.columns(
        [1, 2]
    )

    with left:

        target_type = st.selectbox(
            "What are you adding?",
            [
                "name",
                "username",
                "phone",
                "email",
                "dob",
                "domain",
                "organization",
                "ip",
                "url",
                "other"
            ],
            format_func=lambda x: {
                "name": "Full Name",
                "username": "Username / Handle",
                "phone": "Phone Number",
                "email": "Email Address",
                "dob": "Date of Birth (DOB)",
                "domain": "Domain / Website",
                "organization": "Organization / Company",
                "ip": "IP Address",
                "url": "URL / Link",
                "other": "Other"
            }.get(x, x)
        )

        placeholders = {
            "name": "e.g. John Michael Smith",
            "username": "e.g. johnsmith99",
            "phone": "e.g. +1 555 123 4567",
            "email": "e.g. john@example.com",
            "dob": "e.g. 1990-05-15 or 15 May 1990",
            "domain": "e.g. example.com",
            "organization": "e.g. Acme Corp",
            "ip": "e.g. 192.168.1.1",
            "url": "e.g. https://...",
            "other": "Enter value"
        }

        target_value = st.text_input(
            "Value",
            placeholder=placeholders.get(target_type, "Enter value")
        )

        target_label = st.text_input(
            "Optional Label / Note",
            placeholder="e.g. Primary subject, Work email, etc."
        )

        if st.button(
            "➕ Add Target",
            type="primary",
            use_container_width=True
        ):

            if target_value.strip():

                DB.add_target(
                    CASE_ID,
                    target_type,
                    target_value.strip(),
                    target_label.strip()
                )

                DB.add_event(
                    CASE_ID,
                    "target_added",
                    {
                        "type":
                            target_type,

                        "value":
                            redact(
                                target_value
                            )
                    }
                )

                st.success(
                    "Target added successfully."
                )

                st.rerun()
            else:
                st.warning("Please enter a value.")

    with right:

        st.markdown("**Current Targets**")

        targets = DB.get_targets(
            CASE_ID
        )

        if targets:

            st.dataframe(

                pd.DataFrame(

                    targets,

                    columns=[
                        "Target ID",
                        "Type",
                        "Value",
                        "Label",
                        "Created"
                    ]

                ),

                use_container_width=True
            )

        else:

            st.info(
                "No targets."
            )


# ============================================================
# DISCOVERY TAB
# ============================================================

with tabs[1]:

    st.subheader(
        "🔎 Public-Source Discovery / Search"
    )

    st.markdown(
        "Select a target and click **Run Discovery** to search public sources for related information."
    )

    targets = DB.get_targets(
        CASE_ID
    )

    if not targets:

        st.warning(
            "Add at least one target in the Targets tab first."
        )

    else:

        target_options = {
            f"{x[1]}: {x[2]}":
                x

            for x in targets
        }

        selected = st.selectbox(
            "Target",
            list(
                target_options
            )
        )

        target = (
            target_options[
                selected
            ]
        )

        queries = DISCOVERY.queries(
            target[1],
            target[2]
        )

        with st.expander(
            "Generated Search Queries"
        ):

            for query in queries:

                st.code(
                    query
                )

        max_results = st.slider(
            "Results per query",
            3,
            25,
            8
        )

        if st.button(
            "🚀 Run Discovery",
            type="primary"
        ):

            all_results = []

            progress = st.progress(
                0
            )

            for index, query in enumerate(
                queries
            ):

                results = DISCOVERY.search(
                    query,
                    max_results
                )

                all_results.extend(
                    results
                )

                progress.progress(
                    (index + 1)
                    /
                    len(queries)
                )

            unique = {}

            for result in all_results:

                url = result.get(
                    "url"
                )

                if url:

                    unique[url] = result

            results = list(
                unique.values()
            )

            if not results:

                st.warning(
                    "No public results returned."
                )

            else:

                for result in results:

                    text = (
                        result.get(
                            "title",
                            ""
                        )
                        + " "
                        +
                        result.get(
                            "snippet",
                            ""
                        )
                    )

                    signals = (
                        classify_signals(
                            text
                        )
                    )

                    if signals:

                        category = max(
                            signals,
                            key=lambda x:
                                signals[x][
                                    "score"
                                ]
                        )

                        confidence = (
                            signals[
                                category
                            ][
                                "score"
                            ]
                        )

                    else:

                        category = (
                            "general_osint"
                        )

                        confidence = 0.35

                    indicators = (
                        extract_indicators(
                            text
                        )
                    )

                    for (
                        kind,
                        indicator,
                        redacted_value
                    ) in indicators:

                        DB.add_finding({

                            "case_id":
                                CASE_ID,

                            "target_id":
                                target[0],

                            "category":
                                f"{category}:{kind}",

                            "title":
                                result.get(
                                    "title",
                                    "Finding"
                                ),

                            "source":
                                result.get(
                                    "domain",
                                    "search"
                                ),

                            "url":
                                result.get(
                                    "url",
                                    ""
                                ),

                            "indicator":
                                indicator,

                            "redacted_indicator":
                                redacted_value,

                            "confidence":
                                confidence,

                            "sha256":
                                hashlib.sha256(
                                    (
                                        result.get(
                                            "url",
                                            ""
                                        )
                                        + text
                                    ).encode()
                                ).hexdigest(),

                            "notes":
                                json.dumps(
                                    signals
                                )
                        })

                    VECTORS.add(
                        text,
                        {
                            "case_id":
                                CASE_ID,

                            "title":
                                result.get(
                                    "title"
                                ),

                            "url":
                                result.get(
                                    "url"
                                ),

                            "source":
                                result.get(
                                    "domain"
                                )
                        }
                    )

                DB.add_event(
                    CASE_ID,
                    "discovery_completed",
                    {
                        "results":
                            len(results)
                    }
                )

                st.success(
                    f"{len(results)} "
                    "unique results."
                )

                st.dataframe(

                    pd.DataFrame(
                        results
                    )[
                        [
                            "title",
                            "domain",
                            "url",
                            "snippet"
                        ]
                    ],

                    use_container_width=True
                )


# ============================================================
# EVIDENCE TAB
# ============================================================

with tabs[2]:

    st.subheader(
        "📥 Upload Evidence & Images"
    )

    st.markdown(
        "Upload images, PDFs, text files, logs or other authorized evidence. "
        "The system will extract text (OCR for images), indicators, and metadata."
    )

    files = st.file_uploader(

        "Choose files (images, PDF, txt, csv, json, log…)",

        type=[
            "txt",
            "md",
            "csv",
            "json",
            "log",
            "png",
            "jpg",
            "jpeg",
            "tiff",
            "webp",
            "pdf"
        ],

        accept_multiple_files=True
    )

    if files:

        for uploaded in files:

            with st.spinner(
                f"Processing {uploaded.name}..."
            ):

                artifact = (
                    process_uploaded_file(
                        uploaded,
                        CASE_ID
                    )
                )

                text = artifact[
                    "text"
                ]

                indicators = (
                    extract_indicators(
                        text
                    )
                )

                signals = (
                    classify_signals(
                        text
                    )
                )

                ner_results = []

                ner = load_ner()

                if (
                    ner is not None
                    and text.strip()
                ):

                    try:

                        ner_results = ner(
                            text[:15000]
                        )

                    except Exception:

                        ner_results = []

                for (
                    kind,
                    indicator,
                    redacted_value
                ) in indicators:

                    DB.add_finding({

                        "case_id":
                            CASE_ID,

                        "category":
                            f"artifact:{kind}",

                        "title":
                            f"Indicator from "
                            f"{uploaded.name}",

                        "source":
                            "local_evidence",

                        "url":
                            "",

                        "indicator":
                            indicator,

                        "redacted_indicator":
                            redacted_value,

                        "confidence":
                            0.90,

                        "sha256":
                            artifact[
                                "sha256"
                            ],

                        "notes":
                            "Extracted from "
                            "authorized evidence."
                    })

                if text.strip():

                    VECTORS.add(
                        text[:30000],
                        {
                            "case_id":
                                CASE_ID,

                            "source":
                                "local_evidence",

                            "title":
                                uploaded.name,

                            "evidence_id":
                                artifact[
                                    "evidence_id"
                                ]
                        }
                    )

                DB.add_event(
                    CASE_ID,
                    "artifact_ingested",
                    {
                        "filename":
                            uploaded.name,

                        "sha256":
                            artifact[
                                "sha256"
                            ],

                        "indicators":
                            len(indicators)
                    }
                )

                st.success(
                    f"{uploaded.name} processed."
                )

                c1, c2, c3 = st.columns(
                    3
                )

                c1.metric(
                    "Indicators",
                    len(indicators)
                )

                c2.metric(
                    "NER Entities",
                    len(ner_results)
                )

                c3.metric(
                    "Text Characters",
                    len(text)
                )

                st.code(
                    artifact[
                        "sha256"
                    ],
                    language="text"
                )

                if signals:

                    with st.expander(
                        "Detected Intelligence Signals"
                    ):

                        st.json(
                            signals
                        )

                if artifact["exif"]:

                    with st.expander(
                        "EXIF Metadata"
                    ):

                        st.json(
                            artifact[
                                "exif"
                            ]
                        )

                if ner_results:

                    with st.expander(
                        "Named Entities"
                    ):

                        st.dataframe(
                            pd.DataFrame(
                                ner_results
                            ),
                            use_container_width=True
                        )

                if text:

                    with st.expander(
                        "OCR / Extracted Text"
                    ):

                        st.text_area(
                            "Text",
                            text[:15000],
                            height=300,
                            key=(
                                "text_"
                                +
                                artifact[
                                    "evidence_id"
                                ]
                            )
                        )


# ============================================================
# INTELLIGENCE TAB
# ============================================================

with tabs[3]:

    st.subheader(
        "🧠 Intelligence Analysis"
    )

    subtabs = st.tabs(
        [
            "Findings",
            "Semantic Search",
            "Indicators",
            "Signals"
        ]
    )

    with subtabs[0]:

        findings = DB.get_findings(
            CASE_ID
        )

        if findings:

            dataframe = pd.DataFrame(

                findings,

                columns=[
                    "Finding ID",
                    "Category",
                    "Title",
                    "Source",
                    "URL",
                    "Indicator",
                    "Confidence",
                    "First Seen",
                    "Last Seen",
                    "Notes"
                ]
            )

            st.dataframe(
                dataframe,
                use_container_width=True
            )

        else:

            st.info(
                "No findings."
            )

    with subtabs[1]:

        query = st.text_input(
            "Semantic Search",
            placeholder=(
                "Search the investigation "
                "semantically..."
            )
        )

        if query:

            results = VECTORS.search(
                query,
                top_k=10
            )

            if results:

                st.dataframe(
                    pd.DataFrame(
                        results
                    ),
                    use_container_width=True
                )

            else:

                st.info(
                    "No semantic matches."
                )

    with subtabs[2]:

        findings = DB.get_findings(
            CASE_ID
        )

        if findings:

            dataframe = pd.DataFrame(

                findings,

                columns=[
                    "Finding ID",
                    "Category",
                    "Title",
                    "Source",
                    "URL",
                    "Indicator",
                    "Confidence",
                    "First Seen",
                    "Last Seen",
                    "Notes"
                ]
            )

            counts = (
                dataframe[
                    "Category"
                ]
                .value_counts()
            )

            st.bar_chart(
                counts
            )

    with subtabs[3]:

        findings = DB.get_findings(
            CASE_ID
        )

        if findings:

            dataframe = pd.DataFrame(

                findings,

                columns=[
                    "Finding ID",
                    "Category",
                    "Title",
                    "Source",
                    "URL",
                    "Indicator",
                    "Confidence",
                    "First Seen",
                    "Last Seen",
                    "Notes"
                ]
            )

            dataframe[
                "Confidence"
            ] = pd.to_numeric(
                dataframe[
                    "Confidence"
                ],
                errors="coerce"
            )

            high = int(
                (
                    dataframe[
                        "Confidence"
                    ] >= 0.8
                ).sum()
            )

            medium = int(
                (
                    (
                        dataframe[
                            "Confidence"
                        ] >= 0.5
                    )
                    &
                    (
                        dataframe[
                            "Confidence"
                        ] < 0.8
                    )
                ).sum()
            )

            low = int(
                (
                    dataframe[
                        "Confidence"
                    ] < 0.5
                ).sum()
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "High",
                high
            )

            c2.metric(
                "Medium",
                medium
            )

            c3.metric(
                "Low",
                low

            )


# ============================================================
# NETWORK TAB
# ============================================================

with tabs[4]:

    st.subheader(
        "🕸️ Investigation Knowledge Graph"
    )

    GRAPH.clear()

    findings = DB.get_findings(
        CASE_ID
    )

    for finding in findings:

        GRAPH.add_finding({

            "category":
                finding[1],

            "source":
                finding[3],

            "redacted_indicator":
                finding[5],

            "confidence":
                finding[6]
        })

    if len(GRAPH.graph) < 2:

        st.info(
            "More findings are required "
            "to construct the graph."
        )

    else:

        centrality = (
            GRAPH.centrality()
        )

        if centrality:

            st.dataframe(

                pd.DataFrame(
                    centrality[:25]
                ),

                use_container_width=True
            )

        graph = (
            GRAPH.graph
            .to_undirected()
        )

        positions = nx.spring_layout(
            graph,
            seed=42,
            k=1.5
        )

        edge_x = []
        edge_y = []

        for source, target in (
            graph.edges()
        ):

            x0, y0 = positions[
                source
            ]

            x1, y1 = positions[
                target
            ]

            edge_x += [
                x0,
                x1,
                None
            ]

            edge_y += [
                y0,
                y1,
                None
            ]

        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(
                    width=1,
                    color="#45515a"
                ),
                hoverinfo="none"
            )
        )

        node_x = []
        node_y = []
        labels = []
        colors = []

        for node in graph.nodes():

            x, y = positions[
                node
            ]

            node_x.append(x)
            node_y.append(y)

            node_type = (
                GRAPH.graph.nodes[
                    node
                ].get(
                    "node_type",
                    "unknown"
                )
            )

            labels.append(
                f"{node}<br>"
                f"Type: {node_type}"
            )

            if node_type == "indicator":

                colors.append(
                    "#00ff88"
                )

            elif node_type == "source":

                colors.append(
                    "#4ecdc4"
                )

            else:

                colors.append(
                    "#ff6b6b"
                )

        figure.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                text=labels,
                textposition="top center",
                marker=dict(
                    size=18,
                    color=colors,
                    line=dict(
                        width=1,
                        color="white"
                    )
                )
            )
        )

        figure.update_layout(

            height=650,

            paper_bgcolor="#080b0d",

            plot_bgcolor="#080b0d",

            font=dict(
                color="white"
            ),

            showlegend=False,

            xaxis=dict(
                visible=False
            ),

            yaxis=dict(
                visible=False
            )
        )

        st.plotly_chart(
            figure,
            use_container_width=True
        )


# ============================================================
# REPORT TAB
# ============================================================

with tabs[5]:

    st.subheader(
        "📊 Investigation Report"
    )

    report = create_report(
        CASE_ID
    )

    st.download_button(

        "⬇️ Download Markdown Report",

        report,

        file_name=(
            f"{CASE_ID}.md"
        ),

        mime="text/markdown"
    )

    st.code(
        report[:15000],
        language="markdown"
    )

    st.warning(
        "Full indicators (including emails, phones, and other "
        "extracted values) are stored for authorized investigations. "
        "Handle case data, evidence, and reports according to your "
        "legal / organizational authorization and data-protection rules. "
        "A redacted copy is still retained in the database for optional display."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center;color:#444;font-size:11px">

    SPECTER CYBER v2 |
    Authorized Investigation Platform |
    Local SQLite + FAISS

    </div>
    """,
    unsafe_allow_html=True
)