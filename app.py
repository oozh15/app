"""
Tamil Government Document Reader — v4 (Production)
════════════════════════════════════════════════════
KEY FIXES in this version:
 1. Shabdkosh removed (blocks scraping, returns page-SEO text not definition)
 2. Tamil Wiktionary — correct HTML selector, works reliably
 3. MyMemory — used as PRIMARY translation source (very reliable)
 4. Google Translate via deep-translator — strong fallback
 5. SANDHI CONVERSION ENGINE — critical for government words:
      ஒப்பந்தத்தில் → strip த்தில் → ஒப்பந்த → sandhi த→ம் → ஒப்பந்தம் ✓
      விரும்பினால்  → strip இனால்  → விரும்பின் → strip இன் → விரும்பு  ✓
 6. Word search box always visible (right panel) — no need to upload first
"""

import io, re, requests, streamlit as st
from bs4 import BeautifulSoup
from gtts import gTTS
from PIL import Image
import pdfplumber, pytesseract

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Tamil Govt Document Reader", page_icon="📜", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#f4f1ec;}

.hdr{background:#0f172a;border-left:5px solid #d4a843;border-radius:12px;
     padding:1.5rem 2rem;margin-bottom:1.3rem;}
.hdr h1{color:#f8ecd4;font-size:1.65rem;font-weight:600;margin:0 0 .2rem;}
.hdr p {color:#a89880;font-size:.88rem;margin:0;}

.docbox{background:#fffef9;border:1px solid #ddd0b8;border-radius:10px;
  padding:1.3rem 1.6rem;
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:1.05rem;line-height:2.3;color:#1a1a1a;
  white-space:pre-wrap;word-break:break-word;
  max-height:460px;overflow-y:auto;}

.mcard{background:#fff;border-radius:12px;border:1px solid #e2d8c8;
  box-shadow:0 3px 14px rgba(0,0,0,.05);padding:1.25rem 1.45rem;}
.mword{font-family:'Noto Sans Tamil',sans-serif;font-size:1.5rem;
       font-weight:600;color:#0f172a;}
.mroot{font-size:.77rem;color:#999;margin:.15rem 0 .75rem;}
.mrow{margin-bottom:.8rem;}
.badge{display:inline-block;font-size:11px;font-weight:600;
  padding:2px 9px;border-radius:20px;margin:0 5px 3px 0;}
.b-wt{background:#e8f4fd;color:#1155aa;}
.b-mm{background:#d6f5e3;color:#155e2b;}
.b-gt{background:#fff0d6;color:#7a4500;}
.mdef{font-size:.95rem;color:#2d2d2d;line-height:1.75;
  border-left:3px solid #d4a843;padding-left:.75rem;margin-top:.22rem;}
.notfound{font-size:.92rem;color:#b91c1c;background:#fef2f2;
  border:1px solid #fecaca;border-radius:8px;padding:.65rem .9rem;margin-top:.5rem;}
.slabel{font-size:.72rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.08em;color:#888;margin-bottom:.4rem;}
.hint{display:inline-block;background:#fef9e7;border:1px solid #fce7a0;
  border-radius:8px;padding:.42rem .85rem;font-size:.83rem;
  color:#7a5100;margin-bottom:.85rem;}
.step{background:#fff;border:1px solid #e5dfd4;border-radius:10px;
  padding:.85rem 1.1rem;margin-bottom:.5rem;font-size:.92rem;line-height:1.65;}
.num{display:inline-flex;align-items:center;justify-content:center;
  width:21px;height:21px;border-radius:50%;
  background:#0f172a;color:#d4a843;
  font-size:11px;font-weight:700;margin-right:7px;flex-shrink:0;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SUFFIX ENGINE  (strips up to 6 layers of Tamil inflection)
# ══════════════════════════════════════════════════════════════════════════════

# Ordered longest → shortest
SUFFIXES = [
    # passive / causative
    "ப்படுகிறது","ப்படுகின்றது","க்கப்படும்","ப்படும்","ப்பட்டது",
    "வைக்கப்படும்","படுத்தப்படும்",
    # conditional
    "யினால்","வதினால்","தினால்","டினால்","றினால்","னினால்","இனால்","ினால்","னால்","ால்",
    # past person
    "ன்றனர்","னார்கள்","னார்","ட்டார்கள்","ட்டார்","தார்கள்","தார்",
    "ட்டேன்","தேன்","டேன்","ினான்","ினாள்","னான்","னாள்",
    "த்தான்","த்தாள்","ிட்டான்","ிட்டாள்",
    # present
    "கிறார்கள்","கிறார்","கிறான்","கிறாள்","கிறோம்","கிறீர்கள்",
    "கின்றார்","கின்றான்","கிறது","கின்றது",
    # future
    "வார்கள்","வார்","வான்","வாள்","வோம்","பார்","பான்","வீர்கள்",
    # verbal noun / infinitive
    "வதற்கு","படுவது","கின்றது","வதை","தலை","கல்","வது",
    # case suffixes — locative, instrumental, genitive, etc.
    "த்திலிருந்து","த்தினால்","த்துடன்","த்தோடு",
    "த்தில்","த்தை","த்தின்","த்துக்கு","த்தோ",
    "இல்லாமல்","இருந்தால்","இருந்து","உடைய","யுடன்","உடன்",
    "என்று","ஆகும்","ஆனது","ஆல்","ஆக","ஆன",
    "யில்","யை","யின்","யிடம்","கள்","இல்","ஐ","கு",
    # tense markers
    "க்கான","ிய","்ற","்த",
    # verbal suffix ன்
    "ின்","இன்",
]

# SANDHI ENDINGS: when a suffix is removed, the stem may need an ending fix
# Maps last-chars-of-stem → corrected-ending
# e.g. ஒப்பந்த (after removing த்தில்) → ஒப்பந்தம்
SANDHI_MAP = [
    ("ந்த",   "ந்தம்"),    # ஒப்பந்த → ஒப்பந்தம்
    ("ட்ட",   "ட்டம்"),    # பட்ட → பட்டம்
    ("க்க",   "க்கம்"),
    ("ட்டு",  "ட்டு"),     # already ok
    ("ன்று",  "ன்று"),
    ("ல்ல",   "ல்"),
    ("ன்ன",   "ன்னம்"),
    ("ர்த்த", "ர்த்தம்"),
]

def apply_sandhi(word: str) -> list[str]:
    """Return additional sandhi-corrected forms for a stripped stem."""
    results = []
    for tail, replacement in SANDHI_MAP:
        if word.endswith(tail):
            base = word[: -len(tail)]
            results.append(base + replacement)
    return results

def _strip_one(word: str):
    for s in SUFFIXES:
        if word.endswith(s) and len(word) > len(s) + 1:
            return word[: -len(s)]
    return None

def _variants(word: str) -> list[str]:
    swaps = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [word.replace(a,b,1) for a,b in swaps if a in word and word.replace(a,b,1) != word]

def all_candidates(word: str) -> list[str]:
    seen, result = set(), []
    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w); result.append(w)

    add(word)
    cur = word
    for _ in range(6):
        nxt = _strip_one(cur)
        if not nxt:
            break
        add(nxt)
        for sc in apply_sandhi(nxt):   # sandhi forms
            add(sc)
        for v in _variants(nxt):        # spelling variants
            add(v)
        cur = nxt

    for v in _variants(word):           # original spelling variants
        add(v)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1 — Tamil Wiktionary  (dictionary definition, ~30k words)
# ══════════════════════════════════════════════════════════════════════════════
def src_wiktionary(word: str):
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
                    if clean and len(clean) > 3:
                        return clean, "Tamil Wiktionary", "b-wt"
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2 — MyMemory  (free, 5000 chars/day, no key needed)
# Most reliable free Tamil→English translation API
# ══════════════════════════════════════════════════════════════════════════════
def src_mymemory(word: str):
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"},
            timeout=4,
        )
        if r.status_code == 200:
            t = r.json().get("responseData",{}).get("translatedText","")
            if (t and t.strip().lower() != word.lower()
                    and "INVALID" not in t.upper()
                    and len(t.strip()) > 1):
                return t.strip(), "MyMemory (Tamil→English)", "b-mm"
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3 — Google Translate via deep-translator  (free, no key)
# ══════════════════════════════════════════════════════════════════════════════
def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.strip().lower() != word.lower():
            return t.strip(), "Google Translate", "b-gt"
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# Strategy: try every root candidate through MyMemory first.
# MyMemory returns "contract" for ஒப்பந்தம், "if desired" for விரும்பினால் etc.
# Wiktionary checked in parallel for formal definitions.
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str) -> dict:
    candidates = all_candidates(word)
    results, root_used = [], word

    # ── Try the ORIGINAL word directly through all 3 sources first ──
    # This catches compound words and phrases that should not be stripped
    m, src, badge = src_mymemory(word)
    if m:
        results.append({"meaning": m, "source": src, "badge": badge})

    m2, src2, badge2 = src_wiktionary(word)
    if m2:
        results.append({"meaning": m2, "source": src2, "badge": badge2})

    if results:
        return {"word": word, "root": word, "results": results,
                "found": True, "tried": candidates}

    # ── If original failed, try each stripped root ──
    for cand in candidates[1:]:   # skip index 0 = original already tried
        m, src, badge = src_mymemory(cand)
        if m:
            root_used = cand
            results.append({"meaning": m, "source": src, "badge": badge})
            # also try wiktionary for same root (richer definition)
            m2, src2, badge2 = src_wiktionary(cand)
            if m2:
                results.append({"meaning": m2, "source": src2, "badge": badge2})
            break

        m2, src2, badge2 = src_wiktionary(cand)
        if m2:
            root_used = cand
            results.append({"meaning": m2, "source": src2, "badge": badge2})
            break

    # ── If still nothing, fall back to Google Translate on original ──
    if not results:
        m, src, badge = src_google(word)
        if m:
            results.append({"meaning": m, "source": src, "badge": badge})

    return {"word": word, "root": root_used, "results": results,
            "found": bool(results), "tried": candidates}


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word: str):
    try:
        buf = io.BytesIO()
        gTTS(text=word, lang="ta", slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ── OCR / Extraction ──────────────────────────────────────────────────────────
def ocr_image(img):
    return pytesseract.image_to_string(img, config=r"--oem 3 --psm 6 -l tam+eng")

def extract_pdf(f):
    texts = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: texts.append(t)
    return "\n\n".join(texts)

def is_tamil(w): return bool(re.search(r"[\u0B80-\u0BFF]", w))
def tokenize(t): return re.findall(r"[\u0B80-\u0BFF]+|[A-Za-z0-9]+|[^\w]", t)


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("text",""),("word","")]:
    st.session_state.setdefault(k, v)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 Tamil Government Document Reader</h1>
  <p>Upload PDF or image · Extract full text · Search any Tamil word · Get exact meaning + pronunciation · 100% free</p>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
t_reader, t_deploy = st.tabs(["📄 Document Reader", "🚀 GitHub → Streamlit Cloud Guide"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — READER
# ══════════════════════════════════════════════════════════════════════════════
with t_reader:
    left, right = st.columns([3, 2], gap="large")

    # ── LEFT: Upload + Text ──────────────────────────────────────────────────
    with left:
        st.markdown('<div class="slabel">Step 1 — Upload Document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("Extracting text from document…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("No selectable text — running OCR…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs = convert_from_bytes(uploaded.getvalue(), first_page=1, last_page=1)
                            text = ocr_image(imgs[0]) if imgs else ""
                        except Exception as e:
                            st.error(f"OCR error: {e}"); text = ""
                else:
                    text = ocr_image(Image.open(uploaded))
                st.session_state.text = text

        if st.session_state.text:
            st.markdown('<div class="slabel" style="margin-top:1.1rem">Step 2 — Read Document</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 Click any difficult word you see below, then pick it from the dropdown — or type it directly on the right panel</div>', unsafe_allow_html=True)

            # Document text in readable box
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)

            # Dropdown of all Tamil words extracted
            tamil_words = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t) > 1})
            if tamil_words:
                st.markdown('<div class="slabel" style="margin-top:.7rem">Pick a word from the document</div>', unsafe_allow_html=True)
                pick = st.selectbox("Words:", ["— select a word —"] + tamil_words,
                                    label_visibility="collapsed", key="pick")
                if pick != "— select a word —":
                    st.session_state.word = pick
        else:
            st.info("Upload a government document (PDF or scanned image) above to begin.")

    # ── RIGHT: Word Lookup ───────────────────────────────────────────────────
    with right:
        st.markdown('<div class="slabel">Word Meaning Lookup</div>', unsafe_allow_html=True)

        # Search box always visible — user can type without uploading
        typed = st.text_input("Type any Tamil word:", placeholder="உதாரணம்: ஒப்பந்தம், விரும்பினால்", key="typed")
        if typed:
            st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"Looking up '{w}'…"):
                res   = lookup(w)
                audio = speak(w)

            root_note = (f" ← stripped from <em>{res['word']}</em>"
                         if res["root"] != res["word"] else " (used as-is)")

            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">Root searched: <strong>{res['root']}</strong>{root_note}</div>
            """, unsafe_allow_html=True)

            if res["found"]:
                for r in res["results"]:
                    st.markdown(f"""
                    <div class="mrow">
                      <span class="badge {r['badge']}">{r['source']}</span>
                      <div class="mdef">{r['meaning']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                tried_count = len(res['tried'])
                st.markdown(f"""
                <div class="notfound">
                  ⚠️ No meaning found for <strong>{res['word']}</strong>.<br>
                  Tried <strong>{tried_count}</strong> root forms including
                  <em>{res['root']}</em>.<br>
                  💡 Tip: Try typing only the base part of the word.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 Pronunciation**")
                st.audio(audio, format="audio/mp3")

            with st.expander("🔍 All candidate roots tried"):
                for i, c in enumerate(res["tried"], 1):
                    st.write(f"{i}. `{c}`")

        elif w:
            st.info("Please enter a word using Tamil script (தமிழ்).")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-size:.92rem;margin-top:.4rem">
                Type any Tamil word above<br>or pick one from the document
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("Sources: Tamil Wiktionary + MyMemory + Google Translate  |  All free, zero API key")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEPLOY GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with t_deploy:
    st.markdown("## 🚀 Connect GitHub → Streamlit Cloud (Free, ~10 Minutes)")
    st.markdown("After setup, every save on GitHub **auto-deploys in ~60 seconds**.")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>Create free GitHub account</strong> →
      <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>New repository</strong> → click <code>+</code> top-right → New repository<br>
      Name: <code>tamil-doc-reader</code> | Visibility: <strong>Public</strong> → Create repository
    </div>
    <div class="step"><span class="num">3</span>
      <strong>Upload all 3 files</strong> → click "uploading an existing file" on GitHub<br>
      Drag & drop: <code>app.py</code> &emsp; <code>requirements.txt</code> &emsp; <code>packages.txt</code><br>
      → Commit changes
    </div>
    <div class="step"><span class="num">4</span>
      Go to <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → <strong>Sign in with GitHub</strong>
    </div>
    <div class="step"><span class="num">5</span>
      Click <strong>New app</strong> → choose repo <code>tamil-doc-reader</code><br>
      Branch: <code>main</code> | Main file: <code>app.py</code> → <strong>Deploy!</strong>
    </div>
    <div class="step"><span class="num">6</span>
      Wait <strong>3–5 minutes</strong> for first build. Streamlit reads <code>packages.txt</code>
      and installs Tesseract Tamil OCR automatically.<br>
      Free URL: <code>https://yourname-tamil-doc-reader.streamlit.app</code> ✅
    </div>
    <div class="step"><span class="num">7</span>
      <strong>Future updates:</strong> edit <code>app.py</code> on GitHub → commit → auto-redeploy ✅
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 File contents to upload")
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
            "deep-translator>=1.11.4",
            language="text",
        )
    with c2:
        st.markdown("**`packages.txt`** ← system packages for OCR")
        st.code(
            "tesseract-ocr\n"
            "tesseract-ocr-tam\n"
            "tesseract-ocr-eng\n"
            "poppler-utils",
            language="text",
        )
    st.success("✅ Zero paid services. Zero API keys. Just 3 files on GitHub.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.75rem;color:#bbb;margin-top:2rem;
  padding-top:.8rem;border-top:1px solid #ddd4c4;">
  Tamil Govt Document Reader · OCR: Tesseract ·
  Sources: Tamil Wiktionary + MyMemory + Google Translate · Audio: gTTS · 100% Free
</div>
""", unsafe_allow_html=True)
