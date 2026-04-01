import streamlit as st
import json, re, io, math
from pathlib import Path
from collections import Counter

st.set_page_config(
    page_title="தமிழ்நாடு அரசு | Tamil Language Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)
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

.gov-breadcrumb {
  background: var(--tn-white); border-bottom: 1px solid var(--tn-border);
  padding: .4rem 1.5rem; font-size: .73rem; color: var(--tn-gray3);
  font-family: 'Noto Sans Tamil', sans-serif;
  display: flex; align-items: center; gap: .4rem;
}
.gov-bc-link { color: var(--tn-blue); }

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

.stats-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:.5rem; margin-bottom:.9rem; }
.stat-box {
  background: var(--tn-white); border: 1px solid var(--tn-border);
  border-top: 3px solid var(--tn-navy); padding: .5rem .5rem; text-align: center;
}
.stat-num { font-family:'Noto Serif Tamil',serif; font-size:1.25rem; font-weight:700; color:var(--tn-navy); display:block; }
.stat-lbl { font-size:.62rem; text-transform:uppercase; letter-spacing:.04em; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; }

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

.doc-content { font-family:'Noto Sans Tamil',sans-serif; font-size:1.05rem; line-height:2.2; color:var(--tn-text); }
.doc-para { margin-bottom:1rem; text-align:justify; }
.doc-heading {
  font-family:'Noto Serif Tamil',serif; font-size:1.12rem; font-weight:700; color:var(--tn-navy);
  background:var(--tn-gray1); border-left:4px solid var(--tn-saffron);
  padding:.4rem .8rem; margin:1.1rem 0 .5rem;
}
.doc-list-item { padding:.15rem 0 .15rem 1.2rem; position:relative; }
.doc-list-item::before { content:'▸'; position:absolute; left:0; color:var(--tn-saffron); font-size:.8rem; top:.3rem; }

.tw {
  cursor:pointer; border-bottom:2px solid var(--tn-saffron); color:var(--tn-text);
  padding:0 1px; transition:background .12s,color .12s; display:inline;
}
.tw:hover { background:#fff3cc; color:var(--tn-navy); border-bottom-color:var(--tn-navy); }
.tw.active { background:#ffeaa0; color:var(--tn-navy2); border-bottom:2.5px solid var(--tn-navy); font-weight:600; }

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

.gov-upload-title {
  font-size:.76rem; font-weight:600; color:var(--tn-navy);
  font-family:'Noto Sans Tamil',sans-serif; text-transform:uppercase; letter-spacing:.05em;
  margin-bottom:.5rem; display:flex; align-items:center; gap:.4rem;
}
.gov-upload-title::before { content:''; display:inline-block; width:3px; height:13px; background:var(--tn-saffron); border-radius:1px; }

.sum-card {
  background: var(--tn-white); border: 1px solid var(--tn-border);
  border-top: 3px solid var(--tn-green);
  margin-bottom: .8rem;
}
.sum-titlebar {
  background: var(--tn-green); color: white;
  padding: .5rem 1rem; font-family:'Noto Sans Tamil',sans-serif;
  font-size: .76rem; font-weight: 600; letter-spacing:.04em;
  display: flex; align-items:center; justify-content:space-between;
}
.sum-body {
  padding: 1rem 1.4rem;
  font-family:'Noto Sans Tamil',sans-serif; font-size:1rem;
  line-height: 2.1; color: var(--tn-text);
}
.sum-method-badge {
  display:inline-flex; align-items:center; gap:.3rem;
  font-size:.65rem; padding:.15rem .55rem; border-radius:2px;
  font-family:'Noto Sans Tamil',sans-serif; font-weight:500;
  background:#e8f5ee; color:#155724; border:1px solid #b8ddc4;
  margin-bottom:.6rem;
}

.metrics-panel {
  background: var(--tn-white); border: 1px solid var(--tn-border);
  border-top: 3px solid var(--tn-navy); margin-top: .6rem;
}
.metrics-head {
  background: var(--tn-navy2); color: white;
  padding: .5rem .9rem; font-family:'Noto Sans Tamil',sans-serif;
  font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em;
  display:flex; align-items:center; gap:.4rem;
}
.metrics-body { padding: .7rem .8rem; }
.metric-row {
  display: flex; align-items: center; gap:.6rem;
  margin-bottom: .6rem; padding-bottom:.6rem;
  border-bottom: 1px dashed var(--tn-gray1);
}
.metric-row:last-child { border-bottom: none; margin-bottom:0; padding-bottom:0; }
.metric-label {
  font-size:.7rem; color:var(--tn-text2); font-family:'Noto Sans Tamil',sans-serif;
  width: 130px; flex-shrink:0; line-height:1.3;
}
.metric-label small { display:block; color:var(--tn-gray3); font-size:.62rem; font-style:italic; }
.metric-bar-wrap { flex:1; height:10px; background:var(--tn-gray1); border-radius:1px; overflow:hidden; }
.metric-bar { height:100%; border-radius:1px; transition:width .6s ease; }
.bar-green  { background: #1a6b2e; }
.bar-blue   { background: #1a5276; }
.bar-saffron{ background: #e07b00; }
.bar-navy   { background: #003366; }
.bar-red    { background: #8b1a1a; }
.metric-val {
  font-size:.75rem; font-weight:600; color:var(--tn-navy);
  font-family:'Noto Sans Tamil',sans-serif; width:42px; text-align:right;
}
.metric-grade {
  font-size:.65rem; padding:.1rem .38rem; border-radius:2px; font-weight:600;
  font-family:'Noto Sans Tamil',sans-serif;
}
.grade-A { background:#d4edda; color:#155724; border:1px solid #b8ddc4; }
.grade-B { background:#d1ecf1; color:#0c5460; border:1px solid #bee5eb; }
.grade-C { background:#fff3cd; color:#856404; border:1px solid #ffc107; }
.grade-D { background:#f8d7da; color:#721c24; border:1px solid #f5c2c7; }
.metrics-summary-box {
  background: var(--tn-offwhite); border: 1px solid var(--tn-gray1);
  border-left: 4px solid var(--tn-saffron);
  padding: .55rem .8rem; margin-top: .5rem;
  font-size: .74rem; color: var(--tn-text2);
  font-family:'Noto Sans Tamil',sans-serif; line-height:1.6;
}
.overall-score-box {
  background: var(--tn-navy); color:white; padding:.6rem .9rem;
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:.6rem;
}
.overall-score-num {
  font-size:2rem; font-weight:700;
  font-family:'Noto Serif Tamil',serif;
}
.overall-score-label { font-size:.68rem; color:#aabbd4; font-family:'Noto Sans Tamil',sans-serif; margin-top:.1rem; }
.overall-score-grade { font-size:1.1rem; font-weight:700; padding:.3rem .7rem; border-radius:2px; }
.keywords-box {
  background:var(--tn-offwhite); border:1px solid var(--tn-gray1);
  padding:.5rem .7rem; margin-top:.4rem;
}
.kw-label { font-size:.62rem; text-transform:uppercase; letter-spacing:.07em; color:var(--tn-gray3); font-family:'Noto Sans Tamil',sans-serif; margin-bottom:.35rem; }
.kw-chip {
  display:inline-block; font-family:'Noto Sans Tamil',sans-serif; font-size:.72rem;
  padding:.1rem .4rem; margin:2px; border-radius:1px;
  background:#e8f0fa; border:1px solid #b8cce8; color:var(--tn-navy);
}
.kw-chip.in-summary { background:#d4edda; border-color:#b8ddc4; color:#155724; }

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

def tier2_json(word):
    w = clean_word(word)
    if w in TDICT:
        e = TDICT[w]
        return {"english":e.get("english",""),"tamil":e.get("tamil",""),
                "example":e.get("example",""),"tier":2,"label":"உள்ளக அகராதி"}
    for n in (1,2):
        s = w[:-n]
        if len(s) >= 2 and s in TDICT:
            e = TDICT[s]
            return {"english":e.get("english","")+" (வேர்ச்சொல்)","tamil":e.get("tamil",""),
                    "example":e.get("example",""),"tier":2,"label":"அகராதி (வேர்)"}
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
            "definition":"","example":"","tier":0,"label":"கண்டுபிடிக்கவில்லை"}

def meaning_card_html(word, r):
    tier = r.get("tier",0)
    tcls = {2:"t2",3:"t3",4:"t4"}.get(tier,"tn")
    en   = r.get("english","—")
    ta   = r.get("tamil","")
    defn = r.get("definition","")
    ex   = r.get("example","")
    lbl  = r.get("label","")

    ta_sec = (f'<div class="mcard-sec-lbl">தமிழ் விளக்கம்</div>'
              f'<div class="mcard-ta"> {ta}</div>') if ta else ""
    def_sec = (f'<div class="mcard-sec-lbl">வரையறை | Definition</div>'
               f'<div class="mcard-def">{defn}</div>') if defn and defn != en and len(defn)>12 else ""
    ex_sec = f'<div class="mcard-ex"> {ex}</div>' if ex else ""

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


def get_tamil_sentences(text):
    """
    Split Tamil text into sentence units.
    For Tamil legal docs, each line/block is a natural sentence unit.
    Also splits within lines on Tamil + standard punctuation.
    """
    line_sents = [l.strip() for l in text.splitlines() if l.strip()]
    final = []
    for line in line_sents:
        sub = re.split(r'[।॥\u0964\u0965\.\!\?;]+', line)
        for s in sub:
            s = s.strip()
            if len(s) > 5:
                final.append(s)
    seen, result = set(), []
    for s in final:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result if result else [text.strip()]

def score_sentence_tfidf(sentences):
    """Score sentences using TF-IDF-like approach for Tamil."""
    all_words = []
    sent_words = []
    for s in sentences:
        words = [clean_word(w) for w in s.split() if is_tamil_word(w)]
        sent_words.append(words)
        all_words.extend(words)

    total_docs = len(sentences)
    word_doc_freq = Counter()
    for sw in sent_words:
        for w in set(sw):
            word_doc_freq[w] += 1

    total_word_freq = Counter(all_words)

    scores = []
    for i, sw in enumerate(sent_words):
        if not sw:
            scores.append(0.0)
            continue
        score = 0.0
        for w in sw:
            tf  = sw.count(w) / len(sw)
            idf = math.log((total_docs + 1) / (word_doc_freq[w] + 1)) + 1
            score += tf * idf
        scores.append(score / len(sw))
    return scores

def score_sentence_position(sentences):
    """Positional bias: first and last sentences score higher."""
    n = len(sentences)
    scores = []
    for i in range(n):
        if i == 0 or i == n - 1:
            scores.append(1.0)
        elif i < n * 0.25:
            scores.append(0.7)
        elif i > n * 0.75:
            scores.append(0.5)
        else:
            scores.append(0.3)
    return scores

def score_sentence_length(sentences):
    """Prefer medium-length sentences, penalise very short/long."""
    scores = []
    for s in sentences:
        wc = len(s.split())
        if 8 <= wc <= 25:
            scores.append(1.0)
        elif 5 <= wc < 8:
            scores.append(0.6)
        elif wc > 25:
            scores.append(0.7)
        else:
            scores.append(0.3)
    return scores

def extractive_summarize(text, ratio=0.4, method="hybrid"):
    """
    Extractive summarization with three methods:
      - tfidf    : TF-IDF scoring
      - position : positional lead-bias
      - hybrid   : weighted blend
    Returns (summary_text, selected_indices, all_scores_dict).
    """
    sentences = get_tamil_sentences(text)
    n = len(sentences)

    if n == 0:
        return text, [], {}
    if n <= 3:
        return text, list(range(n)), {}
    n_select = max(3, min(n - 1, round(n * ratio)))

    tfidf_scores    = score_sentence_tfidf(sentences)
    position_scores = score_sentence_position(sentences)
    length_scores   = score_sentence_length(sentences)

    if method == "tfidf":
        final_scores = tfidf_scores
    elif method == "position":
        final_scores = position_scores
    else:  # hybrid
        final_scores = [
            0.5 * t + 0.3 * p + 0.2 * l
            for t, p, l in zip(tfidf_scores, position_scores, length_scores)
        ]

    ranked = sorted(range(len(sentences)), key=lambda i: final_scores[i], reverse=True)
    selected = sorted(ranked[:n_select])
    summary  = " ".join(sentences[i] for i in selected)

    scores_dict = {
        "tfidf":    tfidf_scores,
        "position": position_scores,
        "length":   length_scores,
        "final":    final_scores,
    }
    return summary, selected, scores_dict

def abstractive_summarize_ai(text, length_hint="medium"):
    """Call Anthropic API to generate a Tamil abstractive summary."""
    import requests

    length_map = {
        "short":  "2–3 sentences",
        "medium": "4–6 sentences",
        "long":   "8–10 sentences",
    }
    length_desc = length_map.get(length_hint, "4–6 sentences")

    prompt = (
        f"நீங்கள் ஒரு தமிழ் மொழி நிபுணர். கீழே கொடுக்கப்பட்ட தமிழ் ஆவண உரையை "
        f"படிக்கவும். இந்த உரையில் உள்ள அனைத்து முக்கிய கருத்துக்களையும், "
        f"தகவல்களையும், நபர்களையும், நிபந்தனைகளையும் உள்ளடக்கிய "
        f"விரிவான சுருக்கம் எழுதுங்கள். "
        f"சுருக்கம் {length_desc} இருக்க வேண்டும். "
        f"சுருக்கம் மட்டும் தமிழில் எழுதுங்கள், வேறு எந்த மொழியிலும் வேண்டாம். "
        f"முன்னுரை அல்லது 'சுருக்கம்:' என்று தொடங்க வேண்டாம், நேரடியாக எழுதுங்கள்.\n\n"
        f"உரை:\n{text[:4000]}\n\n"
        f"சுருக்கம்:"
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = resp.json()
        text_out = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_out += block["text"]
        return text_out.strip() if text_out else None
    except Exception as e:
        return None


def get_ngrams(tokens, n):
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))

def rouge_n(reference_tokens, summary_tokens, n=1):
    ref_ng = get_ngrams(reference_tokens, n)
    sum_ng = get_ngrams(summary_tokens, n)
    if not ref_ng or not sum_ng:
        return 0.0
    overlap = sum(min(ref_ng[k], sum_ng[k]) for k in sum_ng)
    recall  = overlap / sum(ref_ng.values())
    precision = overlap / sum(sum_ng.values())
    if precision + recall == 0:
        return 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1 * 100, 1)

def lcs_length(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(2)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i%2][j] = dp[(i-1)%2][j-1] + 1
            else:
                dp[i%2][j] = max(dp[(i-1)%2][j], dp[i%2][j-1])
    return dp[m%2][n]

def rouge_l(reference_tokens, summary_tokens):
    if not reference_tokens or not summary_tokens:
        return 0.0
    lcs = lcs_length(reference_tokens, summary_tokens)
    recall    = lcs / len(reference_tokens)
    precision = lcs / len(summary_tokens)
    if precision + recall == 0:
        return 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1 * 100, 1)

def compression_ratio(original_text, summary_text):
    orig_wc = len(original_text.split())
    sum_wc  = len(summary_text.split())
    if orig_wc == 0:
        return 0.0
    ratio = (1 - sum_wc / orig_wc) * 100
    return round(max(0.0, min(100.0, ratio)), 1)

def keyword_coverage(original_text, summary_text, top_n=15):
    orig_words = [clean_word(w) for w in original_text.split() if is_tamil_word(w)]
    sum_words  = set(clean_word(w) for w in summary_text.split() if is_tamil_word(w))
    if not orig_words:
        return 0.0, [], []
    freq = Counter(orig_words)
    top_kws = [w for w, _ in freq.most_common(top_n) if len(w) > 2]
    covered = [w for w in top_kws if w in sum_words]
    score   = round(len(covered) / len(top_kws) * 100, 1) if top_kws else 0.0
    return score, top_kws, covered

def lexical_diversity(text):
    words = [clean_word(w) for w in text.split() if is_tamil_word(w)]
    if len(words) < 3:
        return 0.0
    return round(len(set(words)) / len(words) * 100, 1)

def avg_sentence_length(text):
    sents = get_tamil_sentences(text)
    if not sents:
        return 0
    total = sum(len(s.split()) for s in sents)
    return round(total / len(sents), 1)

def grade_score(score):
    if score >= 75: return "A", "grade-A"
    if score >= 55: return "B", "grade-B"
    if score >= 35: return "C", "grade-C"
    return "D", "grade-D"

def evaluate_summary(original_text, summary_text, method_label=""):
    orig_toks = [clean_word(w) for w in original_text.split() if is_tamil_word(w)]
    sum_toks  = [clean_word(w) for w in summary_text.split() if is_tamil_word(w)]

    r1  = rouge_n(orig_toks, sum_toks, 1)
    r2  = rouge_n(orig_toks, sum_toks, 2)
    rl  = rouge_l(orig_toks, sum_toks)
    cr  = compression_ratio(original_text, summary_text)
    kc, top_kws, covered_kws = keyword_coverage(original_text, summary_text)
    ld_orig = lexical_diversity(original_text)
    ld_sum  = lexical_diversity(summary_text)
    asl_sum = avg_sentence_length(summary_text)
    n_sents_orig = len(get_tamil_sentences(original_text))
    n_sents_sum  = len(get_tamil_sentences(summary_text))

    overall = round((r1 * 0.3 + r2 * 0.2 + rl * 0.2 + kc * 0.3), 1)

    return {
        "rouge_1": r1,
        "rouge_2": r2,
        "rouge_l": rl,
        "compression_ratio": cr,
        "keyword_coverage": kc,
        "lexical_diversity_orig": ld_orig,
        "lexical_diversity_sum":  ld_sum,
        "avg_sent_len": asl_sum,
        "n_sents_orig": n_sents_orig,
        "n_sents_sum":  n_sents_sum,
        "top_keywords": top_kws,
        "covered_keywords": covered_kws,
        "overall": overall,
        "method": method_label,
    }

def _grade_color(score):
    if score >= 75: return ("#d4edda","#155724","#b8ddc4","A")
    if score >= 55: return ("#d1ecf1","#0c5460","#bee5eb","B")
    if score >= 35: return ("#fff3cd","#856404","#ffc107","C")
    return ("#f8d7da","#721c24","#f5c2c7","D")

def render_metrics_panel(metrics):
    if not metrics:
        return ""

    r1  = metrics["rouge_1"]
    r2  = metrics["rouge_2"]
    rl  = metrics["rouge_l"]
    cr  = metrics["compression_ratio"]
    kc  = metrics["keyword_coverage"]
    ld_s = metrics["lexical_diversity_sum"]
    overall = metrics["overall"]
    bg_o, fg_o, bd_o, lbl_o = _grade_color(overall)

    bar_colors = {"green":"#1a6b2e","blue":"#1a5276","navy":"#003366","saffron":"#e07b00","red":"#8b1a1a"}

    def row(label, sublabel, val, bar_color_key):
        pct = min(100, round(val))
        bg, fg, bd, gl = _grade_color(val)
        bc = bar_colors.get(bar_color_key, "#003366")
        return (
            f'<div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem;padding-bottom:.6rem;border-bottom:1px dashed #e8ecf1;">' +
            f'<div style="font-size:.7rem;color:#3a4a5a;font-family:Noto Sans Tamil,sans-serif;width:130px;flex-shrink:0;line-height:1.3;">' +
            f'{label}<span style="display:block;color:#7a8a99;font-size:.62rem;font-style:italic">{sublabel}</span></div>' +
            f'<div style="flex:1;height:10px;background:#e8ecf1;border-radius:1px;overflow:hidden;">' +
            f'<div style="height:100%;width:{pct}%;background:{bc};border-radius:1px;"></div></div>' +
            f'<div style="font-size:.75rem;font-weight:600;color:#003366;font-family:Noto Sans Tamil,sans-serif;width:42px;text-align:right;">{val:.1f}%</div>' +
            f'<span style="font-size:.65rem;padding:.1rem .38rem;border-radius:2px;font-weight:600;font-family:Noto Sans Tamil,sans-serif;background:{bg};color:{fg};border:1px solid {bd};">{gl}</span>' +
            f'</div>'
        )

    rows_html = (
        row("ROUGE-1", "Unigram overlap", r1, "green") +
        row("ROUGE-2", "Bigram overlap", r2, "blue") +
        row("ROUGE-L", "Longest common subseq.", rl, "navy") +
        row("Keyword Coverage", "முக்கிய சொல் உள்ளடக்கம்", kc, "saffron") +
        row("Lexical Diversity", "சொல் வகை / தனித்தன்மை", ld_s, "red")
    )

    top_kws = metrics.get("top_keywords", [])
    covered = set(metrics.get("covered_keywords", []))
    kw_chips = "".join(
        f'<span style="display:inline-block;font-family:Noto Sans Tamil,sans-serif;font-size:.72rem;padding:.1rem .4rem;margin:2px;border-radius:1px;' +
        ('background:#d4edda;border:1px solid #b8ddc4;color:#155724;">' if w in covered else 'background:#e8f0fa;border:1px solid #b8cce8;color:#003366;">') +
        f'{w}</span>'
        for w in top_kws[:15]
    )

    cr_color = "#1a6b2e" if cr >= 50 else ("#e07b00" if cr >= 25 else "#8b1a1a")
    n_orig = metrics["n_sents_orig"]
    n_sum  = metrics["n_sents_sum"]
    asl    = metrics["avg_sent_len"]

    summary_note = (
        f"சுருக்கம் {n_sum} வாக்கியங்களில் {n_orig} வாக்கியங்களை {cr:.0f}% குறைத்தது. "
        f"சராசரி வாக்கிய நீளம் {asl:.0f} சொற்கள். "
        f"முக்கிய சொற்களில் {len(covered)}/{len(top_kws)} உள்ளடக்கப்பட்டுள்ளன."
    )
    method_lbl = metrics.get("method", "")

    return (
        f'<div style="background:#fff;border:1px solid #c5cdd8;border-top:3px solid #003366;margin-top:.6rem;">' +
        f'<div style="background:#002244;color:white;padding:.5rem .9rem;font-family:Noto Sans Tamil,sans-serif;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">' +
        f' சுருக்க மதிப்பீடு | Summary Evaluation</div>' +
        f'<div style="padding:.7rem .8rem;">' +
        f'<div style="background:#003366;color:white;padding:.6rem .9rem;display:flex;align-items:center;justify-content:space-between;margin-bottom:.6rem;">' +
        f'<div><div style="font-size:2rem;font-weight:700;font-family:Noto Serif Tamil,serif;">{overall:.0f}</div>' +
        f'<div style="font-size:.68rem;color:#aabbd4;font-family:Noto Sans Tamil,sans-serif;margin-top:.1rem;">ஒட்டுமொத்த மதிப்பெண் | Overall Score (0–100)</div></div>' +
        f'<div><span style="font-size:1.1rem;font-weight:700;padding:.3rem .7rem;border-radius:2px;background:{bg_o};color:{fg_o};">{lbl_o}</span>' +
        f'<div style="font-size:.65rem;color:#aabbd4;margin-top:.3rem;font-family:Noto Sans Tamil,sans-serif;">{method_lbl}</div></div>' +
        f'</div>' +
        rows_html +
        f'<div style="display:flex;align-items:center;gap:.5rem;margin:.4rem 0;font-size:.7rem;font-family:Noto Sans Tamil,sans-serif;color:#3a4a5a;">' +
        f'<span>அமுக்க விகிதம் | Compression</span>' +
        f'<span style="font-size:1.1rem;font-weight:700;color:{cr_color};">{cr:.1f}%</span>' +
        f'<span style="color:#7a8a99;">({n_orig} → {n_sum} வாக்கியங்கள்)</span></div>' +
        f'<div style="background:#f5f7fa;border:1px solid #e8ecf1;padding:.5rem .7rem;margin-top:.4rem;">' +
        f'<div style="font-size:.62rem;text-transform:uppercase;letter-spacing:.07em;color:#7a8a99;font-family:Noto Sans Tamil,sans-serif;margin-bottom:.35rem;">🔑 முக்கிய சொற்கள் (பச்சை = சுருக்கத்தில் உள்ளன)</div>' +
        (kw_chips if kw_chips else '<span style="font-size:.72rem;color:#7a8a99;font-family:Noto Sans Tamil,sans-serif;">தமிழ் உரை இல்லை</span>') +
        f'</div>' +
        f'<div style="background:#f5f7fa;border:1px solid #e8ecf1;border-left:4px solid #e07b00;padding:.55rem .8rem;margin-top:.5rem;font-size:.74rem;color:#3a4a5a;font-family:Noto Sans Tamil,sans-serif;line-height:1.6;">' +
        f'{summary_note}</div>' +
        f'</div></div>'
    )

for k,v in [("blocks",[]),("sel_word",""),("meaning",None),
            ("history",[]),("fname",""),("paste_blocks",[]),
            ("summary_text",""),("summary_metrics",None),
            ("summary_method",""),("summary_generated",False)]:
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

st.markdown("""
<div class="gov-topstrip">
  <div>🇮🇳 தமிழ்நாடு அரசு · Government of Tamil Nadu · India</div>
  <div class="gov-topstrip-links">
    <span>30 மார்ச் 2026</span>
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
        ஆவண வாசிப்பு · சொல் பொருள் தேடல் · தமிழ் சுருக்கம் · 4-நிலை அமைப்பு |
        Document Reader · Word Meaning · Tamil Summarization · 4-Tier Engine
      </div>
    </div>
  </div>
  <div class="gov-header-badges">
    <div class="gov-badge"><span class="gov-badge-dot"></span>LIVE SYSTEM</div>
    <div class="gov-badge"> TN GOVT</div>
    <div class="gov-badge"> SECURE</div>
  </div>
</div>
<div class="gov-nav">
  <a class="gov-nav-item active"> முகப்பு</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> ஆவண வாசிப்பு</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> சொல் தேடல்</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> சுருக்கம்</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> அகராதி</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> புள்ளிவிவரம்</a><span class="gov-nav-sep">|</span>
  <a class="gov-nav-item"> உதவி</a>
</div>
<div class="gov-breadcrumb">
  <span class="gov-bc-link">முகப்பு</span> ›
  <span class="gov-bc-link">சேவைகள்</span> ›
  <span>தமிழ் மொழி உதவியாளர்</span>
</div>
<div class="tn-ticker">
  <span class="tn-ticker-label"> அறிவிப்பு</span>
  <span class="tn-ticker-content">
    தமிழ் சொற்களை கிளிக் செய்து பொருள் காணுங்கள் &nbsp;·&nbsp;
    PDF, DOCX, TXT கோப்புகளை பதிவேற்றவும் &nbsp;·&nbsp;
    புதுமை: தமிழ் சுருக்கம் + மதிப்பீட்டு அமைப்பு இப்போது கிடைக்கிறது &nbsp;·&nbsp;
    ROUGE மதிப்பீடு · முக்கிய சொல் உள்ளடக்கம் · அமுக்க விகிதம் &nbsp;·&nbsp;
    Click any underlined Tamil word to see meaning &nbsp;·&nbsp;
    NEW: Tamil Summarization with Evaluation Metrics now available &nbsp;·&nbsp;
    4-நிலை பொருள் தேடல் அமைப்பு இப்போது கிடைக்கிறது &nbsp;·&nbsp;
    தமிழ்நாடு அரசு சேவை — Government of Tamil Nadu Service
  </span>
</div>
""", unsafe_allow_html=True)

col_l, col_c, col_r = st.columns([2, 5, 3], gap="small")

with col_l:
    st.markdown('<div class="gov-sidebar-head"> உயிர் எழுத்துக்கள்</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="gov-sidebar-head">மெய் எழுத்துக்கள்</div>', unsafe_allow_html=True)
    st.markdown('<div class="gov-sidebar-body">', unsafe_allow_html=True)
    ccols = st.columns(6)
    for i, letter in enumerate(TAMIL_CONSONANTS[:18]):
        with ccols[i % 6]:
            if st.button(letter, key=f"c_{letter}"):
                st.session_state.sel_word = letter
                st.session_state.meaning  = lookup(letter)
    st.markdown('</div>', unsafe_allow_html=True)

    all_text = " ".join(b["text"] for b in st.session_state.blocks)
    tw_all   = [clean_word(t) for t in all_text.split() if is_tamil_word(t)]
    tw_uniq  = list(dict.fromkeys(w for w in tw_all if w))
    in_dict  = sum(1 for w in tw_uniq if tier2_json(w))

    st.markdown(f"""
    <div class="gov-sidebar-head"> ஆவண புள்ளிவிவரம்</div>
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

    if st.session_state.summary_generated and st.session_state.summary_metrics:
        m = st.session_state.summary_metrics
        st.markdown(f"""
        <div class="gov-sidebar-head"> சுருக்க புள்ளிவிவரம்</div>
        <div class="gov-sidebar-body">
          <div class="gov-stat-row">
            <span class="gov-stat-label">ஒட்டுமொத்த மதிப்பெண்</span>
            <span class="gov-stat-val">{m['overall']:.0f}/100</span>
          </div>
          <div class="gov-stat-row">
            <span class="gov-stat-label">ROUGE-1</span>
            <span class="gov-stat-val">{m['rouge_1']:.1f}%</span>
          </div>
          <div class="gov-stat-row">
            <span class="gov-stat-label">ROUGE-2</span>
            <span class="gov-stat-val">{m['rouge_2']:.1f}%</span>
          </div>
          <div class="gov-stat-row">
            <span class="gov-stat-label">அமுக்க விகிதம்</span>
            <span class="gov-stat-val">{m['compression_ratio']:.0f}%</span>
          </div>
          <div class="gov-stat-row">
            <span class="gov-stat-label">சொல் உள்ளடக்கம்</span>
            <span class="gov-stat-val">{m['keyword_coverage']:.0f}%</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-sidebar-head"> பயன்பாட்டு முறை</div>
    <div class="gov-sidebar-body">
      <div class="gov-infobox">
        PDF / DOCX / TXT பதிவேற்றவும்<br>
        தமிழ் சொல்லை கிளிக் செய்யவும்<br>
        சுருக்கம் தாவலில் சுருக்கம் காணுங்கள்<br>
        ROUGE மதிப்பீடு தானாக காட்டும்<br>
        உரையையும் ஒட்டலாம்
      </div>
      <div class="gov-warnbox">
         அரசு ஆவணங்களை பாதுகாப்பாக பதிவேற்றவும். இந்த சேவை இலவசம்.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-sidebar-head">தமிழ்நாடு சின்னங்கள்</div>
    <div class="gov-sidebar-body">
      <div class="gov-stat-row"><span class="gov-stat-label"> மலர்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">கொன்றை</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label"> பறவை</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">மரங்கொத்தி</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label"> மரம்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">பனை மரம்</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label"> விலங்கு</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">நீலகிரி தார்</span></div>
      <div class="gov-stat-row"><span class="gov-stat-label"> மீன்</span><span class="gov-stat-val" style="font-family:'Noto Sans Tamil',sans-serif">இந்திய கணவாய்</span></div>
      <div style="text-align:center;margin-top:.7rem;padding:.5rem;background:#e8f0fa;border-radius:2px">
        <div style="font-family:'Noto Serif Tamil',serif;font-size:1.15rem;color:#003366;font-weight:700">செந்தமிழ் வாழ்க!</div>
        <div style="font-size:.68rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif;margin-top:.15rem">தமிழ் மொழி எப்போதும் வாழட்டும்</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    tab_upload, tab_paste, tab_summary = st.tabs([
        " ஆவணம் பதிவேற்று | Upload",
        " உரை ஒட்டு | Paste",
        " தமிழ் சுருக்கம் | Summarize",
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
                    st.session_state.blocks           = blocks
                    st.session_state.fname            = uploaded.name
                    st.session_state.sel_word         = ""
                    st.session_state.meaning          = None
                    st.session_state.paste_blocks     = []
                    st.session_state.summary_text     = ""
                    st.session_state.summary_metrics  = None
                    st.session_state.summary_generated= False

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
                <span class="gov-doc-filename">{uploaded.name}</span>
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
               அடிக்கோடிட்ட தமிழ் சொற்களை கிளிக் செய்யவும் · "சுருக்கம்" தாவலில் சுருக்கம் காணுங்கள்
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem 2rem;background:white;
                        border:1px dashed #c5cdd8;border-top:3px solid #003366;margin-top:.5rem">
              <div style="font-size:2.8rem;margin-bottom:.8rem"></div>
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
        if st.button(" உரையை படி | Read Text", key="paste_btn"):
            if pasted.strip():
                blocks = [{"type":"para","text":l.strip()} for l in pasted.strip().splitlines() if l.strip()]
                st.session_state.paste_blocks     = blocks
                st.session_state.blocks           = blocks
                st.session_state.fname            = "ஒட்டிய உரை"
                st.session_state.sel_word         = ""
                st.session_state.meaning          = None
                st.session_state.summary_text     = ""
                st.session_state.summary_metrics  = None
                st.session_state.summary_generated= False

        if st.session_state.paste_blocks:
            pb  = st.session_state.paste_blocks
            pt  = " ".join(b["text"] for b in pb)
            ptw = list(dict.fromkeys(clean_word(t) for t in pt.split() if is_tamil_word(t)))
            st.markdown(f"""
            <div class="stats-grid">
              <div class="stat-box"><span class="stat-num">{len(pb)}</span><span class="stat-lbl">வரிகள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(pt.split())}</span><span class="stat-lbl">மொத்த சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{len(ptw)}</span><span class="stat-lbl">தமிழ் சொற்கள்</span></div>
              <div class="stat-box"><span class="stat-num">{sum(1 for w in ptw if tier2_json(w))}</span><span class="stat-lbl">அகராதியில்</span></div>
            </div>
            <div class="gov-doc-card">
              <div class="gov-doc-titlebar">
                <span class="gov-doc-filename"> ஒட்டிய உரை | Pasted Text</span>
                <span class="gov-doc-meta">{len(ptw)} தமிழ் சொற்கள்</span>
              </div>
              <div class="gov-doc-body">
                <div class="doc-content">{blocks_to_html(pb)}</div>
              </div>
            </div>
            <div style="text-align:center;margin-top:.4rem;font-size:.72rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif">
               தமிழ் சொற்களை கிளிக் செய்யவும் · "சுருக்கம்" தாவலில் சுருக்கம் உருவாக்குங்கள்
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_summary:
        st.markdown('<div style="margin-top:.5rem">', unsafe_allow_html=True)
        source_text = "\n".join(b["text"] for b in st.session_state.blocks)
        tamil_words_in_doc = [clean_word(w) for w in source_text.split() if is_tamil_word(w)]

        if not source_text.strip():
            st.markdown("""
            <div style="text-align:center;padding:2.5rem 1.5rem;background:white;
                        border:1px dashed #c5cdd8;border-top:3px solid #1a6b2e;margin-top:.5rem">
              <div style="font-size:2.4rem;margin-bottom:.7rem">📝</div>
              <div style="font-family:'Noto Serif Tamil',serif;font-size:1.1rem;color:#003366;font-weight:700;margin-bottom:.4rem">
                முதலில் ஆவணம் பதிவேற்றுங்கள்
              </div>
              <div style="font-size:.82rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif;">
                "பதிவேற்று" அல்லது "ஒட்டு" தாவலில் உரை சேர்த்த பின் இங்கே வாருங்கள்.<br>
                Upload or paste text first, then come here to summarize.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
            with ctrl1:
                summ_method = st.selectbox(
                    "சுருக்க முறை | Method",
                    options=["hybrid", "tfidf", "position", "abstractive_ai"],
                    format_func=lambda x: {
                        "hybrid":        " Hybrid (TF-IDF + Position)",
                        "tfidf":         " TF-IDF மட்டும்",
                        "position":      " நிலை அடிப்படையில்",
                        "abstractive_ai":" AI சுருக்கம் (Claude)",
                    }[x],
                    key="summ_method_sel",
                    label_visibility="visible",
                )
            with ctrl2:
                if summ_method == "abstractive_ai":
                    summ_length = st.selectbox(
                        "நீளம் | Length",
                        options=["short","medium","long"],
                        format_func=lambda x: {"short":"குறுகிய (2–3 வாக்கியம்)",
                                               "medium":"நடுத்தர (4–6 வாக்கியம்)",
                                               "long":"நீண்ட (8–10 வாக்கியம்)"}[x],
                        index=1, key="summ_len_sel", label_visibility="visible",
                    )
                else:
                    summ_ratio = st.slider(
                        "சுருக்க விகிதம் | Compression ratio",
                        min_value=10, max_value=70, value=40, step=5,
                        format="%d%%", key="summ_ratio_sl", label_visibility="visible",
                    )
            with ctrl3:
                st.markdown("<div style='margin-top:1.6rem'>", unsafe_allow_html=True)
                run_btn = st.button("▶ சுருக்கு | Summarize", key="run_summary_btn")
                st.markdown("</div>", unsafe_allow_html=True)

            if run_btn:
                with st.spinner("சுருக்கம் உருவாக்குகிறது… | Generating summary…"):
                    if summ_method == "abstractive_ai":
                        summ_out = abstractive_summarize_ai(source_text, length_hint=summ_length)
                        if summ_out:
                            st.session_state.summary_text    = summ_out
                            st.session_state.summary_method  = "🤖 AI சுருக்கம் (Claude)"
                            st.session_state.summary_metrics = evaluate_summary(
                                source_text, summ_out, "AI Abstractive"
                            )
                            st.session_state.summary_generated = True
                        else:
                            st.error("AI சுருக்கம் தோல்வியடைந்தது. Extractive முறையை முயற்சிக்கவும்.")
                    else:
                        ratio = summ_ratio / 100.0
                        summ_out, sel_idx, _ = extractive_summarize(source_text, ratio=ratio, method=summ_method)
                        method_labels = {
                            "hybrid":   "Hybrid Extractive",
                            "tfidf":    "TF-IDF Extractive",
                            "position": "Position-based Extractive",
                        }
                        st.session_state.summary_text    = summ_out
                        st.session_state.summary_method  = method_labels.get(summ_method, summ_method)
                        st.session_state.summary_metrics = evaluate_summary(
                            source_text, summ_out, method_labels.get(summ_method,"")
                        )
                        st.session_state.summary_generated = True

            if st.session_state.summary_generated and st.session_state.summary_text:
                summ_wc   = len(st.session_state.summary_text.split())
                orig_wc   = len(source_text.split())
                cr_display= round((1 - summ_wc / orig_wc) * 100) if orig_wc else 0

                st.markdown(f"""
                <div class="stats-grid" style="margin-top:.7rem">
                  <div class="stat-box"><span class="stat-num">{orig_wc:,}</span><span class="stat-lbl">மூல சொற்கள்</span></div>
                  <div class="stat-box"><span class="stat-num">{summ_wc:,}</span><span class="stat-lbl">சுருக்க சொற்கள்</span></div>
                  <div class="stat-box" style="border-top-color:#1a6b2e"><span class="stat-num" style="color:#1a6b2e">{cr_display}%</span><span class="stat-lbl">அமுக்கம்</span></div>
                  <div class="stat-box" style="border-top-color:#e07b00">
                    <span class="stat-num" style="color:#e07b00">
                      {st.session_state.summary_metrics['overall']:.0f}
                    </span>
                    <span class="stat-lbl">மதிப்பெண் /100</span>
                  </div>
                </div>

                <div class="sum-card">
                  <div class="sum-titlebar">
                    <span>தமிழ் சுருக்கம் | Tamil Summary</span>
                    <span style="font-size:.68rem;color:#b8ddc4">{st.session_state.summary_method}</span>
                  </div>
                  <div class="sum-body">
                    <span class="sum-method-badge">✓ {st.session_state.summary_method}</span>
                    <div style="font-family:'Noto Sans Tamil',sans-serif;font-size:1.02rem;line-height:2.1;color:var(--tn-text)">
                      {st.session_state.summary_text}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.session_state.summary_metrics:
                    st.markdown(render_metrics_panel(st.session_state.summary_metrics),
                                unsafe_allow_html=True)
                if summ_method != "abstractive_ai":
                    st.markdown('<div style="margin-top:.6rem">', unsafe_allow_html=True)
                    if st.button("அனைத்து முறைகளையும் ஒப்பிடு | Compare All Extractive Methods",
                                 key="compare_btn"):
                        with st.spinner("ஒப்பீடு செய்கிறது…"):
                            ratio_c = summ_ratio / 100.0
                            methods = [("hybrid","Hybrid"),("tfidf","TF-IDF"),("position","Position")]
                            compare_rows = ""
                            for m_key, m_lbl in methods:
                                s_out, _, _ = extractive_summarize(source_text, ratio=ratio_c, method=m_key)
                                ev = evaluate_summary(source_text, s_out, m_lbl)
                                gl, gc = grade_score(ev["overall"])
                                compare_rows += f"""
                                <tr style="font-family:'Noto Sans Tamil',sans-serif;font-size:.75rem">
                                  <td style="padding:.4rem .6rem;font-weight:600">{m_lbl}</td>
                                  <td style="padding:.4rem .6rem;text-align:center">{ev['rouge_1']:.1f}%</td>
                                  <td style="padding:.4rem .6rem;text-align:center">{ev['rouge_2']:.1f}%</td>
                                  <td style="padding:.4rem .6rem;text-align:center">{ev['rouge_l']:.1f}%</td>
                                  <td style="padding:.4rem .6rem;text-align:center">{ev['keyword_coverage']:.0f}%</td>
                                  <td style="padding:.4rem .6rem;text-align:center">{ev['compression_ratio']:.0f}%</td>
                                  <td style="padding:.4rem .6rem;text-align:center;font-weight:700;color:var(--tn-navy)">{ev['overall']:.0f}</td>
                                  <td style="padding:.4rem .6rem;text-align:center">
                                    <span style="font-size:.65rem;padding:.12rem .38rem;border-radius:2px;font-weight:600;
                                      background:{'#d4edda' if ev['overall']>=75 else '#d1ecf1' if ev['overall']>=55 else '#fff3cd' if ev['overall']>=35 else '#f8d7da'};
                                      color:{'#155724' if ev['overall']>=75 else '#0c5460' if ev['overall']>=55 else '#856404' if ev['overall']>=35 else '#721c24'}">
                                      {gl}
                                    </span>
                                  </td>
                                </tr>"""
                            st.markdown(f"""
                            <div class="metrics-panel" style="margin-top:.5rem">
                              <div class="metrics-head">முறை ஒப்பீடு | Method Comparison</div>
                              <div style="overflow-x:auto">
                              <table style="width:100%;border-collapse:collapse;font-size:.75rem">
                                <thead>
                                  <tr style="background:var(--tn-gray1);font-family:'Noto Sans Tamil',sans-serif;font-size:.66rem;text-transform:uppercase;letter-spacing:.04em;color:var(--tn-text2)">
                                    <th style="padding:.4rem .6rem;text-align:left">முறை</th>
                                    <th style="padding:.4rem .6rem">ROUGE-1</th>
                                    <th style="padding:.4rem .6rem">ROUGE-2</th>
                                    <th style="padding:.4rem .6rem">ROUGE-L</th>
                                    <th style="padding:.4rem .6rem">KW Cov.</th>
                                    <th style="padding:.4rem .6rem">Compress</th>
                                    <th style="padding:.4rem .6rem">Score</th>
                                    <th style="padding:.4rem .6rem">Grade</th>
                                  </tr>
                                </thead>
                                <tbody>{compare_rows}</tbody>
                              </table>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif not run_btn:
                st.markdown("""
                <div style="text-align:center;padding:2rem 1rem;background:white;
                            border:1px solid #c5cdd8;border-top:3px solid #1a6b2e;margin-top:.7rem">
                  <div style="font-size:2rem;margin-bottom:.6rem"></div>
                  <div style="font-family:'Noto Serif Tamil',serif;font-size:1rem;color:#003366;font-weight:700;margin-bottom:.3rem">
                    சுருக்க முறையை தேர்வு செய்யுங்கள்
                  </div>
                  <div style="font-size:.78rem;color:#7a8a99;font-family:'Noto Sans Tamil',sans-serif;line-height:1.7">
                    Hybrid · TF-IDF · Position-based · AI (Claude) ஆகிய முறைகளில் தேர்ந்தெடுங்கள்.<br>
                    சுருக்கத்திற்கு பின் ROUGE மதிப்பீடு தானாக காட்டும்.
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="gov-meaning-head"> சொல் பொருள் | Word Meaning</div>', unsafe_allow_html=True)

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
          <div class="panel-idle-icon"></div>
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

    st.markdown('<div style="margin-top:.6rem"><div class="gov-search-label">அகராதி | Dictionary Browse</div></div>', unsafe_allow_html=True)
    if TDICT:
        letters = sorted({w[0] for w in TDICT if w})
        pick_l  = st.selectbox("எழுத்தால் தேடு", ["எல்லாம்"] + letters,
                               key="browse_letter", label_visibility="collapsed")
        filtered = {k:v for k,v in TDICT.items() if pick_l=="எல்லாம்" or k.startswith(pick_l)}
        st.caption(f"{len(filtered):,} சொற்கள்")
        for wk, wd in list(filtered.items())[:6]:
            en = wd.get("english","")[:35]
            with st.expander(f"{wk} — {en}"):
                st.markdown(meaning_card_html(wk,{**wd,"tier":2,"label":" உள்ளக அகராதி"}),
                            unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
st.markdown("""
<div class="gov-footer">
  <div>
    © 2026 தமிழ்நாடு அரசு | Government of Tamil Nadu · All Rights Reserved<br>
    <span style="color:#556677">
      தமிழ் மொழி உதவியாளர் v4.0 · 4-நிலை பொருள் தேடல் · தமிழ் சுருக்கம் · ROUGE மதிப்பீடு ·
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
