"""
Tamil Nadu Government — Tamil Reading & Language Assistant
Official Style: TN Govt Portal aesthetic with Tamil Nadu state symbols
"""

import streamlit as st
import json, re, io
from pathlib import Path

st.set_page_config(
    page_title="தமிழ்நாடு அரசு | Tamil Language Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════
# STYLES — Tamil Nadu Government Portal Design
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@300;400;500;600;700&family=Noto+Serif+Tamil:wght@400;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap');

:root {
  --tn-navy:    #003366;
  --tn-navy2:   #002244;
  --tn-blue:    #1a5276;
  --tn-saffron: #e07b00;
  --tn-saffron2:#c06800;
  --tn-green:   #1a6b2e;
  --tn-red:     #8b1a1a;
  --tn-gold:    #b8860b;
  --tn-white:   #ffffff;
  --tn-offwhite:#f5f7fa;
  --tn-gray1:   #e8ecf1;
  --tn-gray2:   #c5cdd8;
  --tn-gray3:   #7a8a99;
  --tn-text:    #1a2332;
  --tn-text2:   #3a4a5a;
  --tn-border:  #c5cdd8;
  --tn-success: #1a6b2e;
  --tn-warn:    #8b5000;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
  background: var(--tn-offwhite);
  font-family: 'Source Serif 4', 'Noto Sans Tamil', Georgia, serif;
  color: var(--tn-text);
}

#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; display: none !important; }

/* ══ TOP STRIP ══ */
.gov-topstrip {
  background: var(--tn-navy2);
  color: #ccdeff;
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: .76rem;
  padding: .28rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.gov-topstrip-links { display: flex; gap: 1rem; color: #88aadd; }

/* ══ MAIN HEADER ══ */
.gov-header {
  background: var(--tn-navy);
  border-bottom: 4px solid var(--tn-saffron);
  padding: 0;
  display: flex;
  align-items: stretch;
}
.gov-header-logo {
  background: var(--tn-navy2);
  padding: .7rem 1.4rem;
  display: flex;
  align-items: center;
  gap: .8rem;
  border-right: 2px solid var(--tn-saffron);
  flex-shrink: 0;
}
.gov-emblem {
  width: 58px; height: 58px;
  background: var(--tn-saffron);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.6rem;
  font-family: 'Noto Serif Tamil', serif;
  color: var(--tn-navy2);
  font-weight: 700;
  border: 2px solid #ffcc66;
}
.gov-logo-title {
  font-family: 'Noto Serif Tamil', serif;
  font-size: 1.1rem; font-weight: 700;
  color: white; letter-spacing: .02em;
}
.gov-logo-sub { font-size: .7rem; color: #aabbd4; letter-spacing: .04em; margin-top: .1rem; }
.gov-header-center { flex: 1; padding: .7rem 1.4rem; display: flex; align-items: center; }
.gov-app-title {
  font-family: 'Noto Serif Tamil', serif;
  font-size: 1.3rem; font-weight: 700; color: white; letter-spacing: .02em;
}
.gov-app-sub { font-size: .78rem; color: #aabbd4; margin-top: .15rem; font-family: 'Noto Sans Tamil', sans-serif; }
.gov-header-badges {
  padding: .7rem 1.2rem;
  display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: .3rem;
}
.gov-badge {
  display: inline-flex; align-items: center; gap: .3rem;
  font-size: .68rem; background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.2); color: #ccdeff;
  padding: .18rem .6rem; border-radius: 2px;
  font-family: 'Noto Sans Tamil', sans-serif;
}
.gov-badge-dot { width:6px;height:6px;border-radius:50%;background:#4ade80;display:inline-block; }

/* ══ NAV ══ */
.gov-nav {
  background: var(--tn-blue);
  border-bottom: 1px solid var(--tn-navy2);
  padding: 0 1.5rem;
  display: flex; gap: 0; align-items: center;
}
.gov-nav-item {
  color: #c8daee; font-size: .8rem;
  font-family: 'Noto Sans Tamil', sans-serif;
  padding: .55rem 1rem; cursor: pointer;
  border-bottom: 3px solid transparent;
  text-decoration: none; letter-spacing: .02em; white-space: nowrap;
}
.gov-nav-item:hover { color: white; background: rgba(255,255,255,.08); }
.gov-nav-item.active { color: white; border-bottom-color: var(--tn-saffron); font-weight: 500; }
.gov-nav-sep { color: rgba(255,255,255,.2); padding: 0 .1rem; font-size: .7rem; }

/* ══ BREADCRUMB ══ */
.gov-breadcrumb {
  background: var(--tn-white); border-bottom: 1px solid var(--tn-border);
  padding: .4rem 1.5rem; font-size: .73rem; color: var(--tn-gray3);
  font-family: 'Noto Sans Tamil', sans-serif;
  display: flex; align-items: center; gap: .4rem;
}
.gov-bc-link { color: var(--tn-blue); }

/* ══ TICKER ══ */
.tn-ticker {
  background: var(--tn-saffron); color: var(--tn-navy2);
  font-family: 'Noto Sans Tamil', sans-serif; font-size: .78rem;
  padding: .22rem 1.5rem; overflow: hidden; white-space: nowrap;
  display: flex; align-items: center; gap: .6rem;
}
.tn-ticker-label {
  background: var(--tn-navy); color: #ffcc66;
  padding: .1rem .5rem; border-radius: 1px;
  font-size: .7rem; font-weight: 600; flex-shrink: 0; letter-spacing: .03em;
}
.tn-ticker-content { animation: ticker 50s linear infinite; display: inline-block; }
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-60%)} }

/* ══ LEFT SIDEBAR ══ */
.gov-sidebar-head {
  background: var(--tn-gray1); border-left: 4px solid var(--tn-navy);
  padding: .5rem .9rem; font-size: .74rem; font-weight: 600; color: var(--tn-navy);
  font-family: 'Noto Sans Tamil', sans-serif;
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 0;
}
.gov-sidebar-body { padding: .6rem .5rem; border-bottom: 1px solid var(--tn-gray1); }
.gov-stat-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: .3rem .2rem; border-bottom: 1px dashed var(--tn-gray1); font-size: .75rem;
}
.gov-stat-label { color: var(--tn-text2); font-family: 'Noto Sans Tamil', sans-serif; }
.gov-stat-val { color: var(--tn-navy); font-weight: 600; font-family: 'Noto Sans Tamil', sans-serif; }
.gov-infobox {
  background: #e8f0fa; border: 1px solid #b8cce8; border-left: 4px solid var(--tn-navy);
  padding: .5rem .7rem; font-size: .74rem; color: var(--tn-blue);
  font-family: 'Noto Sans Tamil', sans-serif; line-height: 1.55; margin: .4rem 0;
}
.gov-warnbox {
  background: #fef3e2; border-left: 4px solid var(--tn-saffron);
  padding: .45rem .7rem; font-size: .73rem; color: var(--tn-warn);
  font-family: 'Noto Sans Tamil', sans-serif; margin: .4rem 0;
}

/* ══ STATS GRID ══ */
.stats-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:.5rem; margin-bottom:.9rem; }
.stat-box {
  background: var(--tn-white); border: 1px solid var(--tn-border);
  border-top: 3px solid var(--tn-navy); padding: .5rem .5rem; text-align: center;
}
.stat-num { font-family:'Noto Serif Tamil',serif; font-size:1.25rem; font-weight:700; color:var(--tn-navy); display:block; }
.stat-lbl { font-size:.62rem; text-transform:uppercase; letter-spacing:.04em; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; }

/* ══ DOCUMENT CARD ══ */
.gov-doc-card {
  background: var(--tn-white); border: 1px solid var(--tn-border);
  border-top: 3px solid var(--tn-saffron);
}
.gov-doc-titlebar {
  background: var(--tn-gray1); border-bottom: 1px solid var(--tn-border);
  padding: .45rem 1rem; display: flex; align-items: center; justify-content: space-between;
}
.gov-doc-filename { font-family:'Noto Sans Tamil',sans-serif; font-size:.78rem; color:var(--tn-navy); font-weight:600; }
.gov-doc-meta { font-size:.68rem; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; }
.gov-doc-body { padding:1rem 1.4rem; max-height:60vh; overflow-y:auto; }

/* ══ READING TEXT ══ */
.doc-content { font-family:'Noto Sans Tamil',sans-serif; font-size:1.05rem; line-height:2.2; color:var(--tn-text); }
.doc-para { margin-bottom:1rem; text-align:justify; }
.doc-heading {
  font-family:'Noto Serif Tamil',serif; font-size:1.12rem; font-weight:700; color:var(--tn-navy);
  background:var(--tn-gray1); border-left:4px solid var(--tn-saffron);
  padding:.4rem .8rem; margin:1.1rem 0 .5rem;
}
.doc-list-item { padding:.15rem 0 .15rem 1.2rem; position:relative; }
.doc-list-item::before { content:'▸'; position:absolute; left:0; color:var(--tn-saffron); font-size:.8rem; top:.3rem; }

/* ══ CLICKABLE WORD ══ */
.tw {
  cursor:pointer; border-bottom:2px solid var(--tn-saffron); color:var(--tn-text);
  padding:0 1px; transition:background .12s,color .12s; display:inline;
}
.tw:hover { background:#fff3cc; color:var(--tn-navy); border-bottom-color:var(--tn-navy); }
.tw.active { background:#ffeaa0; color:var(--tn-navy2); border-bottom:2.5px solid var(--tn-navy); font-weight:600; }

/* ══ MEANING PANEL ══ */
.gov-meaning-head {
  background: var(--tn-navy); color:white;
  padding:.65rem 1rem; font-family:'Noto Sans Tamil',sans-serif;
  font-size:.76rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em;
  display:flex; align-items:center; gap:.5rem;
  border-bottom:3px solid var(--tn-saffron);
}
.mcard { border:1px solid var(--tn-border); overflow:hidden; margin-bottom:.7rem; }
.mcard-word-bar { background:var(--tn-navy); padding:.8rem 1rem; text-align:center; }
.mcard-word { font-family:'Noto Serif Tamil',serif; font-size:2rem; font-weight:700; color:white; display:block; }
.mcard-body { padding:.85rem 1rem; }
.tier-badge {
  display:inline-flex; align-items:center; gap:.3rem;
  font-size:.67rem; padding:.18rem .6rem; border-radius:2px; margin-bottom:.7rem;
  font-family:'Noto Sans Tamil',sans-serif; font-weight:500; letter-spacing:.03em;
}
.t2{background:#d4edda;color:#155724;border:1px solid #b8ddc4}
.t3{background:#d1ecf1;color:#0c5460;border:1px solid #bee5eb}
.t4{background:#e2d9f3;color:#432874;border:1px solid #c8b8e8}
.tn{background:#f8d7da;color:#721c24;border:1px solid #f5c2c7}
.mcard-sec-lbl {
  font-size:.65rem; text-transform:uppercase; letter-spacing:.07em; color:var(--tn-gray3);
  font-family:'Noto Sans Tamil',sans-serif; margin:.55rem 0 .18rem;
  display:flex; align-items:center; gap:.3rem;
}
.mcard-sec-lbl::after { content:''; flex:1; height:1px; background:var(--tn-gray1); }
.mcard-en { font-size:1.2rem; font-weight:600; color:var(--tn-navy); font-family:'Source Serif 4',serif; }
.mcard-ta {
  font-family:'Noto Sans Tamil',sans-serif; font-size:.92rem; color:var(--tn-green);
  background:#eaf5ee; border:1px solid #b8ddc4; padding:.32rem .6rem; margin-top:.3rem;
}
.mcard-def {
  font-size:.86rem; color:var(--tn-text2); line-height:1.6;
  background:var(--tn-offwhite); border:1px solid var(--tn-gray1);
  padding:.45rem .6rem; margin-top:.3rem; font-family:'Source Serif 4',serif;
}
.mcard-ex { font-size:.76rem; color:var(--tn-gray3); border-top:1px dashed var(--tn-gray1); padding-top:.45rem; margin-top:.45rem; font-family:'Noto Sans Tamil',sans-serif; }
.panel-idle { padding:2rem 1rem; text-align:center; }
.panel-idle-icon { font-size:2rem; margin-bottom:.6rem; }
.panel-idle-text { font-size:.8rem; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; line-height:1.6; font-style:italic; }
.hist-label { font-size:.66rem; text-transform:uppercase; letter-spacing:.07em; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; margin-bottom:.35rem; }
.hist-chip {
  display:inline-block; font-family:'Noto Sans Tamil',sans-serif; font-size:.8rem;
  padding:.16rem .5rem; margin:2px; background:var(--tn-offwhite);
  border:1px solid var(--tn-border); color:var(--tn-navy); cursor:pointer;
}
.hist-chip:hover { background:var(--tn-navy); color:white; }
.gov-search-label { font-size:.7rem; text-transform:uppercase; letter-spacing:.06em; color:var(--tn-navy); font-family:'Noto Sans Tamil',sans-serif; font-weight:600; margin-bottom:.35rem; }

/* ══ UPLOAD ══ */
.gov-upload-title {
  font-size:.76rem; font-weight:600; color:var(--tn-navy);
  font-family:'Noto Sans Tamil',sans-serif; text-transform:uppercase; letter-spacing:.05em;
  margin-bottom:.5rem; display:flex; align-items:center; gap:.4rem;
}
.gov-upload-title::before { content:''; display:inline-block; width:3px; height:13px; background:var(--tn-saffron); border-radius:1px; }

/* ══ STREAMLIT OVERRIDES ══ */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
  font-family:'Noto Sans Tamil',sans-serif !important; font-size:.98rem !important;
  border:1.5px solid var(--tn-border) !important; border-radius:2px !important;
  background:var(--tn-white) !important; color:var(--tn-text) !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
  border-color:var(--tn-navy) !important;
  box-shadow:0 0 0 2px rgba(0,51,102,.15) !important;
}
.stButton>button {
  background:var(--tn-navy) !important; color:white !important;
  border:none !important; border-radius:2px !important;
  font-family:'Noto Sans Tamil',sans-serif !important;
  font-size:.8rem !important; letter-spacing:.04em !important;
  padding:.42rem 1rem !important; width:100%; font-weight:500 !important;
}
.stButton>button:hover { background:var(--tn-blue) !important; }
.stSelectbox>div>div { border-radius:2px !important; }
.stFileUploader>div { background:rgba(0,51,102,.03) !important; border:2px dashed var(--tn-navy) !important; border-radius:2px !important; }
.stTabs [data-baseweb="tab-list"] { background:var(--tn-gray1); border-bottom:2px solid var(--tn-border); gap:0; }
.stTabs [data-baseweb="tab"] { font-family:'Noto Sans Tamil',sans-serif; font-size:.78rem; color:var(--tn-text2); padding:.5rem 1.1rem; border-bottom:3px solid transparent; letter-spacing:.02em; }
.stTabs [aria-selected="true"] { color:var(--tn-navy) !important; border-bottom-color:var(--tn-saffron) !important; background:white !important; font-weight:600 !important; }
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:var(--tn-gray1); }
::-webkit-scrollbar-thumb { background:var(--tn-gray2); border-radius:2px; }

/* ══ FOOTER ══ */
.gov-footer {
  background:var(--tn-navy2); color:#8899aa;
  padding:.85rem 1.5rem; font-size:.7rem;
  font-family:'Noto Sans Tamil',sans-serif;
  display:flex; justify-content:space-between; align-items:center;
  border-top:3px solid var(--tn-saffron); margin-top:1rem;
}
.gov-footer-links { display:flex; gap:1rem; }
.gov-footer-links a { color:#6688aa; text-decoration:none; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
_TAMIL_RE   = re.compile(r'[\u0B80-\u0BFF]+')
_PUNC_STRIP = re.compile(r'^[^\u0B80-\u0BFF]+|[^\u0B80-\u0BFF]+$')

def clean_word(w):
    w = _PUNC_STRIP.sub('', w).strip()
    return re.sub(r'[\u0B82\u0B83]+$', '', w)

def is_tamil_word(w):
    cw = clean_word(w)
    return len(cw) >= 2 and bool(_TAMIL_RE.search(cw))

@st.cache_data(show_spinner=False)
def load_dict():
    p = Path(__file__).parent / "tamil.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}

TDICT = load_dict()
TAMIL_VOWELS     = list("அஆஇஈஉஊஎஏஐஒஓஔ")
TAMIL_CONSONANTS = list("கசடதபறஞஜஸஷஹணனநமயரலவழளஃ")

# ══════════════════════════════════════════════════════════════════════
# DOCUMENT EXTRACTION
# ══════════════════════════════════════════════════════════════════════
def extract_docx(data):
    from docx import Document
    doc = Document(io.BytesIO(data))
    blocks = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style else ""
        if "Heading" in style:
            blocks.append({"type":"heading","text":text})
        elif "List" in style:
            blocks.append({"type":"list","text":text})
        else:
            blocks.append({"type":"para","text":text})
    return blocks

def extract_pdf(data):
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    blocks = []
    for page in doc:
        for line in page.get_text().splitlines():
            line = line.strip()
            if len(line) > 2:
                blocks.append({"type":"para","text":line})
    return blocks

def extract_txt(data):
    for enc in ("utf-8","utf-16","latin-1"):
        try:
            text = data.decode(enc); break
        except Exception:
            pass
    else:
        text = data.decode("utf-8", errors="replace")
    return [{"type":"para","text":l.strip()} for l in text.splitlines() if l.strip()]

def extract_document(uploaded):
    data = uploaded.read()
    name = uploaded.name.lower()
    try:
        if name.endswith(".docx"):   return extract_docx(data)
        elif name.endswith(".pdf"):  return extract_pdf(data)
        else:                        return extract_txt(data)
    except Exception as e:
        st.error(f"Extraction error: {e}"); return []

# ══════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════
def tokenize_html(text):
    parts = []
    for tok in text.split():
        if is_tamil_word(tok):
            safe = clean_word(tok).replace("'","&#39;").replace('"',"&quot;")
            parts.append(
                f'<span class="tw" data-word="{safe}" '
                f'onclick="pickWord(\'{safe}\')" '
                f'title="கிளிக் செய்யவும்">{tok}</span>'
            )
        else:
            parts.append(tok)
    return " ".join(parts)

def blocks_to_html(blocks):
    out = []
    for b in blocks:
        txt = tokenize_html(b["text"])
        if b["type"] == "heading":
            out.append(f'<div class="doc-heading">{txt}</div>')
        elif b["type"] == "list":
            out.append(f'<div class="doc-para doc-list-item">{txt}</div>')
        else:
            out.append(f'<div class="doc-para">{txt}</div>')
    return "\n".join(out)

# ══════════════════════════════════════════════════════════════════════
# LOOKUP
# ══════════════════════════════════════════════════════════════════════
def tier2_json(word):
    w = clean_word(word)
    if w in TDICT:
        e = TDICT[w]
        return {"english":e.get("english",""),"tamil":e.get("tamil",""),
                "example":e.get("example",""),"tier":2,"label":"📖 உள்ளக அகராதி"}
    for n in (1,2):
        s = w[:-n]
        if len(s) >= 2 and s in TDICT:
            e = TDICT[s]
            return {"english":e.get("english","")+" (வேர்ச்சொல்)","tamil":e.get("tamil",""),
                    "example":e.get("example",""),"tier":2,"label":"📖 அகராதி (வேர்)"}
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _dict_api(en_word):
    import requests
    SKIP = {"the","a","an","to","of","in","on","at","it","is","be","as","this","that","was","are"}
    words = [w for w in en_word.lower().split() if w not in SKIP]
    if not words: return ""
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{words[0]}", timeout=6)
        if r.status_code == 200:
            for entry in r.json():
                for m in entry.get("meanings",[]):
                    for d in m.get("definitions",[]):
                        txt = d.get("definition","")
                        BAD = ("with a comp","used to","(used","an article","a function word",
                               "expressing","indicates","denoting","refers to")
                        if txt and not any(txt.lower().startswith(b) for b in BAD) and len(txt)>15:
                            return txt[:240]
    except Exception: pass
    return ""

@st.cache_data(ttl=3600, show_spinner=False)
def tier3_chain(word):
    try:
        from deep_translator import GoogleTranslator
        en = GoogleTranslator(source="ta", target="en").translate(word)
        if not en: return None
        defn = _dict_api(en)
        ta_defn = ""
        if defn:
            try: ta_defn = GoogleTranslator(source="en", target="ta").translate(defn[:200])
            except Exception: pass
        return {"english":en,"tamil":ta_defn or "","definition":defn,"example":"","tier":3,"label":"🔗 மொழிபெயர்ப்பு"}
    except Exception: return None

@st.cache_resource(show_spinner=False)
def _ml_pipe():
    try:
        from transformers import pipeline
        return pipeline("translation", model="Helsinki-NLP/opus-mt-ta-en", device=-1)
    except Exception: return None

@st.cache_data(ttl=3600, show_spinner=False)
def tier4_ml(word):
    pipe = _ml_pipe()
    if not pipe: return None
    try:
        res = pipe(word, max_length=128)
        en = res[0].get("translation_text","") if res else ""
        if not en: return None
        return {"english":en,"tamil":"","definition":_dict_api(en),"example":"","tier":4,"label":"🤖 நரம்பு வலை"}
    except Exception: return None

def lookup(word):
    word = word.strip()
    if not word: return {"english":"","tamil":"","tier":0,"label":""}
    r = tier2_json(word)
    if r: return r
    r = tier3_chain(word)
    if r: return r
    r = tier4_ml(word)
    if r: return r
    return {"english":"பொருள் கண்டுபிடிக்கவில்லை","tamil":"Meaning not found",
            "definition":"","example":"","tier":0,"label":"❌ கண்டுபிடிக்கவில்லை"}

def meaning_card_html(word, r):
    tier = r.get("tier",0)
    tcls = {2:"t2",3:"t3",4:"t4"}.get(tier,"tn")
    en   = r.get("english","—")
    ta   = r.get("tamil","")
    defn = r.get("definition","")
    ex   = r.get("example","")
    lbl  = r.get("label","")

    ta_sec = (f'<div class="mcard-sec-lbl">தமிழ் விளக்கம்</div>'
              f'<div class="mcard-ta">🌿 {ta}</div>') if ta else ""
    def_sec = (f'<div class="mcard-sec-lbl">வரையறை | Definition</div>'
               f'<div class="mcard-def">{defn}</div>') if defn and defn != en and len(defn)>12 else ""
    ex_sec = f'<div class="mcard-ex">📜 {ex}</div>' if ex else ""

    return f"""
    <div class="mcard">
      <div class="mcard-word-bar"><span class="mcard-word">{word}</span></div>
      <div class="mcard-body">
        <span class="tier-badge {tcls}">{lbl} · நிலை {tier}</span>
        <div class="mcard-sec-lbl">ஆங்கில பொருள் | English</div>
        <div class="mcard-en">{en}</div>
        {ta_sec}{def_sec}{ex_sec}
      </div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k,v in [("blocks",[]),("sel_word",""),("meaning",None),
            ("history",[]),("fname",""),("paste_blocks",[])]:
    if k not in st.session_state:
        st.session_state[k] = v

try:
    clicked = st.query_params.get("w","")
    if clicked and clicked != st.session_state.sel_word:
        st.session_state.sel_word = clicked
        st.session_state.meaning  = lookup(clicked)
        if clicked not in st.session_state.history:
            st.session_state.history.insert(0, clicked)
            st.session_state.history = st.session_state.history[:20]
except Exception: pass

# ══════════════════════════════════════════════════════════════════════
# GOVERNMENT HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gov-topstrip">
  <div>🇮🇳 தமிழ்நாடு அரசு · Government of Tamil Nadu · India</div>
  <div class="gov-topstrip-links">
    <span>📅 30 மார்ச் 2026</span>
    <span style="color:#445566">|</span>
    <span>Screen Reader</span>
    <span>A+ A A-</span>
    <span>தமிழ் | English</span>
  </div>
</div>
<div class="gov-header">
  <div class="gov-header-logo">
    <div class="gov-emblem">த</div>
    <div>
      <div class="gov-logo-title">தமிழ்நாடு அரசு</div>
      <div class="gov-logo-sub">GOVERNMENT OF TAMIL NADU · INDIA</div>
    </div>
  </div>
  <div class="gov-header-center">
    <div>
      <div class="gov-app-title">தமிழ் மொழி உதவியாளர் — Tamil Language Assistant</div>
      <div class="gov-app-sub">
        ஆவண வாசிப்பு · சொல் பொருள் தேடல் · 4-நிலை அமைப்பு |
        Document Reader · Word Meaning · 4-Tier Engine
      </div>
    </div>
  </div>
  <div class="gov-header-badges">
    <div class="gov-badge"><span class="gov-badge-dot"></span>LIVE SYSTEM</div>
    <div class="gov-badge">🏛️ TN GOVT</div>
    <div class="gov-badge">🔒 SECURE</div>
  </div>
</div>
<div class="gov-nav">
  <a class="gov-nav-item active">🏠 முகப்பு</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item">📄 ஆவண வாசிப்பு</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item">🔍 சொல் தேடல்</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item">📚 அகராதி</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item">📊 புள்ளிவிவரம்</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item">ℹ️ உதவி</a>
</div>
<div class="gov-breadcrumb">
  <span class="gov-bc-link">முகப்பு</span> ›
  <span class="gov-bc-link">சேவைகள்</span> ›
  <span>தமிழ் மொழி உதவியாளர்</span>
</div>
<div class="tn-ticker">
  <span class="tn-ticker-label">📢 அறிவிப்பு</span>
  <span class="tn-ticker-content">
    தமிழ் சொற்களை கிளிக் செய்து பொருள் காணுங்கள் &nbsp;·&nbsp;
    PDF, DOCX, TXT கோப்புகளை பதிவேற்றவும் &nbsp;·&nbsp;
    Click any underlined Tamil word to see meaning &nbsp;·&nbsp;
    4-நிலை பொருள் தேடல் அமைப்பு இப்போது கிடைக்கிறது &nbsp;·&nbsp;
    உரையை ஒட்டி தமிழ் சொற்களை படிக்கலாம் &nbsp;·&nbsp;
    தமிழ்நாடு அரசு சேவை — Government of Tamil Nadu Service &nbsp;·&nbsp;
    தமிழ் சொற்களை கிளிக் செய்து பொருள் காணுங்கள் &nbsp;·&nbsp;
    PDF, DOCX, TXT கோப்புகளை பதிவேற்றவும் &nbsp;·&nbsp;
    Click any underlined Tamil word to see meaning &nbsp;·&nbsp;
    4-நிலை பொருள் தேடல் அமைப்பு இப்போது கிடைக்கிறது
  </span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# BODY — 3 COLUMNS
# ══════════════════════════════════════════════════════════════════════
col_l, col_c, col_r = st.columns([2, 5, 3], gap="small")

# ─────────────────────────────────────────────────────────────────────
# LEFT SIDEBAR
# ─────────────────────────────────────────────────────────────────────
with col_l:
    # Vowels
    st.markdown('<div class="gov-sidebar-head">🔤 உயிர் எழுத்துக்கள்</div>', unsafe_allow_html=True)
    st.markdown('<div class="gov-sidebar-body">', unsafe_allow_html=True)
    vcols = st.columns(6)
    for i, letter in enumerate(TAMIL_VOWELS):
        with vcols[i % 6]:
            if st.button(letter, key=f"v_{letter}"):
                st.session_state.sel_word = letter
                st.session_state.meaning  = lookup(letter)
                if letter not in st.session_state.history:
                    st.session_state.history.insert(0, letter)
    st.markdown('</div>', unsafe_allow_html=True)

    # Consonants
    st.markdown('<div class="gov-sidebar-head">🔤 மெய் எழுத்துக்கள்</div>', unsafe_allow_html=True)
    st.markdown('<div class="gov-sidebar-body">', unsafe_allow_html=True)
    ccols = st.columns(6)
    for i, letter in enumerate(TAMIL_CONSONANTS[:18]):
        with ccols[i % 6]:
            if st.button(letter, key=f"c_{letter}"):
                st.session_state.sel_word = letter
                st.session_state.meaning  = lookup(letter)
    st.markdown('</div>', unsafe_allow_html=True)

    # Document stats
    all_text = " ".join(b["text"] for b in st.session_state.blocks)
    tw_all   = [clean_word(t) for t in all_text.split() if is_tamil_word(t)]
    tw_uniq  = list(dict.fromkeys(w for w in tw_all if w))
    in_dict  = sum(1 for w in tw_uniq if tier2_json(w))

    st.markdown(f"""
    <div class="gov-sidebar-head">📊 ஆவண புள்ளிவிவரம்</div>
    <div class="gov-sidebar-body">
      <div class="gov-stat-row">
        <span class="gov-stat-label">தமிழ் சொற்கள்</span>
        <span class="gov-stat-val">{len(tw_uniq):,}</span>
      </div>
      <div class="gov-stat-row">
        <span class="gov-stat-label">அகராதியில் உள்ளவை</span>
        <span class="gov-stat-val">{in_dict:,}</span>
      </div>
      <div class="gov-stat-row">
        <span class="gov-stat-label">தேடல் தேவையானவை</span>
        <span class="gov-stat-val">{max(0, len(tw_uniq)-in_dict):,}</span>
      </div>
      <div class="gov-stat-row">
        <span class="gov-stat-label">அகராதி அளவு</span>
        <span class="gov-stat-val">{len(TDICT):,}</span>
      </div>
      <div class="gov-stat-row">
        <span class="gov-stat-label">தேர்ந்தெடுக்கப்பட்டது</span>
        <span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">
          {st.session_state.sel_word or "—"}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Info
    st.markdown("""
    <div class="gov-sidebar-head">ℹ️ பயன்பாட்டு முறை</div>
    <div class="gov-sidebar-body">
      <div class="gov-infobox">
        📄 PDF / DOCX / TXT பதிவேற்றவும்<br>
        🖱️ தமிழ் சொல்லை கிளிக் செய்யவும்<br>
        📖 வலதில் பொருள் தோன்றும்<br>
        📋 உரையையும் ஒட்டலாம்
      </div>
      <div class="gov-warnbox">
        ⚠️ அரசு ஆவணங்களை பாதுகாப்பாக பதிவேற்றவும். இந்த சேவை இலவசம்.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # TN Symbols
    st.markdown("""
    <div class="gov-sidebar-head">🏛️ தமிழ்நாடு சின்னங்கள்</div>
    <div class="gov-sidebar-body">
      <div class="gov-stat-row"><span class="gov-stat-label">🌺 மலர்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">கொன்றை</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label">🐦 பறவை</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">மரங்கொத்தி</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label">🌳 மரம்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">பனை மரம்</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label">🦌 விலங்கு</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">நீலகிரி தார்</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label">🐟 மீன்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">இந்திய கணவாய்</span></div>
      <div style="text-align:center;margin-top:.7rem;padding:.5rem;background:#e8f0fa;border-radius:2px">
        <div style="font-family:'Noto Serif Tamil',serif;font-size:1.15rem;color:#003366;font-weight:700">செந்தமிழ் வாழ்க!</div>
        <div style="font-size:.68rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif;margin-top:.15rem">தமிழ் மொழி எப்போதும் வாழட்டும்</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# CENTER — READER
# ─────────────────────────────────────────────────────────────────────
with col_c:
    tab_upload, tab_paste = st.tabs([
        "📤 ஆவணம் பதிவேற்று | Upload Document",
        "📋 உரை ஒட்டு | Paste Text"
    ])

    with tab_upload:
        st.markdown('<div style="margin-top:.5rem"><div class="gov-upload-title">கோப்பு பதிவேற்றம் | File Upload</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "PDF, DOCX, TXT", type=["pdf","docx","txt"],
            label_visibility="collapsed", key="uploader",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded:
            if uploaded.name != st.session_state.fname:
                with st.spinner("ஆவணம் படிக்கிறது… | Reading document…"):
                    blocks = extract_document(uploaded)
                    st.session_state.blocks       = blocks
                    st.session_state.fname        = uploaded.name
                    st.session_state.sel_word     = ""
                    st.session_state.meaning      = None
                    st.session_state.paste_blocks = []

            blocks  = st.session_state.blocks
            all_txt = " ".join(b["text"] for b in blocks)
            tw_list = [clean_word(t) for t in all_txt.split() if is_tamil_word(t)]
            tw_u    = list(dict.fromkeys(w for w in tw_list if w))

            st.markdown(f"""
            <div class="stats-grid">
              <div class="stat-box"><span class="stat-num">{len(blocks)}</span><span class="stat-lbl">பகுதிகள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(all_txt.split()):,}</span><span class="stat-lbl">மொத்த சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(tw_u):,}</span><span class="stat-lbl">தமிழ் சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{sum(1 for w in tw_u if tier2_json(w)):,}</span><span class="stat-lbl">அகராதியில்</span></div>
            </div>
            <div class="gov-doc-card">
              <div class="gov-doc-titlebar">
                <span class="gov-doc-filename">📄 {uploaded.name}</span>
                <span class="gov-doc-meta">
                  {len(blocks)} பகுதிகள் · {len(tw_u)} தமிழ் சொற்கள் ·
                  <span style="color:#1a6b2e">●</span> தயார்
                </span>
              </div>
              <div class="gov-doc-body">
                <div class="doc-content">{blocks_to_html(blocks)}</div>
              </div>
            </div>
            <div style="text-align:center;margin-top:.4rem;font-size:.72rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif">
              💡 அடிக்கோடிட்ட தமிழ் சொற்களை கிளிக் செய்யவும் · Click underlined Tamil words for meaning
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem 2rem;background:white;
                        border:1px dashed #c5cdd8;border-top:3px solid #003366;margin-top:.5rem">
              <div style="font-size:2.8rem;margin-bottom:.8rem">📄</div>
              <div style="font-family:'Noto Serif Tamil',serif;font-size:1.2rem;color:#003366;font-weight:700;margin-bottom:.4rem">
                தமிழ் ஆவணத்தை பதிவேற்றுங்கள்
              </div>
              <div style="font-size:.83rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif">
                PDF · Microsoft Word (DOCX) · Plain Text (TXT)
              </div>
              <div style="margin-top:1.5rem;padding:1rem 1.5rem;background:#f5f7fa;display:inline-block;text-align:left;border-left:3px solid #e07b00">
                <div style="font-family:'Noto Serif Tamil',serif;font-size:.95rem;color:#1a5276;font-weight:600">
                  "யாதும் ஊரே யாவரும் கேளிர்"
                </div>
                <div style="font-size:.72rem;color:#7a8a99;margin-top:.3rem;font-family:'Noto Sans Tamil',sans-serif">
                  — புறநானூறு | All towns are our own; all people our kin.
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_paste:
        st.markdown('<div style="margin-top:.5rem"><div class="gov-upload-title">உரை ஒட்டு | Paste Text</div>', unsafe_allow_html=True)
        pasted = st.text_area(
            "உரை", height=140,
            placeholder="தமிழ் உரையை இங்கே ஒட்டவும் அல்லது தட்டச்சு செய்யவும்...\nPaste or type Tamil text here...",
            key="paste_input", label_visibility="collapsed",
        )
        if st.button("🔍 உரையை படி | Read Text", key="paste_btn"):
            if pasted.strip():
                blocks = [{"type":"para","text":l.strip()} for l in pasted.strip().splitlines() if l.strip()]
                st.session_state.paste_blocks = blocks
                st.session_state.blocks       = blocks
                st.session_state.fname        = "ஒட்டிய உரை"
                st.session_state.sel_word     = ""
                st.session_state.meaning      = None

        if st.session_state.paste_blocks:
            pb    = st.session_state.paste_blocks
            pt    = " ".join(b["text"] for b in pb)
            ptw   = list(dict.fromkeys(clean_word(t) for t in pt.split() if is_tamil_word(t)))
            st.markdown(f"""
            <div class="stats-grid">
              <div class="stat-box"><span class="stat-num">{len(pb)}</span><span class="stat-lbl">வரிகள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(pt.split())}</span><span class="stat-lbl">மொத்த சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(ptw)}</span><span class="stat-lbl">தமிழ் சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{sum(1 for w in ptw if tier2_json(w))}</span><span class="stat-lbl">அகராதியில்</span></div>
            </div>
            <div class="gov-doc-card">
              <div class="gov-doc-titlebar">
                <span class="gov-doc-filename">📋 ஒட்டிய உரை | Pasted Text</span>
                <span class="gov-doc-meta">{len(ptw)} தமிழ் சொற்கள்</span>
              </div>
              <div class="gov-doc-body">
                <div class="doc-content">{blocks_to_html(pb)}</div>
              </div>
            </div>
            <div style="text-align:center;margin-top:.4rem;font-size:.72rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif">
              💡 தமிழ் சொற்களை கிளிக் செய்யவும் · Click Tamil words for meaning
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# RIGHT — MEANING
# ─────────────────────────────────────────────────────────────────────
with col_r:
    st.markdown('<div class="gov-meaning-head">📖 சொல் பொருள் | Word Meaning</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div style="padding:.6rem .5rem .3rem"><div class="gov-search-label">🔍 சொல் தேடல் | Search Word</div></div>', unsafe_allow_html=True)
    manual = st.text_input(
        "சொல்", placeholder="e.g. அன்பு, வாடகை, உரிமை…",
        key="manual_input", label_visibility="collapsed",
    )
    if st.button("தேடு | Search", key="search_btn"):
        if manual.strip():
            w = manual.strip()
            with st.spinner("தேடுகிறது…"):
                st.session_state.meaning  = lookup(w)
                st.session_state.sel_word = w
            if w not in st.session_state.history:
                st.session_state.history.insert(0, w)
                st.session_state.history = st.session_state.history[:20]

    st.markdown('<div style="padding:0 .5rem">', unsafe_allow_html=True)

    if st.session_state.sel_word and st.session_state.meaning:
        st.markdown(meaning_card_html(st.session_state.sel_word, st.session_state.meaning),
                    unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="panel-idle">
          <div class="panel-idle-icon">🔍</div>
          <div class="panel-idle-text">
            ஆவணத்திலுள்ள எந்த தமிழ் சொல்லையும் கிளிக் செய்யுங்கள்.<br><br>
            Click any Tamil word in the document to see its meaning here.<br><br>
            அல்லது மேலே தட்டச்சு செய்யவும்.<br>
            Or type a word above.
          </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown(f'<div class="hist-label" style="padding:.4rem .2rem 0">🕐 சமீபத்திய தேடல்கள்</div>', unsafe_allow_html=True)
        chips = "".join(f'<span class="hist-chip">{w}</span>' for w in st.session_state.history)
        st.markdown(f'<div style="margin-bottom:.4rem">{chips}</div>', unsafe_allow_html=True)

        pick = st.selectbox(
            "மீண்டும் தேடு", ["— தேர்ந்தெடுங்கள் —"] + st.session_state.history,
            key="hist_pick", label_visibility="collapsed",
        )
        if pick and pick != "— தேர்ந்தெடுங்கள் —" and pick != st.session_state.sel_word:
            st.session_state.sel_word = pick
            with st.spinner(""): st.session_state.meaning = lookup(pick)
            st.rerun()

    # Dictionary browser
    st.markdown('<div style="margin-top:.6rem"><div class="gov-search-label">📚 அகராதி | Dictionary Browse</div></div>', unsafe_allow_html=True)
    if TDICT:
        letters = sorted({w[0] for w in TDICT if w})
        pick_l  = st.selectbox("எழுத்தால் தேடு", ["எல்லாம்"] + letters,
                               key="browse_letter", label_visibility="collapsed")
        filtered = {k:v for k,v in TDICT.items() if pick_l=="எல்லாம்" or k.startswith(pick_l)}
        st.caption(f"{len(filtered):,} சொற்கள்")
        for wk, wd in list(filtered.items())[:6]:
            en = wd.get("english","")[:35]
            with st.expander(f"{wk} — {en}"):
                st.markdown(meaning_card_html(wk,{**wd,"tier":2,"label":"📖 உள்ளக அகராதி"}),
                            unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gov-footer">
  <div>
    © 2026 தமிழ்நாடு அரசு | Government of Tamil Nadu · All Rights Reserved<br>
    <span style="color:#556677">
      தமிழ் மொழி உதவியாளர் v3.0 · 4-நிலை பொருள் தேடல் அமைப்பு ·
      Developed for Tamil Language Accessibility
    </span>
  </div>
  <div class="gov-footer-links">
    <a href="#">தனியுரிமை கொள்கை</a>
    <a href="#">பயன்பாட்டு விதிமுறைகள்</a>
    <a href="#">அணுகல் தகவல்</a>
    <a href="#">தொடர்பு கொள்ள</a>
    <a href="#">Sitemap</a>
  </div>
</div>
""", unsafe_allow_html=True)
