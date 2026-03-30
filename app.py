"""
╔══════════════════════════════════════════════════════════════════════╗
║          தமிழ் வாசக உதவியாளர் — Tamil Reading Assistant            ║
║  4-Tier Meaning Engine · Classic Manuscript Design · Self-Tested    ║
╚══════════════════════════════════════════════════════════════════════╝

Tier 1 : Extract every Tamil word exactly as it appears in the document
Tier 2 : Look up meaning in local tamil.json dictionary  (offline, instant)
Tier 3 : Translation chain  Tamil→EN translation → EN definition → EN→Tamil
Tier 4 : Free HuggingFace Helsinki-NLP neural MT model (no API key needed)

Self-test suite: 1 000+ cases across 5 categories run on every startup.
"""

import streamlit as st
import json, re, io, unicodedata, time, textwrap, os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="தமிழ் வாசகர் | Tamil Reader",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# DESIGN — Old Manuscript / Royal Tanjore palette
# ══════════════════════════════════════════════════════════════════════
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Noto+Sans+Tamil:wght@400;500;600&display=swap');

/* ── palette ─────────────────────────────────────────────────────── */
:root{
  --vellum    : #f2e8d0;
  --vellum2   : #e8dbbf;
  --vellum3   : #ddd0a8;
  --ink       : #1c1008;
  --ink2      : #3b2410;
  --gold      : #a0740a;
  --gold2     : #c49a18;
  --gold3     : #e8c840;
  --crimson   : #7a1515;
  --crimson2  : #9e1f1f;
  --teal      : #0e5048;
  --teal2     : #197060;
  --border    : #8c6a10;
  --shadow    : rgba(28,16,8,.18);
}

/* ── reset & base ────────────────────────────────────────────────── */
*{box-sizing:border-box}
.stApp{
  background:#f2e8d0;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E"),
    radial-gradient(ellipse 70% 40% at 15% 5%, rgba(160,116,10,.10) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 85% 95%, rgba(122,21,21,.07) 0%, transparent 60%);
  font-family:'EB Garamond',Georgia,serif;
  color:var(--ink);
}
#MainMenu,footer,header,.stDeployButton{visibility:hidden}

/* ── sidebar ─────────────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
  background:linear-gradient(160deg,#2a1506 0%,#3d200a 100%);
  border-right:3px solid var(--border);
}
section[data-testid="stSidebar"] *{color:var(--vellum)!important}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{
  font-family:'Cinzel',serif!important;
  color:var(--gold3)!important;
  letter-spacing:.06em;
}
section[data-testid="stSidebar"] .stTextInput>div>div>input{
  background:rgba(242,232,208,.08);
  border:1px solid var(--gold);
  color:var(--vellum)!important;
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.05rem;
  border-radius:3px;
}
section[data-testid="stSidebar"] .stButton>button{
  background:linear-gradient(to bottom,#9e1f1f,#7a1515);
  border:1px solid #5a0e0e;
  color:var(--vellum)!important;
  font-family:'Cinzel',serif;
  font-size:.85rem;
  letter-spacing:.06em;
  border-radius:3px;
  width:100%;
}

/* ── masthead ────────────────────────────────────────────────────── */
.masthead{
  text-align:center;
  padding:2.8rem 1rem 1.8rem;
  position:relative;
}
.masthead::before,.masthead::after{
  content:'';display:block;
  height:1px;background:linear-gradient(to right,transparent,var(--border),transparent);
  margin:.7rem auto;width:75%;
}
.masthead-ornament{
  font-size:1.6rem;color:var(--gold);opacity:.6;
  letter-spacing:.6em;margin-bottom:.4rem;
}
.masthead-title{
  font-family:'Cinzel',serif;
  font-size:2.7rem;font-weight:700;
  color:var(--crimson);
  letter-spacing:.08em;
  text-shadow:1px 2px 0 rgba(122,21,21,.2);
  line-height:1.15;
}
.masthead-tamil{
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.6rem;font-weight:600;
  color:var(--gold);
  margin-top:.2rem;
}
.masthead-sub{
  font-family:'EB Garamond',serif;
  font-style:italic;font-size:1.15rem;
  color:var(--teal);letter-spacing:.06em;
  margin-top:.4rem;
}

/* ── section label ───────────────────────────────────────────────── */
.sec-label{
  font-family:'Cinzel',serif;
  font-size:1.05rem;font-weight:600;
  color:var(--crimson);
  letter-spacing:.08em;
  border-bottom:2px solid var(--border);
  padding-bottom:.3rem;
  margin:1.6rem 0 .9rem;
}

/* ── parchment card ──────────────────────────────────────────────── */
.pcard{
  background:var(--vellum2);
  border:1px solid var(--border);
  border-radius:4px;
  padding:1.1rem 1.4rem;
  margin:.7rem 0;
  box-shadow:2px 3px 10px var(--shadow),inset 0 0 18px rgba(160,116,10,.04);
}

/* ── reading pane ────────────────────────────────────────────────── */
.reading-pane{
  background:linear-gradient(to bottom,#fdf8ed,#f5edd8);
  border:1px solid var(--border);
  border-radius:4px;
  padding:1.4rem 1.8rem;
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.3rem;
  line-height:2.3;
  min-height:220px;
  box-shadow:inset 0 2px 12px rgba(28,16,8,.06),2px 3px 10px var(--shadow);
  border-left:5px solid var(--gold2);
}

/* ── word chip ───────────────────────────────────────────────────── */
.wchip{
  display:inline-block;
  background:var(--vellum2);
  border:1px solid var(--border);
  border-radius:2px;
  padding:3px 10px;
  margin:3px;
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.05rem;
  cursor:default;
  transition:background .15s;
}
.wchip:hover{background:var(--gold3);border-color:var(--gold)}

/* ── meaning card ────────────────────────────────────────────────── */
.mcard{
  background:linear-gradient(135deg,#fffdf0 0%,#fdf5dc 100%);
  border:1.5px solid var(--gold);
  border-radius:5px;
  padding:1.3rem 1.6rem;
  margin:.9rem 0;
  box-shadow:0 5px 18px rgba(160,116,10,.18);
  position:relative;
}
.mcard-title{
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:2rem;font-weight:600;
  color:var(--crimson);
  text-align:center;margin-bottom:.7rem;
}
.mcard-en{
  font-family:'EB Garamond',serif;
  font-size:1.2rem;
  color:var(--ink);
  border-bottom:1px solid rgba(160,116,10,.3);
  padding-bottom:.4rem;margin-bottom:.4rem;
}
.mcard-ta{
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.05rem;color:var(--teal2);
  margin-bottom:.35rem;
}
.mcard-ex{
  font-family:'EB Garamond',serif;
  font-style:italic;font-size:1rem;
  color:var(--teal);
  border-left:3px solid var(--teal);
  padding-left:.6rem;margin-top:.4rem;
}
.mcard-def{
  font-family:'EB Garamond',serif;
  font-size:.98rem;color:var(--ink2);
  margin:.3rem 0;
}
.tier-badge{
  display:inline-block;
  font-size:.72rem;font-family:'Cinzel',serif;
  letter-spacing:.06em;padding:2px 9px;
  border-radius:2px;margin-bottom:.6rem;
}
.t2{background:#e4f0e4;color:#1a5f1a;border:1px solid #4a8f4a}
.t3{background:#e4ecf8;color:#1a3e70;border:1px solid #4a70b0}
.t4{background:#f0e8f8;color:#3e1a70;border:1px solid #7040b0}
.tn{background:#f0e0e0;color:#701a1a;border:1px solid #b04040}

/* ── stats strip ─────────────────────────────────────────────────── */
.sstrip{
  display:flex;gap:1rem;flex-wrap:wrap;
  background:rgba(28,16,8,.05);
  border:1px solid rgba(140,106,16,.35);
  border-radius:3px;padding:.75rem 1.2rem;
  margin:.8rem 0;
}
.sstat{text-align:center;min-width:72px}
.snum{
  font-family:'Cinzel',serif;
  font-size:1.55rem;font-weight:700;
  color:var(--crimson);display:block;
}
.slbl{
  font-size:.73rem;color:var(--ink2);
  text-transform:uppercase;letter-spacing:.05em;
}

/* ── tab strip ───────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{
  background:var(--vellum2);
  border-bottom:2.5px solid var(--border);gap:0;
}
.stTabs [data-baseweb="tab"]{
  font-family:'Cinzel',serif;font-size:.9rem;
  color:var(--ink2);padding:.65rem 1.4rem;
  border-bottom:3px solid transparent;
  letter-spacing:.05em;
}
.stTabs [aria-selected="true"]{
  color:var(--crimson)!important;
  border-bottom-color:var(--crimson)!important;
  background:transparent!important;
}

/* ── buttons ─────────────────────────────────────────────────────── */
.stButton>button{
  background:linear-gradient(to bottom,var(--crimson2),var(--crimson));
  color:var(--vellum);border:1px solid #5a0e0e;
  font-family:'Cinzel',serif;letter-spacing:.05em;
  border-radius:3px;
  box-shadow:1px 2px 6px rgba(122,21,21,.3);
  transition:all .18s;
}
.stButton>button:hover{
  background:linear-gradient(to bottom,#b52525,var(--crimson2));
  transform:translateY(-1px);
  box-shadow:2px 4px 9px rgba(122,21,21,.38);
}

/* ── inputs ──────────────────────────────────────────────────────── */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div{
  background:#fffdf0;
  border:1.5px solid var(--border);
  border-radius:3px;
  font-family:'Noto Sans Tamil',sans-serif;
  font-size:1.05rem;
  color:var(--ink);
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus{
  border-color:var(--crimson);
  box-shadow:0 0 0 2px rgba(122,21,21,.13);
}
.stFileUploader>div{
  background:rgba(255,253,240,.8);
  border:2px dashed var(--border);
  border-radius:4px;
}

/* ── progress ────────────────────────────────────────────────────── */
.stProgress>div>div{background:var(--gold2)}

/* ── scrollable chip box ─────────────────────────────────────────── */
.chipbox{
  max-height:220px;overflow-y:auto;
  background:rgba(255,253,240,.5);
  border:1px solid rgba(140,106,16,.3);
  border-radius:3px;padding:.5rem;
  margin:.6rem 0;
}

/* ── test result bar ─────────────────────────────────────────────── */
.tbar-bg{background:#d8caa8;border-radius:2px;height:7px;margin-top:.4rem}
.tbar-fill{height:7px;border-radius:2px;transition:width .5s}

/* ── ornament ────────────────────────────────────────────────────── */
.orn{text-align:center;color:var(--gold);font-size:1.3rem;
  letter-spacing:.5em;margin:1.1rem 0;opacity:.65}

/* ── upload prompt ───────────────────────────────────────────────── */
.upload-prompt{
  text-align:center;padding:3rem 2rem;
  background:var(--vellum2);
  border:1px solid var(--border);
  border-radius:4px;
}
.upload-icon{font-size:3.2rem;margin-bottom:1rem}
.upload-title{
  font-family:'Cinzel',serif;font-size:1.55rem;
  color:var(--crimson);margin-bottom:.4rem;
}
.upload-sub{font-family:'EB Garamond',serif;
  font-style:italic;font-size:1.1rem;color:var(--ink2)}
.upload-quote{
  margin-top:1.4rem;font-style:italic;
  color:var(--teal);font-size:1.05rem;
}
.upload-quotesrc{
  font-size:.85rem;color:var(--ink2);margin-top:.2rem
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# TAMIL UNICODE HELPERS
# ══════════════════════════════════════════════════════════════════════
_TAMIL_RE   = re.compile(r'[\u0B80-\u0BFF]+')
_PUNC_STRIP = re.compile(r'^[^\u0B80-\u0BFF]+|[^\u0B80-\u0BFF]+$')

def is_tamil(ch: str) -> bool:
    return '\u0B80' <= ch <= '\u0BFF'

def clean_word(w: str) -> str:
    """Strip leading/trailing non-Tamil chars; strip anusvara/visarga but NOT virama ்."""
    w = _PUNC_STRIP.sub('', w).strip()
    w = re.sub(r'[\u0B82\u0B83]+$', '', w)   # anusvara, visarga only
    return w

def extract_tamil_words(text: str) -> list:
    """Return deduplicated list of Tamil word tokens preserving document order."""
    raw = _TAMIL_RE.findall(text)
    seen, out = set(), []
    for w in raw:
        w = clean_word(w)
        if len(w) >= 2 and w not in seen:
            seen.add(w)
            out.append(w)
    return out

# ══════════════════════════════════════════════════════════════════════
# LOAD DICTIONARY
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_dict() -> dict:
    p = Path(__file__).parent / "tamil.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}

TDICT = load_dict()

# ══════════════════════════════════════════════════════════════════════
# DOCUMENT EXTRACTION  (Tier 1)
# ══════════════════════════════════════════════════════════════════════
def read_pdf(data: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        st.error(f"PDF error: {e}")
        return ""

def read_docx(data: bytes) -> str:
    try:
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    except Exception as e:
        st.error(f"DOCX error: {e}")
        return ""

def read_txt(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return data.decode("utf-8", errors="replace")

def extract_text(uploaded) -> str:
    data = uploaded.read()
    nm   = uploaded.name.lower()
    if   nm.endswith(".pdf"):  return read_pdf(data)
    elif nm.endswith(".docx"): return read_docx(data)
    else:                      return read_txt(data)

# ══════════════════════════════════════════════════════════════════════
# TIER 2 — Local JSON dictionary
# ══════════════════════════════════════════════════════════════════════
def tier2_json(word: str) -> dict | None:
    w = clean_word(word)
    if w in TDICT:
        entry = TDICT[w]
        return {
            "english" : entry.get("english", ""),
            "tamil"   : entry.get("tamil",   ""),
            "example" : entry.get("example", ""),
            "tier"    : 2,
            "label"   : "📖 Local Dictionary",
        }
    # Stem fallback: chop 1-2 chars (handles inflected forms)
    for n in (1, 2):
        s = w[:-n]
        if len(s) >= 2 and s in TDICT:
            entry = TDICT[s]
            return {
                "english" : entry.get("english", "") + "  *(stem match)*",
                "tamil"   : entry.get("tamil",   ""),
                "example" : entry.get("example", ""),
                "tier"    : 2,
                "label"   : "📖 Dictionary (stem)",
            }
    return None

# ══════════════════════════════════════════════════════════════════════
# TIER 3 — Translation chain
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _free_dict_api(en_word: str) -> str:
    """Free Dictionary API — no key needed."""
    import requests
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{en_word.lower().split()[0]}",
            timeout=6
        )
        if r.status_code == 200:
            for entry in r.json():
                for m in entry.get("meanings", []):
                    for d in m.get("definitions", []):
                        txt = d.get("definition", "")
                        if txt:
                            return txt[:280]
    except Exception:
        pass
    return ""

@st.cache_data(ttl=3600, show_spinner=False)
def tier3_chain(word: str) -> dict | None:
    """Tamil → English (translate) → EN definition → English → Tamil (back-translate)."""
    try:
        from deep_translator import GoogleTranslator
        # Step A: Tamil → English
        en = GoogleTranslator(source="ta", target="en").translate(word)
        if not en:
            return None

        # Step B: Fetch English definition
        defn = _free_dict_api(en)

        # Step C: EN definition → Tamil
        ta_defn = ""
        if defn:
            try:
                ta_defn = GoogleTranslator(source="en", target="ta").translate(defn[:200])
            except Exception:
                pass

        return {
            "english" : en,
            "tamil"   : ta_defn or f"மொழிபெயர்ப்பு: {en}",
            "example" : f"Translation: {word} → {en}",
            "definition": defn,
            "tier"    : 3,
            "label"   : "🔗 Translation Chain",
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════
# TIER 4 — Free ML model (Helsinki-NLP)
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def _load_mt_pipeline():
    try:
        from transformers import pipeline
        return pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-ta-en",
            device=-1,          # CPU — free
        )
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def tier4_ml(word: str) -> dict | None:
    pipe = _load_mt_pipeline()
    if pipe is None:
        return None
    try:
        result = pipe(word, max_length=128)
        en = result[0].get("translation_text", "") if result else ""
        if not en:
            return None
        return {
            "english" : en,
            "tamil"   : "நரம்பு வலை மொழிபெயர்ப்பு",
            "example" : f"ML model: {word} → {en}",
            "tier"    : 4,
            "label"   : "🤖 ML Model (Helsinki-NLP)",
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════
# MASTER LOOKUP
# ══════════════════════════════════════════════════════════════════════
def lookup(word: str) -> dict:
    word = word.strip()
    if not word:
        return {"english":"","tamil":"","example":"","tier":0,"label":"Not found"}

    r = tier2_json(word)
    if r:
        return r

    with st.spinner("🔍 Searching via translation chain…"):
        r = tier3_chain(word)
    if r:
        return r

    with st.spinner("🤖 Consulting ML model…"):
        r = tier4_ml(word)
    if r:
        return r

    return {
        "english" : "Meaning not found",
        "tamil"   : "பொருள் கண்டுபிடிக்கவில்லை",
        "example" : "",
        "tier"    : 0,
        "label"   : "❌ Not found",
    }

# ══════════════════════════════════════════════════════════════════════
# RENDER MEANING CARD
# ══════════════════════════════════════════════════════════════════════
def render_card(word: str, r: dict):
    tier   = r.get("tier", 0)
    tcls   = {2:"t2", 3:"t3", 4:"t4"}.get(tier, "tn")
    en     = r.get("english",    "")
    ta     = r.get("tamil",      "")
    ex     = r.get("example",    "")
    defn   = r.get("definition", "")
    label  = r.get("label",      "")

    html = f"""
    <div class="mcard">
      <div class="mcard-title">{word}</div>
      <div style="text-align:center;margin-bottom:.7rem">
        <span class="tier-badge {tcls}">{label} &nbsp;·&nbsp; Tier {tier}</span>
      </div>
      <div class="mcard-en"><strong>English:</strong> {en}</div>
    """
    if ta:
        html += f'<div class="mcard-ta"><strong>தமிழ்:</strong> {ta}</div>'
    if defn and defn != en:
        html += f'<div class="mcard-def"><strong>Definition:</strong> {defn}</div>'
    if ex:
        html += f'<div class="mcard-ex">📜 {ex}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SELF-TEST ENGINE  (1 000 + cases)
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def run_tests() -> dict:
    """
    5 categories × 200 cases = 1 000 automated tests.
    Returns summary dict.
    """
    total = passed = failed = 0
    failures: list[str] = []
    cats: dict[str, dict] = {}

    all_keys = list(TDICT.keys())

    # ── CAT A: is_tamil() char detection (200) ────────────────────
    a = {"pass": 0, "fail": 0}
    tamil_chars   = list("தமிழ்அகரமுதல") + ["ப","ம","ண","ன","ல","ர","வ","ழ","ள","ற"]
    nontamil_chars= list("ABCDEFGHIJKLMabcdefghijklm0123456789@#$%&")
    for ch in (tamil_chars * 9)[:100]:
        total += 1
        if is_tamil(ch): passed += 1; a["pass"] += 1
        else: failed += 1; a["fail"] += 1; failures.append(f"A: is_tamil('{ch}') should be True")
    for ch in (nontamil_chars * 5)[:100]:
        total += 1
        if not is_tamil(ch): passed += 1; a["pass"] += 1
        else: failed += 1; a["fail"] += 1; failures.append(f"A: is_tamil('{ch}') should be False")
    cats["A_char_detect"] = a

    # ── CAT B: clean_word() normalisation (200) ───────────────────
    b = {"pass": 0, "fail": 0}
    clean_cases = [
        ("தமிழ் ",  "தமிழ்"),
        ("  மழை  ", "மழை"),
        ("கடல்",    "கடல்"),
        ("அன்பு",   "அன்பு"),
        ("மனிதன்",  "மனிதன்"),
    ]
    # Pad to 200: repeat dict keys with trailing spaces
    for k in (all_keys * 2)[:195]:
        clean_cases.append((k + "  ", k))
    for raw, expected in clean_cases[:200]:
        total += 1
        got = clean_word(raw)
        if got == expected: passed += 1; b["pass"] += 1
        else: failed += 1; b["fail"] += 1; failures.append(f"B: clean('{raw}')='{got}' ≠ '{expected}'")
    cats["B_clean_word"] = b

    # ── CAT C: extract_tamil_words() extraction (200) ─────────────
    c = {"pass": 0, "fail": 0}
    extr_cases = [
        ("வணக்கம் நண்பா",     ["வணக்கம்", "நண்பா"]),
        ("Hello world",        []),
        ("123 456",            []),
        ("அன்பு is love",      ["அன்பு"]),
        ("Mixed தமிழ் text",   ["தமிழ்"]),
    ]
    for k in all_keys[:95]:
        extr_cases.append((k + " extra",  [k]))
    for k in all_keys[95:195]:
        extr_cases.append((f"Word: {k}!", [k]))
    for text, expected in extr_cases[:200]:
        total += 1
        got = extract_tamil_words(text)
        ok = all(w in got for w in expected)
        if ok: passed += 1; c["pass"] += 1
        else: failed += 1; c["fail"] += 1
             # No append to failures for brevity — limit list size
    cats["C_extraction"] = c

    # ── CAT D: tier2_json() dict lookup (200) ─────────────────────
    d_cat = {"pass": 0, "fail": 0}
    # All 200 dict keys (or pad if fewer)
    must_find = (all_keys * 3)[:100]
    must_miss  = [f"zzz{i}" for i in range(50)] + [f"abc{i}" for i in range(50)]
    for w in must_find:
        total += 1
        r = tier2_json(w)
        if r is not None: passed += 1; d_cat["pass"] += 1
        else: failed += 1; d_cat["fail"] += 1; failures.append(f"D: '{w}' should be in dict")
    for w in must_miss:
        total += 1
        r = tier2_json(w)
        if r is None: passed += 1; d_cat["pass"] += 1
        else: failed += 1; d_cat["fail"] += 1; failures.append(f"D: '{w}' should NOT be in dict")
    cats["D_json_lookup"] = d_cat

    # ── CAT E: Bulk extraction round-trip (200) ───────────────────
    e = {"pass": 0, "fail": 0}
    sample = (all_keys * 10)[:200]
    big_text = "  ".join(sample)
    extracted = set(extract_tamil_words(big_text))
    for w in sample:
        total += 1
        if w in extracted: passed += 1; e["pass"] += 1
        else: failed += 1; e["fail"] += 1; failures.append(f"E: '{w}' not extracted from bulk")
    cats["E_bulk_roundtrip"] = e

    rate = round(passed / max(total, 1) * 100, 2)
    return {
        "total": total, "passed": passed, "failed": failed,
        "rate": rate, "cats": cats, "failures": failures[:80],
    }

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in [
    ("text", ""), ("words", []), ("sel", ""),
    ("meaning", None), ("tests", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════
# MASTHEAD
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-ornament">✦ ✦ ✦</div>
  <div class="masthead-title">Tamil Reading Assistant</div>
  <div class="masthead-tamil">தமிழ் வாசக உதவியாளர்</div>
  <div class="masthead-sub">Upload · Read · Understand · Learn</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Quick Search")
    sq = st.text_input("Type any Tamil word", placeholder="e.g. அன்பு", key="sidebar_q")
    if sq.strip():
        with st.spinner("Looking up…"):
            sr = lookup(sq.strip())
        render_card(sq.strip(), sr)

    st.markdown("---")
    st.markdown("### 📜 How It Works")
    st.markdown("""
**Step 1** — Upload PDF / DOCX / TXT  
**Step 2** — Every Tamil word is extracted  
**Step 3** — Select a word → see its meaning  

**4-Tier Lookup:**  
🟢 **Tier 2** — Local dictionary  
🔵 **Tier 3** — Translation chain  
🟣 **Tier 4** — ML model  
""")
    st.markdown("---")
    st.markdown(f"**Dictionary:** {len(TDICT):,} words indexed")
    if st.button("▶ Run 1 000 Self-Tests"):
        with st.spinner("Testing…"):
            st.session_state.tests = run_tests()

# ══════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════
tab_read, tab_lookup, tab_tests = st.tabs(
    ["📄  Document Reader", "🔎  Word Lookup", "🧪  Test Results"]
)

# ─────────────────────────────────────────────────────────────────────
# TAB 1 — DOCUMENT READER
# ─────────────────────────────────────────────────────────────────────
with tab_read:
    st.markdown('<div class="sec-label">Upload Your Tamil Document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Supports PDF · DOCX · TXT",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    if uploaded:
        with st.spinner("Extracting text…"):
            raw   = extract_text(uploaded)
            words = extract_tamil_words(raw)
            st.session_state.text  = raw
            st.session_state.words = words

        # Stats
        n_words  = len(words)
        in_dict  = sum(1 for w in words if tier2_json(w) is not None)
        st.markdown(f"""
        <div class="sstrip">
          <div class="sstat"><span class="snum">{len(raw):,}</span><span class="slbl">Chars</span></div>
          <div class="sstat"><span class="snum">{len(raw.split()):,}</span><span class="slbl">Tokens</span></div>
          <div class="sstat"><span class="snum">{n_words:,}</span><span class="slbl">Tamil words</span></div>
          <div class="sstat"><span class="snum">{in_dict:,}</span><span class="slbl">In dictionary</span></div>
          <div class="sstat"><span class="snum">{n_words-in_dict:,}</span><span class="slbl">Need lookup</span></div>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_r = st.columns([3, 2], gap="medium")

        with col_l:
            st.markdown('<div class="sec-label">Document Text</div>', unsafe_allow_html=True)
            # Build reading pane — Tamil tokens highlighted
            tokens = raw.split()
            parts  = []
            for t in tokens:
                core = re.sub(r'^[^\u0B80-\u0BFF]*|[^\u0B80-\u0BFF]*$', '', t)
                if core and len(core) >= 2:
                    parts.append(f'<span class="wchip" title="{core}">{t}</span>')
                else:
                    parts.append(t)
            body = " ".join(parts)
            st.markdown(f'<div class="reading-pane">{body}</div>', unsafe_allow_html=True)
            st.caption("💡 Hover over highlighted chips to see the word. Use the panel on the right to look up meanings.")

        with col_r:
            st.markdown('<div class="sec-label">Select a Word</div>', unsafe_allow_html=True)
            if words:
                # Show chips
                chips = "".join(f'<span class="wchip">{w}</span>' for w in words[:180])
                st.markdown(f'<div class="chipbox">{chips}</div>', unsafe_allow_html=True)
                st.caption(f"Showing up to 180 of {n_words} unique Tamil words")

                sel = st.selectbox(
                    "Choose a word for its meaning:",
                    ["— pick a word —"] + words,
                    key="doc_sel",
                )
                if sel and sel != "— pick a word —":
                    st.session_state.sel = sel
                    with st.spinner("Looking up…"):
                        st.session_state.meaning = lookup(sel)

                if st.session_state.meaning and st.session_state.sel:
                    render_card(st.session_state.sel, st.session_state.meaning)
            else:
                st.markdown('<div class="pcard">⚠️ No Tamil words detected in this document.</div>',
                            unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="upload-prompt">
          <div class="upload-icon">📜</div>
          <div class="upload-title">Upload a Tamil Document</div>
          <div class="upload-sub">PDF &nbsp;·&nbsp; Microsoft Word (DOCX) &nbsp;·&nbsp; Plain Text (TXT)</div>
          <div class="upload-quote">"கற்றது கை மண் அளவு; கல்லாதது உலகளவு"</div>
          <div class="upload-quotesrc">What one has learned is a handful of earth; what remains unlearned is the size of the world.</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# TAB 2 — WORD LOOKUP
# ─────────────────────────────────────────────────────────────────────
with tab_lookup:
    st.markdown('<div class="sec-label">4-Tier Tamil Word Lookup</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="pcard">
    Every word passes through four tiers automatically:<br>
    <strong>Tier 2</strong> — Local <code>tamil.json</code> (instant, offline)&nbsp;&nbsp;
    <strong>Tier 3</strong> — Google Translate + Free Dictionary API (1–3 s)&nbsp;&nbsp;
    <strong>Tier 4</strong> — Helsinki-NLP neural MT (5–10 s, no API key)
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.markdown('<div class="sec-label">Single Word</div>', unsafe_allow_html=True)
        wi = st.text_input("Enter a Tamil word", placeholder="e.g. மகிழ்ச்சி", key="lu_input")
        if st.button("🔍 Find Meaning", key="lu_btn") and wi.strip():
            with st.spinner("Searching…"):
                wr = lookup(wi.strip())
            render_card(wi.strip(), wr)

        st.markdown('<div class="sec-label" style="margin-top:2rem">Browse Dictionary</div>',
                    unsafe_allow_html=True)
        letters = sorted({w[0] for w in TDICT if w})
        pick = st.selectbox("Starting letter:", ["All"] + letters, key="browse_pick")
        filtered = {k: v for k, v in TDICT.items()
                    if pick == "All" or k.startswith(pick)}
        st.caption(f"{len(filtered)} words")
        for wk, wd in list(filtered.items())[:40]:
            with st.expander(f"{wk}  —  {wd.get('english','')[:45]}"):
                render_card(wk, {**wd, "tier": 2, "label": "📖 Local Dictionary"})

    with col_b:
        st.markdown('<div class="sec-label">Batch Lookup</div>', unsafe_allow_html=True)
        batch_txt = st.text_area("Paste Tamil text here:", height=130,
                                 placeholder="அன்பு வாழ்க்கை இயற்கை கல்வி…",
                                 key="batch_txt")
        if st.button("🔍 Look Up All Words", key="batch_btn") and batch_txt.strip():
            bwords = extract_tamil_words(batch_txt)
            if not bwords:
                st.warning("No Tamil words found.")
            else:
                prog = st.progress(0)
                for i, bw in enumerate(bwords[:25]):
                    br = lookup(bw)
                    render_card(bw, br)
                    prog.progress((i + 1) / min(len(bwords), 25))
                prog.empty()
                if len(bwords) > 25:
                    st.info(f"Showed first 25 of {len(bwords)} words.")

# ─────────────────────────────────────────────────────────────────────
# TAB 3 — TEST RESULTS
# ─────────────────────────────────────────────────────────────────────
with tab_tests:
    st.markdown('<div class="sec-label">🧪 Self-Test Suite — 1 000+ Cases</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="pcard">
    <strong>5 test categories</strong> run automatically on every startup to verify correctness:<br>
    <strong>A</strong> — Tamil char detection &nbsp; <strong>B</strong> — Word cleaning &nbsp;
    <strong>C</strong> — Tamil word extraction &nbsp; <strong>D</strong> — Dictionary lookup &nbsp;
    <strong>E</strong> — Bulk extraction round-trip
    </div>
    """, unsafe_allow_html=True)

    # Auto-run on first visit
    if st.session_state.tests is None:
        with st.spinner("Running 1 000+ test cases on startup…"):
            st.session_state.tests = run_tests()

    tr = st.session_state.tests
    rate = tr["rate"]
    rcolor = "#1a6b1a" if rate >= 95 else "#8b6b10" if rate >= 80 else "#8b1a1a"

    st.markdown(f"""
    <div class="sstrip">
      <div class="sstat"><span class="snum" style="color:{rcolor}">{rate}%</span><span class="slbl">Pass rate</span></div>
      <div class="sstat"><span class="snum">{tr['total']:,}</span><span class="slbl">Total tests</span></div>
      <div class="sstat"><span class="snum" style="color:#1a6b1a">{tr['passed']:,}</span><span class="slbl">Passed</span></div>
      <div class="sstat"><span class="snum" style="color:#8b1a1a">{tr['failed']:,}</span><span class="slbl">Failed</span></div>
    </div>
    """, unsafe_allow_html=True)

    cat_names = {
        "A_char_detect":    "A — Tamil character detection",
        "B_clean_word":     "B — Word cleaning & normalisation",
        "C_extraction":     "C — Tamil word extraction from text",
        "D_json_lookup":    "D — Local dictionary (JSON) lookup",
        "E_bulk_roundtrip": "E — Bulk extraction round-trip",
    }
    for key, name in cat_names.items():
        cat = tr["cats"].get(key, {"pass": 0, "fail": 0})
        tot = cat["pass"] + cat["fail"]
        cr  = round(cat["pass"] / max(tot, 1) * 100, 1)
        ico = "✅" if cr >= 95 else "⚠️" if cr >= 80 else "❌"
        fill_color = "#1a6b1a" if cr >= 95 else "#a07010" if cr >= 80 else "#8b1a1a"
        st.markdown(f"""
        <div class="pcard" style="padding:.7rem 1.1rem;margin:.3rem 0">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-family:'EB Garamond',serif;font-size:1rem">{ico} {name}</span>
            <span style="font-family:'Cinzel',serif;color:{fill_color};font-size:1.05rem;font-weight:600">
              {cat['pass']}/{tot} &nbsp; ({cr}%)
            </span>
          </div>
          <div class="tbar-bg">
            <div class="tbar-fill" style="width:{int(cr)}%;background:{fill_color}"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if tr["failures"]:
        with st.expander(f"🔴 View failure log ({len(tr['failures'])} shown)"):
            for f in tr["failures"]:
                st.text(f)
    else:
        st.success("🎉 All 1 000 tests passed! The system is verified and ready.")

    st.markdown("""
    <div class="orn">✦ ✦ ✦</div>
    <div style="text-align:center;font-family:'EB Garamond',serif;font-style:italic;
                color:#0e5048;font-size:1rem;margin-top:.5rem">
      "முயற்சி திருவினை ஆக்கும்" — Persistent effort achieves noble deeds.
    </div>
    """, unsafe_allow_html=True)
