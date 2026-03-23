"""
Tamil Government Document Reader — v6 FINAL
════════════════════════════════════════════
What this version delivers:
  1. TAMIL → TAMIL meaning  (simple Tamil, not English)
  2. Example sentence using the word in Tamil
  3. Document context — what the word means IN THIS specific document type
     (பட்டா / G.O. / certificate / legal — auto-detected)
  4. Improved OCR: contrast boost + sharpen + upscale before Tesseract
  5. Better text cleanup: proper paragraph formatting, Tamil font
  6. Fast fallback (MyMemory) when no API key configured

Setup: Add  ANTHROPIC_API_KEY = "sk-ant-..."  in Streamlit Cloud Secrets
"""

import io, re, os, json, requests
import streamlit as st
from gtts import gTTS
from PIL import Image, ImageFilter, ImageEnhance
import pdfplumber, pytesseract
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="தமிழ் ஆவண வாசகன்", page_icon="📜", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #f2ede6; }

/* Header */
.hdr {
  background: #0f172a; border-left: 5px solid #d4a843;
  border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.3rem;
}
.hdr h1 { color: #f8ecd4; font-size: 1.6rem; font-weight: 600; margin: 0 0 .2rem; }
.hdr p  { color: #a89880; font-size: .87rem; margin: 0; }

/* Document text box */
.docbox {
  background: #fffef8;
  border: 1px solid #ddd0b8;
  border-radius: 12px;
  padding: 1.5rem 1.9rem;
  font-family: 'Noto Sans Tamil', 'IBM Plex Sans', sans-serif;
  font-size: 1.1rem;
  line-height: 2.5;
  color: #111;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 520px;
  overflow-y: auto;
  letter-spacing: 0.01em;
}

/* Meaning card */
.mcard {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e2d8c8;
  box-shadow: 0 4px 18px rgba(0,0,0,.06);
  padding: 1.3rem 1.5rem;
  margin-top: .2rem;
}
.mword {
  font-family: 'Noto Sans Tamil', sans-serif;
  font-size: 1.55rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: .05rem;
}
.mroot { font-size: .74rem; color: #bbb; margin-bottom: 1rem; }

/* Section inside card */
.sec {
  margin-bottom: .9rem;
  border-radius: 9px;
  overflow: hidden;
}
.sec-head {
  font-size: .68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  padding: .3rem .75rem;
  display: flex;
  align-items: center;
  gap: 6px;
}
.sec-body {
  font-family: 'Noto Sans Tamil', 'IBM Plex Sans', sans-serif;
  font-size: 1rem;
  line-height: 1.9;
  padding: .6rem .85rem;
}

/* Colour themes per section */
.s-tamil   { background: #fff8e7; border: 1px solid #f3d98b; }
.s-tamil .sec-head { background: #fef0c0; color: #7a5000; }
.s-tamil .sec-body { color: #3a2a00; }

.s-example { background: #f0f7ff; border: 1px solid #b8d8f8; }
.s-example .sec-head { background: #dbeeff; color: #1a4a8a; }
.s-example .sec-body { color: #1a3a6a; font-style: italic; }

.s-context { background: #f0faf4; border: 1px solid #a8dcb8; }
.s-context .sec-head { background: #c8f0d8; color: #1a5a30; }
.s-context .sec-body { color: #1a3a20; }

.s-doc     { background: #fdf2ff; border: 1px solid #ddb8f8; }
.s-doc .sec-head { background: #f0d0ff; color: #4a0080; }
.s-doc .sec-body { color: #280050; }

/* word not found */
.notfound {
  font-size: .93rem; color: #b91c1c; background: #fef2f2;
  border: 1px solid #fecaca; border-radius: 9px; padding: .7rem 1rem; margin-top: .5rem;
}

/* misc */
.slabel {
  font-size: .71rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .09em; color: #999; margin-bottom: .35rem;
}
.hint {
  display: inline-block; background: #fef9e7; border: 1px solid #fce7a0;
  border-radius: 8px; padding: .4rem .85rem; font-size: .82rem;
  color: #7a5100; margin-bottom: .85rem;
}
.doc-type-chip {
  display: inline-block; font-size: .75rem; font-weight: 600;
  padding: 3px 10px; border-radius: 20px;
  background: #e8f4fd; color: #1155aa;
  margin-bottom: .7rem;
}
.step {
  background: #fff; border: 1px solid #e5dfd4; border-radius: 10px;
  padding: .85rem 1.1rem; margin-bottom: .5rem;
  font-size: .91rem; line-height: 1.65;
}
.num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 21px; height: 21px; border-radius: 50%;
  background: #0f172a; color: #d4a843;
  font-size: 11px; font-weight: 700; margin-right: 7px; flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TYPE DETECTOR
# Detects what kind of govt document was uploaded for context-specific meaning
# ══════════════════════════════════════════════════════════════════════════════
DOC_TYPES = {
    "பட்டா / சிட்டா": ["பட்டா", "சிட்டா", "survey", "சர்வே", "நிலம்", "ஏக்கர்", "புல", "subdivision"],
    "அரசாணை (G.O.)": ["G.O.", "அரசாணை", "government order", "செயல்முறை", "ஆணை"],
    "சான்றிதழ்": ["சான்றிதழ்", "certificate", "பிறப்பு", "சாதி", "வருமானம்", "income", "caste", "birth"],
    "சட்ட / நீதிமன்ற ஆவணம்": ["மனு", "petition", "court", "நீதிமன்றம்", "வழக்கு", "affidavit", "ஒப்பந்தம்"],
}

def detect_doc_type(text: str) -> str:
    text_lower = text.lower()
    for doc_type, keywords in DOC_TYPES.items():
        if any(kw.lower() in text_lower for kw in keywords):
            return doc_type
    return "அரசு ஆவணம்"


# ══════════════════════════════════════════════════════════════════════════════
# SUFFIX + SANDHI ENGINE
# ══════════════════════════════════════════════════════════════════════════════
SUFFIXES = [
    "ப்படுகிறது","ப்படுகின்றது","க்கப்படும்","ப்படும்","ப்பட்டது",
    "வைக்கப்படும்","படுத்தப்படும்",
    "யினால்","வதினால்","தினால்","டினால்","றினால்","னினால்","இனால்","ினால்","னால்","ால்",
    "ன்றனர்","னார்கள்","னார்","ட்டார்கள்","ட்டார்","தார்கள்","தார்",
    "ட்டேன்","தேன்","டேன்","ினான்","ினாள்","னான்","னாள்",
    "த்தான்","த்தாள்","ிட்டான்","ிட்டாள்",
    "கிறார்கள்","கிறார்","கிறான்","கிறாள்","கிறோம்",
    "கின்றார்","கின்றான்","கிறது","கின்றது",
    "வார்கள்","வார்","வான்","வாள்","வோம்","பார்","பான்","வீர்கள்",
    "வதற்கு","படுவது","வதை","தலை","கல்","வது",
    "த்திலிருந்து","த்தினால்","த்துடன்","த்தோடு",
    "த்தில்","த்தை","த்தின்","த்துக்கு","த்தோ",
    "இல்லாமல்","இருந்தால்","இருந்து","உடைய","யுடன்","உடன்",
    "என்று","ஆகும்","ஆனது","ஆல்","ஆக","ஆன",
    "யில்","யை","யின்","யிடம்","கள்","இல்","ஐ","கு",
    "க்கான","ிய","்ற","்த","ின்","இன்",
]

SANDHI_MAP = [
    ("ந்த","ந்தம்"), ("ட்ட","ட்டம்"), ("க்க","க்கம்"),
    ("ல்ல","ல்"),   ("ன்ன","ன்னம்"), ("ர்த்த","ர்த்தம்"),
]

def _strip_one(w):
    for s in SUFFIXES:
        if w.endswith(s) and len(w) > len(s) + 1:
            return w[:-len(s)]
    return None

def _sandhi(w):
    return [w[:-len(t)] + r for t, r in SANDHI_MAP if w.endswith(t)]

def _variants(w):
    swaps = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in swaps if a in w and w.replace(a,b,1) != w]

def all_candidates(word: str) -> list:
    seen, res = set(), []
    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w); res.append(w)
    add(word)
    cur = word
    for _ in range(6):
        nxt = _strip_one(cur)
        if not nxt: break
        add(nxt)
        for sc in _sandhi(nxt): add(sc)
        for v in _variants(nxt): add(v)
        cur = nxt
    for v in _variants(word): add(v)
    return res


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE PREPROCESSING — better OCR accuracy
# ══════════════════════════════════════════════════════════════════════════════
def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")                         # grayscale
    w, h = img.size
    if w < 1800:                                    # upscale to ~300 DPI equivalent
        scale = 1800 / w
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.2)  # boost contrast
    img = ImageEnhance.Sharpness(img).enhance(2.0) # sharpen
    arr = np.array(img)
    thresh = int(arr.mean() * 0.85)                # adaptive binarise
    arr = ((arr > thresh) * 255).astype(np.uint8)
    return Image.fromarray(arr)


# ══════════════════════════════════════════════════════════════════════════════
# TEXT CLEANUP — readable paragraphs after OCR
# ══════════════════════════════════════════════════════════════════════════════
def clean_text(raw: str) -> str:
    lines = raw.splitlines()
    out = []
    for line in lines:
        line = re.sub(r"[|}{\\~`_]", "", line).strip()
        line = re.sub(r" {2,}", " ", line)
        if not line:
            if out and out[-1] != "": out.append("")
            continue
        out.append(line)
    # Merge short wrapped lines (OCR wraps mid-sentence)
    merged, i = [], 0
    while i < len(out):
        if out[i] == "":
            merged.append(""); i += 1; continue
        cur = out[i]
        while (i+1 < len(out) and out[i+1] != ""
               and not cur.rstrip().endswith((".", ":", "?", "!", "।"))
               and len(cur) > 8):
            i += 1; cur += " " + out[i]
        merged.append(cur); i += 1
    return "\n".join(merged).strip()


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT SENTENCE FINDER
# ══════════════════════════════════════════════════════════════════════════════
def find_context(text: str, word: str) -> str | None:
    sentences = re.split(r'(?<=[.!?।\n])\s*', text)
    for cand in all_candidates(word):
        for sent in sentences:
            if cand in sent and len(sent.strip()) > 5:
                return sent.strip()
        idx = text.find(cand)
        if idx >= 0:
            s = max(0, idx-70); e = min(len(text), idx+len(cand)+70)
            return "…" + text[s:e].strip() + "…"
    return None


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE API — rich Tamil explanation
# ══════════════════════════════════════════════════════════════════════════════
def ask_claude(word: str, root: str, doc_type: str, context_sent: str | None) -> dict | None:
    key = st.secrets.get("ANTHROPIC_API_KEY","") or os.environ.get("ANTHROPIC_API_KEY","")
    if not key:
        return None

    ctx = f'\nஆவணத்தில் இந்த வரியில் இந்த சொல் வருகிறது:\n"{context_sent}"' if context_sent else ""

    prompt = f"""நீங்கள் ஒரு தமிழ் மொழி நிபுணர். அரசு ஆவணங்களை புரிந்துகொள்ள மக்களுக்கு உதவுகிறீர்கள்.

ஆவண வகை: {doc_type}
தேடிய சொல்: {word}
அடி வடிவம்: {root}{ctx}

கீழே கொடுக்கப்பட்ட JSON வடிவத்தில் மட்டும் பதில் தாருங்கள் (வேறு எதுவும் வேண்டாம்):
{{
  "tamil_meaning": "எளிய தமிழில் பொருள் — 1 முதல் 2 வரிகள். சாதாரண மக்கள் புரிந்துகொள்ளும் வகையில் எழுதவும்.",
  "example_sentence": "இந்த சொல்லை பயன்படுத்தி ஒரு எளிய தமிழ் வாக்கியம் எழுதவும்.",
  "doc_context": "இந்த சொல் {doc_type} ஆவணத்தில் என்ன குறிக்கிறது என்று 1-2 வரிகளில் விளக்கவும்.",
  "important_note": "இந்த சொல்லை பார்க்கும்போது குடிமக்கள் கவனிக்க வேண்டியது என்ன? (optional, only if relevant)"
}}

மிக எளிய தமிழில் எழுதவும். சங்க இலக்கிய தமிழ் வேண்டாம்."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [{"role":"user","content": prompt}],
            },
            timeout=8,
        )
        if r.status_code == 200:
            raw = r.json()["content"][0]["text"].strip()
            raw = re.sub(r"^```json\s*|```$","", raw.strip(), flags=re.MULTILINE).strip()
            return json.loads(raw)
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# FALLBACK SOURCES (when no API key)
# ══════════════════════════════════════════════════════════════════════════════
def src_mymemory(word: str) -> str | None:
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"},
            timeout=4,
        )
        if r.status_code == 200:
            t = r.json().get("responseData",{}).get("translatedText","")
            if t and t.lower() != word.lower() and "INVALID" not in t.upper() and len(t)>1:
                return t.strip()
    except Exception:
        pass
    return None

def src_wiktionary(word: str) -> str | None:
    try:
        url = f"https://ta.wiktionary.org/api/rest_v1/page/definition/{requests.utils.quote(word)}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            for key in data:
                entries = data[key]
                if isinstance(entries, list) and entries:
                    raw = entries[0].get("definitions",[{}])[0].get("definition","")
                    clean = re.sub(r"<[^>]+>","",raw).strip()
                    if clean and len(clean)>3:
                        return clean
    except Exception:
        pass
    return None

def src_google(word: str) -> str | None:
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.lower() != word.lower():
            return t.strip()
    except Exception:
        pass
    return None

def fallback_lookup(word: str) -> str | None:
    candidates = all_candidates(word)
    t = src_mymemory(word)
    if t: return t
    for c in candidates[1:]:
        t = src_mymemory(c)
        if t: return t
        t = src_wiktionary(c)
        if t: return t
    return src_google(word)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOKUP ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str = "", doc_type: str = "அரசு ஆவணம்") -> dict:
    candidates  = all_candidates(word)
    root_used   = candidates[1] if len(candidates) > 1 else word  # first stripped form
    ctx_sent    = find_context(doc_text, word) if doc_text else None
    ai          = ask_claude(word, root_used, doc_type, ctx_sent)
    fallback    = None if ai else fallback_lookup(word)
    return {
        "word":     word,
        "root":     root_used,
        "ai":       ai,
        "fallback": fallback,
        "context":  ctx_sent,
        "found":    bool(ai or fallback),
        "tried":    candidates,
    }


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word):
    try:
        buf = io.BytesIO()
        gTTS(text=word, lang="ta", slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ── OCR / Extraction ──────────────────────────────────────────────────────────
def ocr_image(img: Image.Image) -> str:
    enhanced = preprocess_for_ocr(img)
    raw = pytesseract.image_to_string(enhanced, config=r"--oem 3 --psm 6 -l tam+eng")
    return clean_text(raw)

def extract_pdf(f) -> str:
    texts = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: texts.append(clean_text(t))
    return "\n\n".join(texts)

def is_tamil(w): return bool(re.search(r"[\u0B80-\u0BFF]", w))
def tokenize(t): return re.findall(r"[\u0B80-\u0BFF]+|[A-Za-z0-9]+", t)


# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("text",""),("word",""),("doc_type","அரசு ஆவணம்")]:
    st.session_state.setdefault(k,v)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 தமிழ் அரசு ஆவண வாசகன்</h1>
  <p>Tamil Government Document Reader — Upload PDF or image · Read clearly · Search any Tamil word · Get full Tamil explanation</p>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
t_reader, t_deploy = st.tabs(["📄 ஆவண வாசகன்", "🚀 GitHub → Streamlit Cloud Guide"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — READER
# ══════════════════════════════════════════════════════════════════════════════
with t_reader:
    left, right = st.columns([3, 2], gap="large")

    # ── LEFT: Upload + Display ───────────────────────────────────────────────
    with left:
        st.markdown('<div class="slabel">படி 1 — ஆவணம் பதிவேற்றவும்</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("உரை எடுக்கிறோம்…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("PDF-ல் தேர்வு செய்யக்கூடிய உரை இல்லை — OCR இயக்குகிறோம்…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs = convert_from_bytes(uploaded.getvalue(), first_page=1, last_page=1)
                            text = ocr_image(imgs[0]) if imgs else ""
                        except Exception as e:
                            st.error(f"OCR பிழை: {e}"); text = ""
                else:
                    text = ocr_image(Image.open(uploaded))

                st.session_state.text     = text
                st.session_state.doc_type = detect_doc_type(text)

        if st.session_state.text:
            # Show detected document type
            st.markdown(
                f'<div class="doc-type-chip">📋 கண்டறிந்த ஆவண வகை: {st.session_state.doc_type}</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="slabel">படி 2 — ஆவணம் படிக்கவும்</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="hint">💡 புரியாத சொல்லை கீழே உள்ள dropdown-ல் தேர்வு செய்யுங்கள் அல்லது வலது பக்கத்தில் தட்டச்சு செய்யுங்கள்</div>',
                unsafe_allow_html=True,
            )

            # Document text — readable
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)

            # Word picker dropdown
            tamil_words = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t) > 1})
            if tamil_words:
                st.markdown('<div class="slabel" style="margin-top:.7rem">ஆவணத்தில் உள்ள சொற்கள்</div>', unsafe_allow_html=True)
                pick = st.selectbox("சொல் தேர்வு", ["— தேர்வு செய்யவும் —"] + tamil_words,
                                    label_visibility="collapsed", key="pick")
                if pick != "— தேர்வு செய்யவும் —":
                    st.session_state.word = pick
        else:
            st.info("மேலே அரசு ஆவணம் (PDF அல்லது படம்) பதிவேற்றவும்.")

    # ── RIGHT: Word Lookup ────────────────────────────────────────────────────
    with right:
        st.markdown('<div class="slabel">சொல் பொருள்</div>', unsafe_allow_html=True)

        typed = st.text_input(
            "தமிழ் சொல் தட்டச்சு செய்யவும்:",
            placeholder="உதா: ஒப்பந்தம், விரும்பினால், சர்வே",
            key="typed",
        )
        if typed:
            st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"'{w}' — பொருள் தேடுகிறோம்…"):
                res   = lookup(w, st.session_state.text, st.session_state.doc_type)
                audio = speak(w)

            # ── Meaning card ─────────────────────────────────────────────────
            root_note = f"(அடி வடிவம்: {res['root']})" if res["root"] != res["word"] else ""
            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">{root_note}</div>
            """, unsafe_allow_html=True)

            if res["found"]:
                ai = res["ai"]

                if ai:
                    # ── 1. Tamil meaning ──
                    if ai.get("tamil_meaning"):
                        st.markdown(f"""
                        <div class="sec s-tamil">
                          <div class="sec-head">📖 தமிழ் பொருள்</div>
                          <div class="sec-body">{ai['tamil_meaning']}</div>
                        </div>""", unsafe_allow_html=True)

                    # ── 2. Example sentence ──
                    if ai.get("example_sentence"):
                        st.markdown(f"""
                        <div class="sec s-example">
                          <div class="sec-head">✏️ எடுத்துக்காட்டு வாக்கியம்</div>
                          <div class="sec-body">{ai['example_sentence']}</div>
                        </div>""", unsafe_allow_html=True)

                    # ── 3. Document context ──
                    if ai.get("doc_context"):
                        st.markdown(f"""
                        <div class="sec s-doc">
                          <div class="sec-head">📋 {res.get('doc_type', st.session_state.doc_type)} — பயன்பாடு</div>
                          <div class="sec-body">{ai['doc_context']}</div>
                        </div>""", unsafe_allow_html=True)

                    # ── 4. Important note (if any) ──
                    if ai.get("important_note"):
                        st.markdown(f"""
                        <div class="sec s-context">
                          <div class="sec-head">⚠️ கவனிக்க வேண்டியது</div>
                          <div class="sec-body">{ai['important_note']}</div>
                        </div>""", unsafe_allow_html=True)

                else:
                    # ── Fallback: English translation ──
                    st.markdown(f"""
                    <div class="sec s-tamil">
                      <div class="sec-head">🔤 பொருள் (English)</div>
                      <div class="sec-body">{res['fallback']}</div>
                    </div>""", unsafe_allow_html=True)

                # ── 5. Sentence from document ──
                if res["context"]:
                    st.markdown(f"""
                    <div class="sec s-context">
                      <div class="sec-head">📄 உங்கள் ஆவணத்தில்</div>
                      <div class="sec-body">{res['context']}</div>
                    </div>""", unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class="notfound">
                  ⚠️ <strong>{res['word']}</strong> — பொருள் கிடைக்கவில்லை.<br>
                  {len(res['tried'])} வடிவங்கள் தேடப்பட்டன. சிறிய வடிவில் மீண்டும் முயற்சிக்கவும்.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 உச்சரிப்பு**")
                st.audio(audio, format="audio/mp3")

            with st.expander("🔍 தேடிய வடிவங்கள்"):
                for i, c in enumerate(res["tried"], 1):
                    st.write(f"{i}. `{c}`")

        elif w:
            st.info("தமிழ் எழுத்தில் சொல்லை தட்டச்சு செய்யவும்.")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-family:'Noto Sans Tamil',sans-serif;font-size:1rem;margin-top:.4rem;color:#999;">
                மேலே சொல்லை தட்டச்சு செய்யுங்கள்<br>அல்லது ஆவணத்தில் இருந்து தேர்வு செய்யுங்கள்
              </div>
            </div>""", unsafe_allow_html=True)

        # API key notice
        has_key = bool(st.secrets.get("ANTHROPIC_API_KEY","") or os.environ.get("ANTHROPIC_API_KEY",""))
        if not has_key:
            with st.expander("⚙️ AI விளக்கம் இயக்கவும் (தமிழ் பொருள் + எடுத்துக்காட்டு)"):
                st.markdown("""
                **AI-powered explanations** (தமிழ் பொருள், எடுத்துக்காட்டு, ஆவண சூழல்) க்கு:

                1. [console.anthropic.com](https://console.anthropic.com) — இலவச API key பெறவும்
                2. Streamlit Cloud → உங்கள் app → **Settings → Secrets**
                3. இதை சேர்க்கவும்: `ANTHROPIC_API_KEY = "sk-ant-..."`
                4. Save → app தானாக மறுதொடக்கம் ஆகும்

                Key இல்லாமலும் app வேலை செய்யும் (English translation மட்டும் கிடைக்கும்).
                """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEPLOY GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with t_deploy:
    st.markdown("## 🚀 GitHub → Streamlit Cloud — ஒரே நேரம் Setup (~10 நிமிடம்)")
    st.markdown("Setup முடிந்தால், GitHub-ல் save செய்தால் **60 நொடியில் auto-deploy** ஆகும்.")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>GitHub account உருவாக்கவும் (இலவசம்)</strong> →
      <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>New repository உருவாக்கவும்</strong> → <code>+</code> → New repository<br>
      Name: <code>tamil-doc-reader</code> | Visibility: <strong>Public</strong> → Create
    </div>
    <div class="step"><span class="num">3</span>
      <strong>3 files upload செய்யவும்</strong> — "uploading an existing file" என்பதை click செய்யவும்<br>
      <code>app.py</code> &emsp; <code>requirements.txt</code> &emsp; <code>packages.txt</code>
      → Commit changes
    </div>
    <div class="step"><span class="num">4</span>
      <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → GitHub உடன் Sign in → <strong>New app</strong><br>
      Repo: <code>tamil-doc-reader</code> | Branch: <code>main</code> | File: <code>app.py</code>
      → <strong>Deploy!</strong>
    </div>
    <div class="step"><span class="num">5</span>
      3–5 நிமிடம் காத்திருக்கவும் → இலவச URL கிடைக்கும்:
      <code>https://yourname-tamil-doc-reader.streamlit.app</code> ✅
    </div>
    <div class="step"><span class="num">6</span>
      <strong>AI விளக்கம் சேர்க்க (optional):</strong><br>
      Streamlit Cloud → app → Settings → Secrets →
      <code>ANTHROPIC_API_KEY = "sk-ant-..."</code> சேர்க்கவும்
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**`requirements.txt`**")
        st.code(
            "streamlit>=1.32.0\n"
            "pytesseract>=0.3.10\n"
            "Pillow>=10.0.0\n"
            "pdfplumber>=0.10.0\n"
            "pdf2image>=1.16.0\n"
            "gTTS>=2.5.0\n"
            "requests>=2.31.0\n"
            "beautifulsoup4>=4.12.0\n"
            "deep-translator>=1.11.4\n"
            "numpy>=1.24.0",
            language="text",
        )
    with c2:
        st.markdown("**`packages.txt`**")
        st.code("tesseract-ocr\ntesseract-ocr-tam\ntesseract-ocr-eng\npoppler-utils", language="text")

    st.success("✅ கட்டண சேவை இல்லை. API key இல்லாமலும் வேலை செய்யும். AI key optional.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.74rem;color:#bbb;margin-top:2rem;
  padding-top:.8rem;border-top:1px solid #ddd4c4;">
  தமிழ் அரசு ஆவண வாசகன் v6 · OCR: Tesseract ·
  AI: Claude Haiku (optional) · Dictionary: Tamil Wiktionary + MyMemory + Google Translate ·
  Audio: gTTS · 100% Free
</div>
""", unsafe_allow_html=True)
