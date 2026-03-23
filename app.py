"""
Tamil Government Document Reader — Production Version
══════════════════════════════════════════════════════
Meaning lookup pipeline (all free, no API key):
  1. Shabdkosh  tamil-english  (best coverage, scrape public page)
  2. Tamil Wiktionary REST API (classical dictionary definitions)
  3. MyMemory free translation  (Tamil → English, no key)
  4. Google Translate via deep-translator (final fallback)

Suffix engine:
  Covers conditional (ால்/இனால்), past (னான்/ட்டான்/தான்),
  future (வான்/பான்), verbal noun, causative, passive endings
  so inflected government-document words reach their root.
"""

import io
import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from gtts import gTTS
from PIL import Image
import pdfplumber
import pytesseract

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tamil Govt Document Reader",
    page_icon="📜",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #f4f1ec; }

/* ── header ── */
.hdr {
  background: #0f172a; border-left: 5px solid #d4a843;
  border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.3rem;
}
.hdr h1 { color: #f8ecd4; font-size: 1.65rem; font-weight: 600; margin: 0 0 .2rem; }
.hdr p  { color: #a89880; font-size: .88rem; margin: 0; }

/* ── document text box ── */
.docbox {
  background: #fffef9; border: 1px solid #ddd0b8; border-radius: 10px;
  padding: 1.3rem 1.6rem;
  font-family: 'Noto Sans Tamil', 'IBM Plex Sans', sans-serif;
  font-size: 1.05rem; line-height: 2.3; color: #1a1a1a;
  white-space: pre-wrap; word-break: break-word;
  max-height: 460px; overflow-y: auto;
}

/* ── meaning card ── */
.mcard {
  background: #fff; border-radius: 12px; border: 1px solid #e2d8c8;
  box-shadow: 0 3px 14px rgba(0,0,0,.05); padding: 1.25rem 1.45rem;
}
.mword { font-family: 'Noto Sans Tamil', sans-serif; font-size: 1.5rem; font-weight: 600; color: #0f172a; }
.mroot { font-size: .77rem; color: #999; margin: .15rem 0 .75rem; }
.mrow  { margin-bottom: .8rem; }
.badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  padding: 2px 9px; border-radius: 20px; margin: 0 5px 3px 0;
}
.b-sk  { background: #e8f4fd; color: #1155aa; }  /* shabdkosh  */
.b-wt  { background: #d6f5e3; color: #155e2b; }  /* wiktionary */
.b-mm  { background: #fff0d6; color: #7a4500; }  /* mymemory   */
.b-gt  { background: #fde8e8; color: #7f1d1d; }  /* google     */
.mdef {
  font-size: .95rem; color: #2d2d2d; line-height: 1.75;
  border-left: 3px solid #d4a843; padding-left: .75rem; margin-top: .22rem;
}
.msynonyms {
  font-size: .82rem; color: #666; margin-top: .35rem;
  font-style: italic;
}
.notfound {
  font-size: .92rem; color: #b91c1c; background: #fef2f2;
  border: 1px solid #fecaca; border-radius: 8px; padding: .65rem .9rem; margin-top: .5rem;
}

/* ── misc ── */
.slabel {
  font-size: .72rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .08em; color: #888; margin-bottom: .4rem;
}
.hint {
  display: inline-block; background: #fef9e7; border: 1px solid #fce7a0;
  border-radius: 8px; padding: .42rem .85rem; font-size: .83rem;
  color: #7a5100; margin-bottom: .85rem;
}
.step {
  background: #fff; border: 1px solid #e5dfd4; border-radius: 10px;
  padding: .85rem 1.1rem; margin-bottom: .5rem; font-size: .92rem; line-height: 1.65;
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
# SUFFIX ENGINE
# Government Tamil verbs carry tense + person + case in stacked suffixes.
# We must strip them all to reach the dictionary headword.
# ══════════════════════════════════════════════════════════════════════════════

# Ordered longest → shortest so the most specific suffix wins first.
SUFFIXES = [
    # conditional
    "யினால்", "வதினால்", "தினால்", "டினால்", "றினால்", "னினால்", "இனால்",
    "ினால்", "னால்", "ால்",
    # passive / causative long forms
    "ப்படுகிறது", "ப்படுகின்றது", "க்கப்படும்", "ப்படும்", "ப்பட்டது",
    "ப்பட்டது", "வைக்கப்படும்", "படுத்தப்படும்",
    # past tense person endings
    "ன்றனர்", "னார்கள்", "னார்", "ட்டார்கள்", "ட்டார்", "தார்கள்", "தார்",
    "ட்டேன்", "தேன்", "டேன்",
    # present tense
    "கிறார்கள்", "கிறார்", "கிறான்", "கிறாள்", "கிறோம்", "கிறீர்கள்",
    "கின்றார்", "கின்றான்", "கிறது", "கின்றது",
    # future tense
    "வார்கள்", "வார்", "வான்", "வாள்", "வோம்", "பார்", "பான்", "வார்",
    "வீர்கள்",
    # verbal noun / infinitive
    "வதற்கு", "படுவது", "கின்றது", "வதை", "தலை", "கல்",
    # common case suffixes
    "இல்லாமல்", "இருந்தால்", "இருந்து", "உடைய", "யுடன்", "உடன்",
    "என்று", "ஆகும்", "ஆனது", "ஆல்", "இல்", "ஆக", "ஆன",
    "கள்", "ஐ", "கு",
    # short tense markers
    "ினான்", "ினாள்", "னான்", "னாள்", "த்தான்", "த்தாள்",
    "ிட்டான்", "ிட்டாள்", "க்கான",
]

def _strip_one(word: str) -> str | None:
    for s in SUFFIXES:
        if word.endswith(s) and len(word) > len(s) + 1:
            return word[: -len(s)]
    return None

def _variants(word: str) -> list[str]:
    swaps = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    out = []
    for a, b in swaps:
        if a in word:
            v = word.replace(a, b, 1)
            if v != word:
                out.append(v)
    return out

def all_candidates(word: str) -> list[str]:
    """Original + up to 6 suffix-stripped roots + spelling variants at each."""
    seen, result = set(), []
    def add(w):
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            result.append(w)

    add(word)
    cur = word
    for _ in range(6):
        nxt = _strip_one(cur)
        if not nxt:
            break
        add(nxt)
        for v in _variants(nxt):
            add(v)
        cur = nxt

    # also add variants of original
    for v in _variants(word):
        add(v)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1 — Shabdkosh  (best coverage, scrapes public page — no key needed)
# URL: shabdkosh.com/dictionary/tamil-english/{word}/{word}-meaning-in-english
# ══════════════════════════════════════════════════════════════════════════════
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def _sk_url(word: str) -> str:
    enc = requests.utils.quote(word)
    return f"https://www.shabdkosh.com/dictionary/tamil-english/{enc}/{enc}-meaning-in-english"

def src_shabdkosh(word: str):
    try:
        r = requests.get(_sk_url(word), headers={"User-Agent": _UA}, timeout=4)
        if r.status_code != 200:
            return None, None, None
        soup = BeautifulSoup(r.text, "html.parser")

        meaning, synonyms = None, None

        # Primary meaning paragraph — Shabdkosh puts it in <p> containing
        # "The word or phrase … refers to"
        for p in soup.find_all("p"):
            t = p.get_text(" ", strip=True)
            if "refers to" in t and len(t) > 20:
                # extract just the "refers to …" part
                idx = t.find("refers to")
                snippet = t[idx + len("refers to"):].strip().rstrip(".")
                if snippet:
                    meaning = "Refers to: " + snippet
                    break

        # Fallback: grab first substantial paragraph with English text
        if not meaning:
            for p in soup.find_all("p"):
                t = p.get_text(" ", strip=True)
                if len(t) > 25 and re.search(r"[A-Za-z]{4,}", t):
                    meaning = t
                    break

        # Tamil synonyms block (தமிழ் சொற்கள்)
        syn_block = soup.find("div", class_=re.compile(r"synonym|related", re.I))
        if syn_block:
            syn_text = syn_block.get_text(", ", strip=True)
            if re.search(r"[\u0B80-\u0BFF]", syn_text):
                synonyms = syn_text[:200]

        if meaning and len(meaning) > 10:
            return meaning, synonyms, ("Shabdkosh (Tamil→English)", "b-sk")
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2 — Tamil Wiktionary
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
                    raw = entries[0].get("definitions", [{}])[0].get("definition", "")
                    clean = re.sub(r"<[^>]+>", "", raw).strip()
                    if clean and len(clean) > 3:
                        return clean, None, ("Tamil Wiktionary", "b-wt")
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3 — MyMemory (free, no key, 5000 chars/day)
# ══════════════════════════════════════════════════════════════════════════════
def src_mymemory(word: str):
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"},
            timeout=3,
        )
        if r.status_code == 200:
            t = r.json().get("responseData", {}).get("translatedText", "")
            if (t and t.strip().lower() != word.lower()
                    and "INVALID" not in t.upper() and len(t.strip()) > 1):
                return t.strip(), None, ("MyMemory (Tamil→English)", "b-mm")
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 4 — Google Translate via deep-translator (free)
# ══════════════════════════════════════════════════════════════════════════════
def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.strip().lower() != word.lower():
            return t.strip(), None, ("Google Translate (free)", "b-gt")
    except Exception:
        pass
    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str) -> dict:
    candidates = all_candidates(word)
    results    = []
    root_used  = word

    # ── dictionary sources: try each candidate until one succeeds ──
    for cand in candidates:
        m, syn, meta = src_shabdkosh(cand)
        if m:
            root_used = cand
            results.append({"meaning": m, "synonyms": syn, "source": meta[0], "badge": meta[1]})
            break

    if not results:
        for cand in candidates:
            m, syn, meta = src_wiktionary(cand)
            if m:
                root_used = cand
                results.append({"meaning": m, "synonyms": syn, "source": meta[0], "badge": meta[1]})
                break

    # ── translation source: always add as supplementary ──
    m, syn, meta = src_mymemory(word)
    if m:
        # avoid duplicate if translation same as dictionary result
        existing = {r["meaning"].lower() for r in results}
        if m.lower() not in existing:
            results.append({"meaning": m, "synonyms": syn, "source": meta[0], "badge": meta[1]})
    else:
        m, syn, meta = src_google(word)
        if m:
            existing = {r["meaning"].lower() for r in results}
            if m.lower() not in existing:
                results.append({"meaning": m, "synonyms": syn, "source": meta[0], "badge": meta[1]})

    return {
        "word":     word,
        "root":     root_used,
        "results":  results,
        "found":    bool(results),
        "tried":    candidates,
    }


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO
# ══════════════════════════════════════════════════════════════════════════════
def speak(word: str) -> io.BytesIO | None:
    try:
        buf = io.BytesIO()
        gTTS(text=word, lang="ta", slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# OCR / EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════
def ocr_image(img) -> str:
    return pytesseract.image_to_string(img, config=r"--oem 3 --psm 6 -l tam+eng")

def extract_pdf(f) -> str:
    texts = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
    return "\n\n".join(texts)

def is_tamil(w: str) -> bool:
    return bool(re.search(r"[\u0B80-\u0BFF]", w))

def tokenize(text: str) -> list[str]:
    return re.findall(r"[\u0B80-\u0BFF]+|[A-Za-z0-9]+|[^\w]", text)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("text", ""), ("word", "")]:
    st.session_state.setdefault(k, v)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📜 Tamil Government Document Reader</h1>
  <p>Upload PDF or image · Extract full text · Search any Tamil word · Get exact meaning + pronunciation · 100% free</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
t_reader, t_deploy = st.tabs(["📄 Document Reader", "🚀 GitHub → Streamlit Cloud Guide"])


# ── TAB 1: READER ─────────────────────────────────────────────────────────────
with t_reader:
    left, right = st.columns([3, 2], gap="large")

    # ── LEFT PANEL ──────────────────────────────────────────────────────────
    with left:
        st.markdown('<div class="slabel">Step 1 — Upload Document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "file", type=["pdf", "png", "jpg", "jpeg"],
            label_visibility="collapsed",
        )

        if uploaded:
            with st.spinner("Extracting text from document…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("PDF has no selectable text — running OCR on first page…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs = convert_from_bytes(uploaded.getvalue(), first_page=1, last_page=1)
                            text = ocr_image(imgs[0]) if imgs else ""
                        except Exception as e:
                            st.error(f"OCR error: {e}")
                            text = ""
                else:
                    text = ocr_image(Image.open(uploaded))
                st.session_state.text = text

        if st.session_state.text:
            st.markdown(
                '<div class="slabel" style="margin-top:1.1rem">Step 2 — Read Document</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="hint">💡 Type any Tamil word in the search box on the right, '
                'or pick a word from the dropdown below to look up its meaning</div>',
                unsafe_allow_html=True,
            )

            # Rendered text box
            st.markdown(
                f'<div class="docbox">{st.session_state.text}</div>',
                unsafe_allow_html=True,
            )

            # Dropdown of all Tamil words in document
            tamil_words = sorted({
                t for t in tokenize(st.session_state.text)
                if is_tamil(t) and len(t) > 1
            })
            if tamil_words:
                st.markdown(
                    '<div class="slabel" style="margin-top:.75rem">Pick any Tamil word from the document</div>',
                    unsafe_allow_html=True,
                )
                pick = st.selectbox(
                    "Words:",
                    ["— select —"] + tamil_words,
                    label_visibility="collapsed",
                    key="pick",
                )
                if pick and pick != "— select —":
                    st.session_state.word = pick
        else:
            st.info("Upload a government document (PDF or image) above to begin.")

    # ── RIGHT PANEL ─────────────────────────────────────────────────────────
    with right:
        st.markdown('<div class="slabel">Word Meaning Lookup</div>', unsafe_allow_html=True)

        typed = st.text_input(
            "Type any Tamil word:",
            placeholder="உதாரணம்: விரும்பினால்",
            key="typed",
        )
        if typed:
            st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"Looking up '{w}'…"):
                res   = lookup(w)
                audio = speak(w)

            # ── Meaning card ──
            root_note = (
                f"&nbsp;← stripped from <strong>{res['word']}</strong>"
                if res["root"] != res["word"] else ""
            )
            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">Root used for search: <strong>{res['root']}</strong>{root_note}</div>
            """, unsafe_allow_html=True)

            if res["found"]:
                for r in res["results"]:
                    syn_html = (
                        f'<div class="msynonyms">Related Tamil words: {r["synonyms"]}</div>'
                        if r.get("synonyms") else ""
                    )
                    st.markdown(f"""
                    <div class="mrow">
                      <span class="badge {r['badge']}">{r['source']}</span>
                      <div class="mdef">{r['meaning']}</div>
                      {syn_html}
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="notfound">
                  No meaning found for <strong>{res['word']}</strong>
                  (or its root <strong>{res['root']}</strong>).<br>
                  All {len(res['tried'])} candidate forms tried. Try a shorter form.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # ── Audio ──
            if audio:
                st.markdown("**🔊 Pronunciation**")
                st.audio(audio, format="audio/mp3")

            # ── Debug expander ──
            with st.expander("🔍 All roots tried during lookup"):
                for i, c in enumerate(res["tried"], 1):
                    st.write(f"{i}. `{c}`")

        elif w:
            st.info("Please enter a word in Tamil script (தமிழ்).")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-size:.92rem;margin-top:.45rem">
                Type a Tamil word above<br>or pick one from the document
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("Sources: Shabdkosh → Tamil Wiktionary → MyMemory → Google Translate  |  All free, no API key")


# ── TAB 2: DEPLOY GUIDE ───────────────────────────────────────────────────────
with t_deploy:
    st.markdown("## 🚀 Connect GitHub → Streamlit Cloud (Free, One-Time Setup)")
    st.markdown("After setup, every time you save `app.py` on GitHub it **auto-deploys in ~60 seconds**.")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>Create GitHub account</strong> (free) →
      <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>New repository</strong> → click <code>+</code> → New repository<br>
      Name: <code>tamil-doc-reader</code> | Visibility: <strong>Public</strong> → Create repository
    </div>
    <div class="step"><span class="num">3</span>
      <strong>Upload 3 files</strong> to repo root → click "uploading an existing file" on GitHub<br>
      Drag & drop: &nbsp; <code>app.py</code> &emsp; <code>requirements.txt</code> &emsp; <code>packages.txt</code><br>
      → Commit changes
    </div>
    <div class="step"><span class="num">4</span>
      <strong>Open Streamlit Cloud</strong> →
      <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → Sign in with GitHub
    </div>
    <div class="step"><span class="num">5</span>
      Click <strong>New app</strong> → choose repo <code>tamil-doc-reader</code><br>
      Branch: <code>main</code> | Main file: <code>app.py</code> → <strong>Deploy!</strong>
    </div>
    <div class="step"><span class="num">6</span>
      Wait <strong>3–5 minutes</strong> for first build. Streamlit reads <code>packages.txt</code>
      and installs Tesseract Tamil OCR automatically.<br>
      Your free URL: <code>https://yourname-tamil-doc-reader.streamlit.app</code> ✅
    </div>
    <div class="step"><span class="num">7</span>
      <strong>Future updates:</strong> edit <code>app.py</code> on GitHub → commit →
      Streamlit Cloud auto-redeploys. No manual steps needed.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Exact file contents to upload")
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
        st.markdown("**`packages.txt`** ← system packages for Tesseract OCR")
        st.code(
            "tesseract-ocr\n"
            "tesseract-ocr-tam\n"
            "tesseract-ocr-eng\n"
            "poppler-utils",
            language="text",
        )
    st.success("✅ Zero paid services. Zero API keys. Zero server management. Just 3 files on GitHub.")

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.75rem;color:#bbb;
  margin-top:2rem;padding-top:.8rem;border-top:1px solid #ddd4c4;">
  Tamil Govt Document Reader ·
  OCR: Tesseract ·
  Dictionary: Shabdkosh + Tamil Wiktionary + MyMemory + Google Translate ·
  Audio: gTTS · 100% Free
</div>
""", unsafe_allow_html=True)
