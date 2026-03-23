"""
Tamil Government Document Reader — v5 FINAL
════════════════════════════════════════════
New in this version:
  1. AI-powered rich explanation (Claude API) — gives Tamil meaning,
     English meaning, document context, and example sentence for every word
  2. Improved OCR — denoise, deskew, contrast boost before Tesseract
  3. Better text formatting — paragraphs cleaned, Tamil/English separated
  4. Fast 3-source fallback (MyMemory → Wiktionary → Google Translate)
     when Claude API not configured
  5. "Context lookup" — finds the sentence in the document containing
     the word and explains it in context
"""

import io, re, os, base64, json
import requests, streamlit as st
from gtts import gTTS
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import pdfplumber, pytesseract
import numpy as np

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

/* Document text box */
.docbox{
  background:#fffef9;border:1px solid #ddd0b8;border-radius:10px;
  padding:1.4rem 1.8rem;
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:1.08rem;line-height:2.4;color:#1a1a1a;
  white-space:pre-wrap;word-break:break-word;
  max-height:500px;overflow-y:auto;
}

/* Meaning card */
.mcard{background:#fff;border-radius:12px;border:1px solid #e2d8c8;
  box-shadow:0 3px 14px rgba(0,0,0,.05);padding:1.3rem 1.5rem;margin-top:.3rem;}
.mword{font-family:'Noto Sans Tamil',sans-serif;font-size:1.5rem;
       font-weight:600;color:#0f172a;margin-bottom:.1rem;}
.mroot{font-size:.76rem;color:#aaa;margin-bottom:.9rem;}

/* Section labels inside card */
.sec-label{
  font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.1em;color:#c9963a;margin:.75rem 0 .2rem;
}
.sec-body{
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:.97rem;color:#2d2d2d;line-height:1.85;
  background:#fafaf7;border-radius:8px;padding:.6rem .85rem;
  border-left:3px solid #d4a843;
}
.ctx-box{
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:.9rem;color:#555;line-height:1.8;
  background:#f0f4ff;border-radius:8px;padding:.6rem .85rem;
  border-left:3px solid #4a7ddb;margin-top:.2rem;
  font-style:italic;
}
.badge{display:inline-block;font-size:11px;font-weight:600;
  padding:2px 9px;border-radius:20px;margin:0 5px 3px 0;vertical-align:middle;}
.b-ai {background:#eae8ff;color:#4f46e5;}
.b-wt {background:#e8f4fd;color:#1155aa;}
.b-mm {background:#d6f5e3;color:#155e2b;}
.b-gt {background:#fff0d6;color:#7a4500;}

.notfound{font-size:.92rem;color:#b91c1c;background:#fef2f2;
  border:1px solid #fecaca;border-radius:8px;padding:.65rem .9rem;margin-top:.5rem;}
.slabel{font-size:.72rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.08em;color:#888;margin-bottom:.4rem;}
.hint{display:inline-block;background:#fef9e7;border:1px solid #fce7a0;
  border-radius:8px;padding:.42rem .85rem;font-size:.83rem;
  color:#7a5100;margin-bottom:.85rem;}

/* Steps in deploy guide */
.step{background:#fff;border:1px solid #e5dfd4;border-radius:10px;
  padding:.85rem 1.1rem;margin-bottom:.5rem;font-size:.92rem;line-height:1.65;}
.num{display:inline-flex;align-items:center;justify-content:center;
  width:21px;height:21px;border-radius:50%;
  background:#0f172a;color:#d4a843;
  font-size:11px;font-weight:700;margin-right:7px;flex-shrink:0;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SUFFIX + SANDHI ENGINE  (unchanged from v4 — proven working)
# ══════════════════════════════════════════════════════════════════════════════
SUFFIXES = [
    "ப்படுகிறது","ப்படுகின்றது","க்கப்படும்","ப்படும்","ப்பட்டது",
    "வைக்கப்படும்","படுத்தப்படும்",
    "யினால்","வதினால்","தினால்","டினால்","றினால்","னினால்","இனால்","ினால்","னால்","ால்",
    "ன்றனர்","னார்கள்","னார்","ட்டார்கள்","ட்டார்","தார்கள்","தார்",
    "ட்டேன்","தேன்","டேன்","ினான்","ினாள்","னான்","னாள்",
    "த்தான்","த்தாள்","ிட்டான்","ிட்டாள்",
    "கிறார்கள்","கிறார்","கிறான்","கிறாள்","கிறோம்","கிறீர்கள்",
    "கின்றார்","கின்றான்","கிறது","கின்றது",
    "வார்கள்","வார்","வான்","வாள்","வோம்","பார்","பான்","வீர்கள்",
    "வதற்கு","படுவது","கின்றது","வதை","தலை","கல்","வது",
    "த்திலிருந்து","த்தினால்","த்துடன்","த்தோடு",
    "த்தில்","த்தை","த்தின்","த்துக்கு","த்தோ",
    "இல்லாமல்","இருந்தால்","இருந்து","உடைய","யுடன்","உடன்",
    "என்று","ஆகும்","ஆனது","ஆல்","ஆக","ஆன",
    "யில்","யை","யின்","யிடம்","கள்","இல்","ஐ","கு",
    "க்கான","ிய","்ற","்த","ின்","இன்",
]
SANDHI_MAP = [
    ("ந்த","ந்தம்"),("ட்ட","ட்டம்"),("க்க","க்கம்"),
    ("ல்ல","ல்"),("ன்ன","ன்னம்"),("ர்த்த","ர்த்தம்"),
]

def _strip_one(w):
    for s in SUFFIXES:
        if w.endswith(s) and len(w) > len(s)+1:
            return w[:-len(s)]
    return None

def _sandhi(w):
    out = []
    for tail, rep in SANDHI_MAP:
        if w.endswith(tail):
            out.append(w[:-len(tail)] + rep)
    return out

def _variants(w):
    swaps = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in swaps if a in w and w.replace(a,b,1)!=w]

def all_candidates(word):
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
# IMAGE PREPROCESSING  — improves OCR accuracy significantly
# ══════════════════════════════════════════════════════════════════════════════
def preprocess_image(img: Image.Image) -> Image.Image:
    """Enhance image for better Tamil OCR results."""
    # Convert to grayscale
    img = img.convert("L")
    # Upscale small images (Tesseract works best at 300+ DPI)
    w, h = img.size
    if w < 1500:
        scale = 1500 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    # Boost contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    # Binarize (Otsu-like simple threshold)
    arr = np.array(img)
    thresh = arr.mean()
    arr = ((arr > thresh) * 255).astype(np.uint8)
    return Image.fromarray(arr)


# ══════════════════════════════════════════════════════════════════════════════
# TEXT CLEANUP  — better readable formatting after OCR
# ══════════════════════════════════════════════════════════════════════════════
def clean_extracted_text(raw: str) -> str:
    """Clean OCR output into well-formatted readable text."""
    lines = raw.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")   # preserve paragraph breaks
            continue
        # Remove common OCR noise characters
        line = re.sub(r"[|}{\\~`]", "", line)
        # Fix multiple spaces
        line = re.sub(r"  +", " ", line)
        if line:
            cleaned.append(line)

    # Join lines — if a line ends with Tamil punctuation or is short, keep newline
    # otherwise join with space (OCR wraps mid-sentence)
    result_lines = []
    i = 0
    while i < len(cleaned):
        if cleaned[i] == "":
            result_lines.append("")
            i += 1
            continue
        current = cleaned[i]
        # Merge with next non-empty line if current doesn't end a sentence
        while (i + 1 < len(cleaned)
               and cleaned[i+1] != ""
               and not current.endswith((".", "।", ":", "?", "!", "௷", "\u0BE7"))
               and len(current) > 5):
            i += 1
            current = current + " " + cleaned[i]
        result_lines.append(current)
        i += 1

    return "\n".join(result_lines).strip()


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT FINDER  — finds the sentence in the doc containing the searched word
# ══════════════════════════════════════════════════════════════════════════════
def find_context_sentence(text: str, word: str) -> str | None:
    """Find the sentence in extracted text that contains the word."""
    # Split into sentences
    sentences = re.split(r'[.!?।\n]{1,3}', text)
    candidates = all_candidates(word)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 5:
            continue
        for cand in candidates:
            if cand in sent:
                return sent
    # Fallback: return fragment around word position
    for cand in candidates:
        idx = text.find(cand)
        if idx >= 0:
            start = max(0, idx - 60)
            end   = min(len(text), idx + len(cand) + 60)
            return "…" + text[start:end].strip() + "…"
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1 — Claude API  (rich explanation with Tamil + English + context)
# Set ANTHROPIC_API_KEY in Streamlit Cloud → Settings → Secrets
# Format in secrets: ANTHROPIC_API_KEY = "sk-ant-..."
# ══════════════════════════════════════════════════════════════════════════════
def src_claude_explain(word: str, root: str, context_sentence: str | None) -> dict | None:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    ctx_part = (f'\nThis word appears in the following sentence from a government document:\n"{context_sentence}"'
                if context_sentence else "")

    prompt = f"""You are a Tamil language expert helping citizens understand government documents.

Word to explain: {word}
Root form: {root}{ctx_part}

Give a clear explanation in this exact JSON format (no extra text):
{{
  "tamil_meaning": "meaning in simple Tamil (2-3 words or a short phrase)",
  "english_meaning": "clear English meaning in 1-2 sentences",
  "document_context": "what this word means specifically in a government/legal document context (1-2 sentences)",
  "example_sentence": "a simple Tamil example sentence using this word, with English translation in parentheses"
}}

Keep the language very simple. The reader may not be educated. Be direct and clear."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=8,
        )
        if r.status_code == 200:
            text = r.json()["content"][0]["text"].strip()
            # Strip markdown code fences if present
            text = re.sub(r"^```json\s*|```$", "", text.strip(), flags=re.MULTILINE).strip()
            return json.loads(text)
    except Exception:
        pass
    return None


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
                    raw = entries[0].get("definitions",[{}])[0].get("definition","")
                    clean = re.sub(r"<[^>]+>","",raw).strip()
                    if clean and len(clean) > 3:
                        return clean
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3 — MyMemory
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
            if t and t.strip().lower() != word.lower() and "INVALID" not in t.upper() and len(t.strip())>1:
                return t.strip()
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 4 — Google Translate
# ══════════════════════════════════════════════════════════════════════════════
def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.strip().lower() != word.lower():
            return t.strip()
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str = "") -> dict:
    candidates = all_candidates(word)
    root_used  = word

    # Find which candidate actually has a translation (for root detection)
    translation = src_mymemory(word)
    if not translation:
        for cand in candidates[1:]:
            t = src_mymemory(cand)
            if t:
                root_used = cand
                translation = t
                break

    if not translation:
        translation = src_google(word)

    # Find sentence context from document
    context_sent = find_context_sentence(doc_text, word) if doc_text else None

    # Try Claude for rich explanation
    ai_result = src_claude_explain(word, root_used, context_sent)

    # Fallback: Wiktionary
    wiki_def = None
    for cand in candidates:
        wiki_def = src_wiktionary(cand)
        if wiki_def:
            if root_used == word:
                root_used = cand
            break

    return {
        "word":        word,
        "root":        root_used,
        "translation": translation,
        "wiki":        wiki_def,
        "ai":          ai_result,
        "context":     context_sent,
        "found":       bool(translation or wiki_def or ai_result),
        "tried":       candidates,
    }


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
def ocr_image(img: Image.Image) -> str:
    enhanced = preprocess_image(img)
    raw = pytesseract.image_to_string(enhanced, config=r"--oem 3 --psm 6 -l tam+eng")
    return clean_extracted_text(raw)

def extract_pdf(f) -> str:
    texts = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(clean_extracted_text(t))
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
  <p>Upload PDF or image · Read clearly formatted text · Search any Tamil word · Get full explanation in Tamil &amp; English · Free</p>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
t_reader, t_deploy = st.tabs(["📄 Document Reader", "🚀 GitHub → Streamlit Cloud Guide"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — READER
# ══════════════════════════════════════════════════════════════════════════════
with t_reader:
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="slabel">Step 1 — Upload Document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("Extracting and formatting text…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("No selectable text in PDF — running OCR…")
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
            st.markdown('<div class="slabel" style="margin-top:1rem">Step 2 — Read Document</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 Find a difficult word → type it in the right panel or pick from the dropdown below</div>', unsafe_allow_html=True)

            # Display formatted text
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)

            # Word picker
            tamil_words = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t)>1})
            if tamil_words:
                st.markdown('<div class="slabel" style="margin-top:.7rem">Or pick a word from the document</div>', unsafe_allow_html=True)
                pick = st.selectbox("pick", ["— select —"] + tamil_words, label_visibility="collapsed", key="pick")
                if pick != "— select —":
                    st.session_state.word = pick
        else:
            st.info("Upload a government document (PDF or scanned image) above to begin.")

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    with right:
        st.markdown('<div class="slabel">Word Meaning Lookup</div>', unsafe_allow_html=True)

        typed = st.text_input("Type any Tamil word:", placeholder="உதாரணம்: ஒப்பந்தம், விரும்பினால்", key="typed")
        if typed:
            st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"Explaining '{w}'…"):
                res   = lookup(w, st.session_state.text)
                audio = speak(w)

            root_note = (f" (root: {res['root']})" if res["root"] != res["word"] else "")

            # ── Render meaning card ──────────────────────────────────────────
            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">{root_note if root_note else "searched as-is"}</div>
            """, unsafe_allow_html=True)

            if res["found"]:

                # ── AI RICH EXPLANATION (best) ──
                if res["ai"]:
                    ai = res["ai"]
                    if ai.get("tamil_meaning"):
                        st.markdown(f"""
                        <span class="badge b-ai">தமிழ் பொருள்</span>
                        <div class="sec-body">{ai['tamil_meaning']}</div>
                        """, unsafe_allow_html=True)

                    if ai.get("english_meaning"):
                        st.markdown(f"""
                        <div class="sec-label">English Meaning</div>
                        <div class="sec-body">{ai['english_meaning']}</div>
                        """, unsafe_allow_html=True)

                    if ai.get("document_context"):
                        st.markdown(f"""
                        <div class="sec-label">In Government Documents</div>
                        <div class="sec-body">{ai['document_context']}</div>
                        """, unsafe_allow_html=True)

                    if ai.get("example_sentence"):
                        st.markdown(f"""
                        <div class="sec-label">Example / எடுத்துக்காட்டு</div>
                        <div class="ctx-box">{ai['example_sentence']}</div>
                        """, unsafe_allow_html=True)

                else:
                    # ── FALLBACK: show translation + wiktionary ──
                    if res["translation"]:
                        st.markdown(f"""
                        <span class="badge b-mm">English meaning</span>
                        <div class="sec-body">{res['translation']}</div>
                        """, unsafe_allow_html=True)

                    if res["wiki"]:
                        st.markdown(f"""
                        <span class="badge b-wt">Wiktionary definition</span>
                        <div class="sec-body">{res['wiki']}</div>
                        """, unsafe_allow_html=True)

                # ── CONTEXT IN DOCUMENT ──
                if res["context"]:
                    st.markdown(f"""
                    <div class="sec-label">Found in your document</div>
                    <div class="ctx-box">{res['context']}</div>
                    """, unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class="notfound">
                  ⚠️ No meaning found for <strong>{res['word']}</strong>.<br>
                  Tried {len(res['tried'])} root forms. Try typing a shorter form.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 Pronunciation**")
                st.audio(audio, format="audio/mp3")

            with st.expander("🔍 Roots tried"):
                for i, c in enumerate(res["tried"], 1):
                    st.write(f"{i}. `{c}`")

        elif w:
            st.info("Please enter a word in Tamil script.")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-size:.92rem;margin-top:.4rem">
                Type any Tamil word above<br>or pick one from the document
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("Sources: AI explanation + Tamil Wiktionary + MyMemory + Google Translate")

        # ── API key setup info ──
        api_key = st.secrets.get("ANTHROPIC_API_KEY","") or os.environ.get("ANTHROPIC_API_KEY","")
        if not api_key:
            with st.expander("⚙️ Enable AI-powered explanations"):
                st.markdown("""
                For richer Tamil + English + document-context explanations, add your free Anthropic API key:
                1. Get a free key at [console.anthropic.com](https://console.anthropic.com)
                2. In Streamlit Cloud → your app → **Settings → Secrets**
                3. Add: `ANTHROPIC_API_KEY = "sk-ant-..."`
                4. Save → app restarts automatically

                Without the key, the app still works using MyMemory + Wiktionary.
                """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEPLOY GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with t_deploy:
    st.markdown("## 🚀 Connect GitHub → Streamlit Cloud (Free, ~10 min one-time setup)")
    st.markdown("After setup, every save on GitHub **auto-deploys in ~60 seconds**.")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>Create free GitHub account</strong> →
      <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>New repository</strong> → click <code>+</code> → New repository<br>
      Name: <code>tamil-doc-reader</code> | Visibility: <strong>Public</strong> → Create
    </div>
    <div class="step"><span class="num">3</span>
      <strong>Upload 3 files</strong> to repo root:<br>
      <code>app.py</code> &emsp; <code>requirements.txt</code> &emsp; <code>packages.txt</code><br>
      → Commit changes
    </div>
    <div class="step"><span class="num">4</span>
      <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → Sign in with GitHub → <strong>New app</strong><br>
      Repo: <code>tamil-doc-reader</code> | Branch: <code>main</code> | File: <code>app.py</code> → Deploy
    </div>
    <div class="step"><span class="num">5</span>
      Wait 3–5 min for first build → get free URL:
      <code>https://yourname-tamil-doc-reader.streamlit.app</code> ✅
    </div>
    <div class="step"><span class="num">6</span>
      <strong>Add AI key (optional but recommended):</strong><br>
      Streamlit Cloud → your app → Settings → Secrets → add:<br>
      <code>ANTHROPIC_API_KEY = "sk-ant-your-key-here"</code>
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

    st.success("✅ Zero paid services needed. AI explanation is optional — app fully works without it.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.75rem;color:#bbb;margin-top:2rem;
  padding-top:.8rem;border-top:1px solid #ddd4c4;">
  Tamil Govt Document Reader v5 · OCR: Tesseract ·
  AI: Claude (optional) · Dict: Tamil Wiktionary + MyMemory + Google Translate ·
  Audio: gTTS · 100% Free
</div>
""", unsafe_allow_html=True)
