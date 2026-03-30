"""
Tamil Reading Assistant — Clean Word-Click Meaning Lookup
"""

import streamlit as st
import json, re, io
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="தமிழ் வாசகர்",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+Tamil:wght@300;400;500;600&family=Playfair+Display:wght@700;800&display=swap');

:root {
  --bg:        #faf7f2;
  --paper:     #fffdf8;
  --border:    #e2d9c8;
  --gold:      #b8860b;
  --gold-lt:   #f0e6c8;
  --ink:       #1a1208;
  --ink2:      #4a3828;
  --red:       #8b1a1a;
  --teal:      #0d4f47;
  --teal-lt:   #e6f4f2;
  --tag-g:     #1a5c1a;
  --tag-b:     #1a3f7a;
  --tag-p:     #4a1a7a;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
  background: var(--bg);
  font-family: 'Lora', Georgia, serif;
  color: var(--ink);
}

/* hide streamlit chrome */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── TOP BAR ── */
.topbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  background: var(--ink);
  border-bottom: 3px solid var(--gold);
  position: sticky; top: 0; z-index: 100;
}
.topbar-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem;
  color: var(--gold);
  letter-spacing: .04em;
}
.topbar-tamil {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 1rem;
  color: #c8b08a;
}

/* ── LAYOUT ── */
.app-shell {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 0;
  min-height: calc(100vh - 64px);
}

/* ── LEFT: READER ── */
.reader-panel {
  padding: 2rem 2.5rem;
  border-right: 1px solid var(--border);
  background: var(--paper);
}

.upload-zone {
  border: 2px dashed var(--border);
  border-radius: 8px;
  padding: 3rem 2rem;
  text-align: center;
  background: var(--gold-lt);
  margin-bottom: 1.5rem;
}
.upload-icon { font-size: 2.5rem; margin-bottom: .5rem; }
.upload-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem;
  color: var(--red);
  margin-bottom: .3rem;
}
.upload-sub {
  font-style: italic;
  color: var(--ink2);
  font-size: .95rem;
}

/* doc title */
.doc-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem;
  color: var(--ink2);
  padding: .5rem .8rem;
  background: var(--gold-lt);
  border-left: 4px solid var(--gold);
  border-radius: 0 4px 4px 0;
  margin-bottom: 1.5rem;
}

/* ── READING CONTENT ── */
.doc-content {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 1.1rem;
  line-height: 2.1;
  color: var(--ink);
}
.doc-para {
  margin-bottom: 1.1rem;
  text-align: justify;
}
.doc-heading {
  font-family: 'Playfair Display', serif;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--red);
  margin: 1.5rem 0 .6rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: .3rem;
}
.doc-list-item {
  padding: .2rem 0 .2rem 1.2rem;
  position: relative;
}
.doc-list-item::before {
  content: '•';
  position: absolute; left: 0;
  color: var(--gold);
}

/* ── TAMIL WORD CHIP ── */
.tw {
  display: inline;
  cursor: pointer;
  border-radius: 3px;
  padding: 1px 3px;
  margin: 0 1px;
  transition: background .15s, color .15s;
  border-bottom: 1.5px dotted var(--gold);
  color: var(--ink);
}
.tw:hover {
  background: var(--gold-lt);
  border-bottom-color: var(--red);
  color: var(--red);
}
.tw.active {
  background: #ffeaa0;
  border-bottom: 2px solid var(--gold);
  color: var(--red);
  font-weight: 500;
}

/* ── RIGHT: MEANING PANEL ── */
.meaning-panel {
  padding: 1.5rem 1.4rem;
  background: var(--bg);
  position: sticky;
  top: 64px;
  height: calc(100vh - 64px);
  overflow-y: auto;
}

.panel-idle {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--ink2);
}
.panel-idle-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.panel-idle-text {
  font-style: italic;
  font-size: 1rem;
  line-height: 1.6;
}

/* ── MEANING CARD ── */
.mcard {
  background: var(--paper);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
}
.mcard-head {
  background: var(--ink);
  padding: 1rem 1.2rem;
  text-align: center;
}
.mcard-word {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 2rem;
  font-weight: 600;
  color: #fff;
  display: block;
}
.mcard-body {
  padding: 1.2rem;
}
.tier-pill {
  display: inline-block;
  font-size: .7rem;
  font-family: 'Lora', serif;
  letter-spacing: .05em;
  padding: 2px 8px;
  border-radius: 20px;
  margin-bottom: .9rem;
  font-style: italic;
}
.t2 { background: #d4edda; color: #155724; }
.t3 { background: #cce5ff; color: #004085; }
.t4 { background: #e2d9f3; color: #432874; }
.tn { background: #f8d7da; color: #721c24; }

.mcard-en {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--red);
  margin-bottom: .5rem;
}
.mcard-ta {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 1rem;
  color: var(--teal);
  background: var(--teal-lt);
  padding: .4rem .7rem;
  border-radius: 4px;
  margin-bottom: .6rem;
}
.mcard-def {
  font-size: .92rem;
  color: var(--ink2);
  font-style: italic;
  line-height: 1.55;
  border-left: 3px solid var(--border);
  padding-left: .7rem;
  margin-bottom: .6rem;
}
.mcard-ex {
  font-size: .85rem;
  color: #888;
  padding-top: .5rem;
  border-top: 1px dashed var(--border);
}

/* ── HISTORY ── */
.hist-label {
  font-size: .75rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--ink2);
  margin: 1.2rem 0 .5rem;
  font-family: 'Lora', serif;
}
.hist-item {
  display: inline-block;
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: .9rem;
  padding: 3px 10px;
  margin: 2px;
  background: var(--gold-lt);
  border: 1px solid var(--border);
  border-radius: 3px;
  cursor: pointer;
  color: var(--ink2);
}
.hist-item:hover { background: #f0e6c8; color: var(--red); }

/* ── STATS BAR ── */
.stats-bar {
  display: flex;
  gap: .8rem;
  flex-wrap: wrap;
  padding: .7rem 1rem;
  background: var(--gold-lt);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 1.5rem;
}
.stat { text-align: center; flex: 1; min-width: 55px; }
.stat-n {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem;
  color: var(--red);
  display: block;
}
.stat-l {
  font-size: .65rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--ink2);
}

/* ── SIDEBAR word input ── */
.stTextInput > div > div > input {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 1.05rem;
  border: 1.5px solid var(--border);
  border-radius: 4px;
  background: var(--paper);
}
.stButton > button {
  background: var(--red);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-family: 'Lora', serif;
  font-size: .9rem;
  letter-spacing: .04em;
  padding: .45rem 1.2rem;
  width: 100%;
  cursor: pointer;
}
.stButton > button:hover { background: #a02020; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# TAMIL HELPERS
# ══════════════════════════════════════════════════════════════════════
_TAMIL_RE   = re.compile(r'[\u0B80-\u0BFF]+')
_PUNC_STRIP = re.compile(r'^[^\u0B80-\u0BFF]+|[^\u0B80-\u0BFF]+$')

def is_tamil_char(ch): return '\u0B80' <= ch <= '\u0BFF'

def clean_word(w):
    w = _PUNC_STRIP.sub('', w).strip()
    w = re.sub(r'[\u0B82\u0B83]+$', '', w)
    return w

def is_tamil_word(w):
    cw = clean_word(w)
    return len(cw) >= 2 and bool(_TAMIL_RE.search(cw))

# ══════════════════════════════════════════════════════════════════════
# LOAD DICTIONARY
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_dict():
    p = Path(__file__).parent / "tamil.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}

TDICT = load_dict()

# ══════════════════════════════════════════════════════════════════════
# DOCUMENT EXTRACTION  — returns list of {"type": ..., "text": ...}
# ══════════════════════════════════════════════════════════════════════
def extract_docx(data: bytes) -> list:
    """Extract paragraphs from DOCX preserving structure."""
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document(io.BytesIO(data))
    blocks = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style else ""

        if "Heading" in style or para.runs and all(r.bold for r in para.runs if r.text.strip()):
            blocks.append({"type": "heading", "text": text})
        elif para.style and "List" in style:
            blocks.append({"type": "list", "text": text})
        else:
            blocks.append({"type": "para", "text": text})

    return blocks

def extract_pdf(data: bytes) -> list:
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    blocks = []
    for page in doc:
        txt = page.get_text()
        for line in txt.splitlines():
            line = line.strip()
            if line:
                blocks.append({"type": "para", "text": line})
    return blocks

def extract_txt(data: bytes) -> list:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            text = data.decode(enc)
            break
        except Exception:
            pass
    else:
        text = data.decode("utf-8", errors="replace")

    blocks = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            blocks.append({"type": "para", "text": line})
    return blocks

def extract_document(uploaded) -> list:
    data = uploaded.read()
    name = uploaded.name.lower()
    try:
        if name.endswith(".docx"):
            return extract_docx(data)
        elif name.endswith(".pdf"):
            return extract_pdf(data)
        else:
            return extract_txt(data)
    except Exception as e:
        st.error(f"Extraction error: {e}")
        return []

# ══════════════════════════════════════════════════════════════════════
# RENDER DOCUMENT — returns HTML with clickable Tamil words
# ══════════════════════════════════════════════════════════════════════
def tokenize_to_html(text: str) -> str:
    """Split text into tokens; wrap Tamil words in clickable spans."""
    tokens = text.split()
    parts = []
    for tok in tokens:
        core = clean_word(tok)
        if is_tamil_word(tok):
            safe = core.replace('"', '&quot;').replace("'", "&#39;")
            # preserve punctuation around the word
            pre  = tok[:len(tok) - len(tok.lstrip()) ]
            post = tok[len(tok.rstrip()):]
            parts.append(
                f'<span class="tw" '
                f'onclick="selectWord(\'{safe}\')" '
                f'data-word="{safe}">{tok}</span>'
            )
        else:
            parts.append(tok)
    return " ".join(parts)

def blocks_to_html(blocks: list) -> str:
    html_parts = []
    for b in blocks:
        t   = b["type"]
        txt = tokenize_to_html(b["text"])
        if t == "heading":
            html_parts.append(f'<div class="doc-heading">{txt}</div>')
        elif t == "list":
            html_parts.append(f'<div class="doc-para doc-list-item">{txt}</div>')
        else:
            html_parts.append(f'<div class="doc-para">{txt}</div>')
    return "\n".join(html_parts)

# ══════════════════════════════════════════════════════════════════════
# LOOKUP TIERS
# ══════════════════════════════════════════════════════════════════════
def tier2_json(word: str):
    w = clean_word(word)
    if w in TDICT:
        e = TDICT[w]
        return {"english": e.get("english",""), "tamil": e.get("tamil",""),
                "example": e.get("example",""), "tier": 2, "label": "Local Dictionary"}
    for n in (1, 2):
        s = w[:-n]
        if len(s) >= 2 and s in TDICT:
            e = TDICT[s]
            return {"english": e.get("english","") + " (stem)", "tamil": e.get("tamil",""),
                    "example": e.get("example",""), "tier": 2, "label": "Dictionary (stem)"}
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _dict_api(en_word: str) -> str:
    import requests
    SKIP = {"the","a","an","to","of","in","on","at","it","is","be","as"}
    words = [w for w in en_word.lower().split() if w not in SKIP]
    if not words:
        return ""
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{words[0]}",
            timeout=6
        )
        if r.status_code == 200:
            for entry in r.json():
                for m in entry.get("meanings", []):
                    for d in m.get("definitions", []):
                        txt = d.get("definition","")
                        # skip grammatical/article definitions
                        if txt and not txt.lower().startswith(("with a comp","used","(used")):
                            return txt[:220]
    except Exception:
        pass
    return ""

@st.cache_data(ttl=3600, show_spinner=False)
def tier3_chain(word: str):
    try:
        from deep_translator import GoogleTranslator
        en = GoogleTranslator(source="ta", target="en").translate(word)
        if not en:
            return None
        defn = _dict_api(en)
        ta_defn = ""
        if defn:
            try:
                ta_defn = GoogleTranslator(source="en", target="ta").translate(defn[:200])
            except Exception:
                pass
        return {
            "english": en,
            "tamil": ta_defn or "",
            "example": "",
            "definition": defn,
            "tier": 3,
            "label": "Translation",
        }
    except Exception:
        return None

@st.cache_resource(show_spinner=False)
def _ml_pipe():
    try:
        from transformers import pipeline
        return pipeline("translation", model="Helsinki-NLP/opus-mt-ta-en", device=-1)
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def tier4_ml(word: str):
    pipe = _ml_pipe()
    if not pipe:
        return None
    try:
        res = pipe(word, max_length=128)
        en  = res[0].get("translation_text","") if res else ""
        if not en:
            return None
        defn = _dict_api(en)
        return {"english": en, "tamil": "", "example": "", "definition": defn,
                "tier": 4, "label": "ML Model"}
    except Exception:
        return None

def lookup(word: str) -> dict:
    word = word.strip()
    if not word:
        return {"english":"","tamil":"","tier":0,"label":"Not found"}
    r = tier2_json(word)
    if r: return r
    r = tier3_chain(word)
    if r: return r
    r = tier4_ml(word)
    if r: return r
    return {"english":"Meaning not found","tamil":"பொருள் இல்லை","tier":0,"label":"Not found"}

# ══════════════════════════════════════════════════════════════════════
# RENDER MEANING CARD (HTML)
# ══════════════════════════════════════════════════════════════════════
def meaning_card_html(word: str, r: dict) -> str:
    tier  = r.get("tier", 0)
    tcls  = {2:"t2", 3:"t3", 4:"t4"}.get(tier, "tn")
    en    = r.get("english",    "—")
    ta    = r.get("tamil",      "")
    ex    = r.get("example",    "")
    defn  = r.get("definition", "")
    label = r.get("label",      "")

    ta_block = f'<div class="mcard-ta">🌿 {ta}</div>' if ta else ""
    defn_block = ""
    if defn and defn != en and len(defn) > 10:
        defn_block = f'<div class="mcard-def">{defn}</div>'
    ex_block = f'<div class="mcard-ex">📜 {ex}</div>' if ex else ""

    return f"""
    <div class="mcard">
      <div class="mcard-head">
        <span class="mcard-word">{word}</span>
      </div>
      <div class="mcard-body">
        <span class="tier-pill {tcls}">{label} · Tier {tier}</span>
        <div class="mcard-en">{en}</div>
        {ta_block}
        {defn_block}
        {ex_block}
      </div>
    </div>
    """

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in [("blocks", []), ("sel_word", ""), ("meaning", None),
             ("history", []), ("fname", ""), ("manual_word", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="topbar">
  <span class="topbar-title">Tamil Reading Assistant</span>
  <span class="topbar-tamil">தமிழ் வாசக உதவியாளர்</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# WORD SELECTION via URL query param  (Streamlit experimental)
# ══════════════════════════════════════════════════════════════════════
try:
    params = st.query_params
    clicked = params.get("w", "")
    if clicked and clicked != st.session_state.sel_word:
        st.session_state.sel_word = clicked
        with st.spinner(""):
            st.session_state.meaning = lookup(clicked)
        if clicked not in st.session_state.history:
            st.session_state.history.insert(0, clicked)
            st.session_state.history = st.session_state.history[:15]
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT — two columns
# ══════════════════════════════════════════════════════════════════════
col_reader, col_meaning = st.columns([6, 3], gap="small")

# ─────────────────────────────────────────────────────────────────────
# LEFT — READER
# ─────────────────────────────────────────────────────────────────────
with col_reader:
    # File uploader
    uploaded = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        key="uploader",
    )

    if uploaded:
        if uploaded.name != st.session_state.fname:
            with st.spinner("Reading document…"):
                blocks = extract_document(uploaded)
                st.session_state.blocks = blocks
                st.session_state.fname  = uploaded.name
                st.session_state.sel_word = ""
                st.session_state.meaning  = None

        blocks = st.session_state.blocks

        # Stats
        all_text = " ".join(b["text"] for b in blocks)
        tamil_words_all = [clean_word(t) for t in all_text.split() if is_tamil_word(t)]
        unique_tamil = list(dict.fromkeys(w for w in tamil_words_all if w))
        in_dict = sum(1 for w in unique_tamil if tier2_json(w))

        st.markdown(f"""
        <div class="stats-bar">
          <div class="stat"><span class="stat-n">{len(blocks)}</span><span class="stat-l">Sections</span></div>
          <div class="stat"><span class="stat-n">{len(all_text.split()):,}</span><span class="stat-l">Words</span></div>
          <div class="stat"><span class="stat-n">{len(unique_tamil):,}</span><span class="stat-l">Tamil words</span></div>
          <div class="stat"><span class="stat-n">{in_dict:,}</span><span class="stat-l">In dict</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Doc title
        fname_display = uploaded.name
        st.markdown(f'<div class="doc-title">📄 {fname_display}</div>', unsafe_allow_html=True)

        # Render document
        doc_html = blocks_to_html(blocks)

        # JavaScript for word selection — posts selected word to Streamlit
        js_code = """
        <script>
        function selectWord(word) {
            // highlight all instances
            document.querySelectorAll('.tw').forEach(el => {
                el.classList.remove('active');
                if (el.dataset.word === word) el.classList.add('active');
            });
            // update URL param to communicate with Streamlit
            const url = new URL(window.location.href);
            url.searchParams.set('w', word);
            window.history.replaceState({}, '', url);
            // trigger Streamlit rerun
            window.parent.postMessage({type:'streamlit:setComponentValue', value: word}, '*');
        }
        </script>
        """

        st.markdown(
            f'<div class="doc-content">{doc_html}</div>',
            unsafe_allow_html=True,
        )

        st.caption("💡 Tap any underlined Tamil word to see its meaning →")

    else:
        st.markdown("""
        <div class="upload-zone">
          <div class="upload-icon">📄</div>
          <div class="upload-title">Upload a Tamil Document</div>
          <div class="upload-sub">PDF · Word (DOCX) · Plain Text (TXT)</div>
          <br>
          <div style="color:#4a3828;font-style:italic;font-size:.95rem">
            "கற்றது கை மண் அளவு; கல்லாதது உலகளவு"<br>
            <span style="font-size:.82rem;color:#888">
            What one has learned is a handful of earth; what remains is the size of the world.
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# RIGHT — MEANING PANEL
# ─────────────────────────────────────────────────────────────────────
with col_meaning:
    # Manual search
    st.markdown("#### 🔍 Look up a word")
    manual = st.text_input(
        "Type Tamil word",
        placeholder="e.g. அன்பு",
        key="manual_input",
        label_visibility="collapsed",
    )
    if st.button("Find Meaning"):
        if manual.strip():
            st.session_state.sel_word = manual.strip()
            with st.spinner("Looking up…"):
                st.session_state.meaning = lookup(manual.strip())
            if manual.strip() not in st.session_state.history:
                st.session_state.history.insert(0, manual.strip())
                st.session_state.history = st.session_state.history[:15]

    st.markdown("---")

    # Selected from document
    if st.session_state.sel_word and st.session_state.meaning:
        word = st.session_state.sel_word
        r    = st.session_state.meaning

        # Auto-fetch if meaning missing
        if not r:
            with st.spinner("Fetching…"):
                r = lookup(word)
                st.session_state.meaning = r

        st.markdown(meaning_card_html(word, r), unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="panel-idle">
          <div class="panel-idle-icon">👆</div>
          <div class="panel-idle-text">
            Tap any Tamil word in the document<br>to see its meaning here.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # History
    if st.session_state.history:
        st.markdown('<div class="hist-label">Recently looked up</div>', unsafe_allow_html=True)
        hist_html = "".join(
            f'<span class="hist-item" onclick="void(0)">{w}</span>'
            for w in st.session_state.history
        )
        st.markdown(f'<div>{hist_html}</div>', unsafe_allow_html=True)

        # Selectbox for re-lookup from history
        pick = st.selectbox(
            "Re-look up:",
            ["—"] + st.session_state.history,
            key="hist_pick",
            label_visibility="collapsed",
        )
        if pick and pick != "—" and pick != st.session_state.sel_word:
            st.session_state.sel_word = pick
            with st.spinner(""):
                st.session_state.meaning = lookup(pick)
            st.rerun()

    # Dictionary size
    st.markdown(
        f'<div style="text-align:center;font-size:.75rem;color:#aaa;margin-top:1.5rem">'
        f'{len(TDICT):,} words in dictionary</div>',
        unsafe_allow_html=True
    )
