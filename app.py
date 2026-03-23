"""
Tamil Government Document Reader
─────────────────────────────────
Meaning sources tried in order:
  1. Tamil Wiktionary REST API         (dictionary definition)
  2. agarathi.com web-page scrape      (100k+ words, free web scrape)
  3. MyMemory free translation API     (Tamil → English)
  4. Google Translate via deep-translator (final fallback)

Suffix engine strips up to 5 layers so inflected government-document
words like பயன்படுத்தப்படும் reach their root பயன்படுத்து.
"""

import streamlit as st
import pytesseract
from PIL import Image
import pdfplumber
import requests
from bs4 import BeautifulSoup
import re
import io
from gtts import gTTS

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Tamil Govt Document Reader", page_icon="📜", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{ font-family:'IBM Plex Sans',sans-serif; }
.stApp{ background:#f4f1ec; }

.header{
  background:#0f172a; border-left:5px solid #d4a843;
  border-radius:12px; padding:1.6rem 2rem; margin-bottom:1.4rem;
}
.header h1{ color:#f8ecd4; font-size:1.7rem; font-weight:600; margin:0 0 .25rem; }
.header p { color:#a89880; font-size:.9rem; margin:0; }

/* text display */
.doc-box{
  background:#fffef9; border:1px solid #ddd0b8; border-radius:10px;
  padding:1.4rem 1.7rem;
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:1.05rem; line-height:2.3; color:#1e1e1e;
  white-space:pre-wrap; word-break:break-word;
  max-height:460px; overflow-y:auto;
}

/* meaning panel */
.mcard{
  background:#fff; border-radius:12px; border:1px solid #e2d8c8;
  box-shadow:0 3px 12px rgba(0,0,0,.05); padding:1.3rem 1.5rem;
}
.mword { font-family:'Noto Sans Tamil',sans-serif; font-size:1.5rem; font-weight:600; color:#0f172a; }
.mroot { font-size:.78rem; color:#999; margin:.15rem 0 .8rem; }
.mrow  { margin-bottom:.85rem; }
.badge {
  display:inline-block; font-size:11px; font-weight:600;
  padding:2px 9px; border-radius:20px; margin-right:5px; margin-bottom:3px;
}
.b1{ background:#e0f0ff; color:#1155aa; }   /* wiktionary  */
.b2{ background:#d6f5e3; color:#156030; }   /* agarathi    */
.b3{ background:#fff0d6; color:#8a4e00; }   /* mymemory    */
.b4{ background:#fde8e8; color:#8b1a1a; }   /* google      */
.mdef{
  font-size:.96rem; color:#333; line-height:1.75;
  border-left:3px solid #d4a843; padding-left:.75rem; margin-top:.25rem;
}
.notfound{
  font-size:.93rem; color:#b91c1c; background:#fef2f2;
  border:1px solid #fecaca; border-radius:8px; padding:.65rem .9rem;
}
.slabel{
  font-size:.72rem; font-weight:600; text-transform:uppercase;
  letter-spacing:.08em; color:#888; margin-bottom:.4rem;
}
.hint{
  display:inline-block; background:#fef9e7; border:1px solid #fce7a0;
  border-radius:8px; padding:.45rem .85rem; font-size:.84rem;
  color:#7a5100; margin-bottom:.9rem;
}
.step{
  background:#fff; border:1px solid #e5dfd4; border-radius:10px;
  padding:.9rem 1.1rem; margin-bottom:.55rem; font-size:.93rem; line-height:1.6;
}
.num{
  display:inline-flex; align-items:center; justify-content:center;
  width:22px; height:22px; border-radius:50%;
  background:#0f172a; color:#d4a843;
  font-size:12px; font-weight:700; margin-right:8px; flex-shrink:0;
}
</style>
""", unsafe_allow_html=True)

# ── Tamil suffix database (longest → shortest, strips layered inflections) ────
# Government docs heavily use causative, passive, and case suffixes.
SUFFIX_LAYERS = [
    # 5-letter+
    "படுத்தப்படும்", "செய்யப்பட்டது", "வைக்கப்படும்",
    "இல்லாமல்",  "இருந்தால்",  "பட்டிருக்கும்",
    # 4-letter
    "படுத்தல்",  "இருக்கும்",  "யிருந்து", "வைத்தல்",
    "கொண்டு",   "விட்டது",   "என்பது",
    # 3-letter
    "உடன்",  "இல்",   "இருந்து", "ஆகும்",
    "ஆனது",  "என்று", "யுடன்",  "படும்",
    "வரும்",  "தரும்",
    # 2-letter
    "ஆல்", "ஆக", "ஆன", "கள்", "இல்", "கு",
    # 1-letter
    "ஐ",
]

def strip_suffix_once(word: str) -> str | None:
    for s in SUFFIX_LAYERS:
        if word.endswith(s) and len(word) > len(s) + 1:
            return word[: -len(s)]
    return None

def get_roots(word: str) -> list[str]:
    """Return word + up to 5 progressively stripped roots, deduplicated."""
    seen, forms = set(), [word]
    seen.add(word)
    cur = word
    for _ in range(5):
        nxt = strip_suffix_once(cur)
        if nxt and nxt not in seen:
            forms.append(nxt)
            seen.add(nxt)
            cur = nxt
        else:
            break
    return forms

def spelling_variants(word: str) -> list[str]:
    """Common ர/ற ல/ள confusions in government Tamil."""
    swaps = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    out = []
    for a, b in swaps:
        if a in word:
            v = word.replace(a, b, 1)
            if v != word:
                out.append(v)
    return out

def all_candidates(word: str) -> list[str]:
    """All forms to try: roots + spelling variants at each root level."""
    cands, seen = [], set()
    for root in get_roots(word):
        for form in [root] + spelling_variants(root):
            if form not in seen:
                cands.append(form)
                seen.add(form)
    return cands


# ── Source 1: Tamil Wiktionary ────────────────────────────────────────────────
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
                        return clean, "Tamil Wiktionary", "b1"
    except Exception:
        pass
    return None, None, None


# ── Source 2: agarathi.com public web scrape ──────────────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def src_agarathi(word: str):
    """
    Scrapes the agarathi.com public search page (not their paid API).
    URL pattern: https://agarathi.com/word/<encoded-word>
    The meaning is inside <div class="meaning"> or <p class="description">.
    """
    try:
        url = f"https://agarathi.com/word/{requests.utils.quote(word)}"
        r = requests.get(url, headers=_HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Try several selectors — agarathi occasionally changes markup
            for sel in [
                "div.meaning", "div.description", "p.description",
                "div.def",     "div.content p",    "section.meaning",
            ]:
                tag = soup.select_one(sel)
                if tag:
                    text = tag.get_text(separator=" ", strip=True)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text and len(text) > 4:
                        return text, "agarathi.com (web)", "b2"
            # Fallback: grab first <p> that contains Tamil characters
            for p in soup.find_all("p"):
                t = p.get_text(strip=True)
                if re.search(r"[\u0B80-\u0BFF]", t) and len(t) > 4:
                    return t, "agarathi.com (web)", "b2"
    except Exception:
        pass
    return None, None, None


# ── Source 3: MyMemory free translation ──────────────────────────────────────
def src_mymemory(word: str):
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"},
            timeout=3,
        )
        if r.status_code == 200:
            t = r.json().get("responseData", {}).get("translatedText", "")
            if t and t.strip().lower() != word.lower() and "INVALID" not in t.upper() and len(t.strip()) > 1:
                return t.strip(), "MyMemory (Tamil→English)", "b3"
    except Exception:
        pass
    return None, None, None


# ── Source 4: Google Translate via deep-translator ───────────────────────────
def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.strip().lower() != word.lower():
            return t.strip(), "Google Translate (free)", "b4"
    except Exception:
        pass
    return None, None, None


# ── Orchestrator ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str) -> dict:
    """
    Returns:
        {word, root, results:[{meaning,source,badge}], found}
    Dictionary sources searched on every root candidate.
    Translation sources searched once on original word.
    """
    candidates = all_candidates(word)
    results = []
    root_used = word

    # --- dictionary sources: Wiktionary then agarathi, stop when found -------
    for candidate in candidates:
        m, src, badge = src_wiktionary(candidate)
        if m:
            root_used = candidate
            results.append({"meaning": m, "source": src, "badge": badge})
            break

    if not results:
        for candidate in candidates:
            m, src, badge = src_agarathi(candidate)
            if m:
                root_used = candidate
                results.append({"meaning": m, "source": src, "badge": badge})
                break

    # --- translation sources: always add as supplementary info ---------------
    m, src, badge = src_mymemory(word)
    if m:
        results.append({"meaning": m, "source": src, "badge": badge})
    else:
        m, src, badge = src_google(word)
        if m:
            results.append({"meaning": m, "source": src, "badge": badge})

    return {"word": word, "root": root_used, "results": results, "found": bool(results)}


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word: str):
    try:
        buf = io.BytesIO()
        gTTS(text=word, lang="ta", slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ── OCR / extraction helpers ─────────────────────────────────────────────────
def ocr_image(img):
    return pytesseract.image_to_string(img, config=r"--oem 3 --psm 6 -l tam+eng")

def extract_pdf(f):
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


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("text", ""), ("word", "")]:
    st.session_state.setdefault(k, v)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header">
  <h1>📜 Tamil Government Document Reader</h1>
  <p>Upload any PDF or image · Extract full text · Instant meaning for any Tamil word · 100 % free</p>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
t1, t2 = st.tabs(["📄 Document Reader", "🚀 Deploy Guide (GitHub → Streamlit Cloud)"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — READER
# ════════════════════════════════════════════════════════════════════════════════
with t1:
    left, right = st.columns([3, 2], gap="large")

    # ── LEFT: upload + text display ──
    with left:
        st.markdown('<div class="slabel">Step 1 — Upload document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("File", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("Extracting text…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("No selectable text — running OCR on first page…")
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
            st.markdown('<div class="slabel" style="margin-top:1.1rem">Step 2 — Read &amp; pick a word</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 Type a Tamil word below, or choose one from the dropdown</div>', unsafe_allow_html=True)

            typed = st.text_input("Type Tamil word:", placeholder="உதாரணம்: அக்கறை", key="typed")
            if typed:
                st.session_state.word = typed.strip()

            st.markdown(f'<div class="doc-box">{st.session_state.text}</div>', unsafe_allow_html=True)

            tamil_words = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t) > 1})
            if tamil_words:
                st.markdown('<div class="slabel" style="margin-top:.7rem">Or pick from document</div>', unsafe_allow_html=True)
                pick = st.selectbox("Pick:", ["— select —"] + tamil_words, label_visibility="collapsed", key="pick")
                if pick and pick != "— select —":
                    st.session_state.word = pick
        else:
            st.info("Upload a government document above to begin reading.")

    # ── RIGHT: meaning panel ──
    with right:
        st.markdown('<div class="slabel">Word meaning</div>', unsafe_allow_html=True)
        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"Looking up '{w}'…"):
                res   = lookup(w)
                audio = speak(w)

            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">Root found: <strong>{res['root']}</strong>
                {'&nbsp;(after suffix stripping)' if res['root'] != res['word'] else ''}
              </div>
            """, unsafe_allow_html=True)

            if res["found"]:
                for r in res["results"]:
                    st.markdown(f"""
                    <div class="mrow">
                      <span class="badge {r['badge']}">{r['source']}</span>
                      <div class="mdef">{r['meaning']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="notfound">
                  No meaning found for <strong>{res['word']}</strong> or its root
                  <strong>{res['root']}</strong>.<br>
                  Try typing a shorter/simpler form of the word.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 Pronunciation**")
                st.audio(audio, format="audio/mp3")

            # show what roots were tried (debug help for users)
            with st.expander("🔍 Roots tried during lookup"):
                for i, c in enumerate(all_candidates(w)):
                    st.write(f"{i+1}. `{c}`")

        elif w:
            st.info("Please enter a word in Tamil script (தமிழ்).")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-size:.93rem;margin-top:.4rem">
                Select or type a Tamil word<br>to see its meaning here
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("Sources: Tamil Wiktionary → agarathi.com (web) → MyMemory → Google Translate")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEPLOY GUIDE
# ════════════════════════════════════════════════════════════════════════════════
with t2:
    st.markdown("## 🚀 Connect GitHub to Streamlit Cloud — Step by Step")
    st.markdown("**One-time setup (~10 min). After that, every save on GitHub auto-deploys.**")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>Create a free GitHub account</strong> —
      go to <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>Create a new repository</strong> —
      click <code>+</code> → <em>New repository</em><br>
      Name: <code>tamil-doc-reader</code> &nbsp;|&nbsp; Visibility: <strong>Public</strong> → <em>Create repository</em>
    </div>
    <div class="step"><span class="num">3</span>
      <strong>Upload all 3 files</strong> to the repo root —
      click <em>"uploading an existing file"</em> on GitHub, then drag &amp; drop:<br>
      &nbsp;&nbsp;📄 <code>app.py</code> &emsp; 📄 <code>requirements.txt</code> &emsp; 📄 <code>packages.txt</code><br>
      Scroll down → <em>Commit changes</em>
    </div>
    <div class="step"><span class="num">4</span>
      <strong>Open Streamlit Cloud</strong> —
      go to <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → <strong>Sign in with GitHub</strong>
    </div>
    <div class="step"><span class="num">5</span>
      <strong>Deploy your app</strong> — click <em>New app</em><br>
      Repository: <code>tamil-doc-reader</code> &nbsp;|&nbsp;
      Branch: <code>main</code> &nbsp;|&nbsp;
      Main file: <code>app.py</code> → <em>Deploy!</em>
    </div>
    <div class="step"><span class="num">6</span>
      <strong>Wait 3–5 min</strong> for first build — Streamlit reads
      <code>packages.txt</code> and installs Tesseract + Tamil OCR automatically.<br>
      You get a free URL: <code>https://yourname-tamil-doc-reader.streamlit.app</code>
    </div>
    <div class="step"><span class="num">7</span>
      <strong>Future updates</strong> — edit <code>app.py</code> on GitHub →
      commit → Streamlit Cloud auto-redeploys in ~60 seconds. ✅
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 File contents to copy into GitHub")

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
        st.markdown("**`packages.txt`** ← tells Streamlit Cloud to install system packages")
        st.code(
            "tesseract-ocr\n"
            "tesseract-ocr-tam\n"
            "tesseract-ocr-eng\n"
            "poppler-utils",
            language="text",
        )

    st.success("✅ No paid services. No API keys. Nothing to configure. Just upload 3 files and deploy.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.76rem;color:#bbb;margin-top:2rem;
  padding-top:.8rem;border-top:1px solid #ddd4c4;">
  Tamil Govt Document Reader ·
  OCR: Tesseract · Sources: Tamil Wiktionary, agarathi.com, MyMemory, Google Translate ·
  Audio: gTTS · 100 % Free
</div>
""", unsafe_allow_html=True)
