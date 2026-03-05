import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
import wikipediaapi

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="நிகண்டு | Digital Tamil Lexicon",
    layout="wide"
)

# ---------------- THEME ----------------
def apply_theme():
    bg = "https://www.transparenttextures.com/patterns/papyrus.png"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
    .stApp {{
        background-image: url("{bg}");
        background-color: #F7E7CE;
        font-family: 'Pavanam', sans-serif;
        color: #3E2723;
    }}
    .title {{
        font-family: 'Arima Madurai', cursive;
        text-align: center;
        color: #800000;
        font-size: 3.2rem;
    }}
    .card {{
        background: #fff;
        padding: 18px;
        border-left: 8px solid #800000;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
        border-radius: 6px;
    }}
    .label {{
        font-weight: bold;
        color: #1B5E20;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ---------------- OCR ----------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Ensure Tesseract has Tamil data installed
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

# ---------------- ROOT NORMALIZATION ----------------
def normalize_word(word):
    suffixes = ["இல்", "இன்", "ஆல்", "உடன்", "க்கு", "கள்", "து", "தை", "ன்", "யை", "இய", "ஆ"]
    for suf in suffixes:
        if word.endswith(suf) and len(word) > len(suf) + 1:
            return word[:-len(suf)]
    return word

# ---------------- WIKTIONARY API (New Live Search) ----------------
def search_wiktionary(word):
    """Fetches definitions from Tamil Wiktionary API"""
    WIKTIONARY_URL = "https://ta.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": word,
        "prop": "extracts",
        "explaintext": True,
        "exintro": True
    }
    try:
        response = requests.get(WIKTIONARY_URL, params=params, timeout=5)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, content in pages.items():
            if page_id != "-1":
                extract = content.get("extract", "")
                if extract:
                    # Return first few descriptive lines
                    return "\n".join(extract.split("\n")[:5]), "Live Wiktionary"
    except:
        pass
    return None, None

# ---------------- WIKIPEDIA (Fallback) ----------------
wiki_ta = wikipediaapi.Wikipedia(
    user_agent="NiganduLexicon/1.0",
    language="ta",
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

def search_wikipedia(word):
    page = wiki_ta.page(word)
    if page.exists():
        return page.summary[:800], "Tamil Wikipedia"
    return None, None

# ---------------- MAIN SEARCH LOGIC ----------------
def get_meaning(word):
    word = word.strip()
    root = normalize_word(word)

    # 1) Try Wiktionary (Direct)
    meaning, source = search_wiktionary(word)
    if meaning: return meaning, source

    # 2) Try Wiktionary (Root)
    if root != word:
        meaning, source = search_wiktionary(root)
        if meaning: return meaning, f"Wiktionary (Root: {root})"

    # 3) Fallback to Wikipedia
    meaning, source = search_wikipedia(word)
    if meaning: return meaning, source

    return None, None

# ---------------- UI LAYOUT ----------------
st.markdown("<h1 class='title'>நிகண்டு</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📜 ஆவண ஆய்வு (OCR)")
    file = st.file_uploader("PDF / Image", type=["pdf", "png", "jpg", "jpeg"])
    if file:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                text = "\n".join(
                    process_ocr(p.to_image(resolution=300).original)
                    for p in pdf.pages
                )
        else:
            text = process_ocr(Image.open(file))
        st.text_area("பிரித்தெடுக்கப்பட்ட உரை", text, height=300)

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    query = st.text_input("ஒரு தமிழ் சொல்லை உள்ளிடவும்")

    if query:
        meaning, source = get_meaning(query)
        if meaning:
            st.markdown(f"""
            <div class="card">
                <p style="font-size:0.85rem;color:#555;">ஆதாரம்: {source}</p>
                <h2 style="color:#800000">{query}</h2>
                <hr>
                <p><span class="label">பொருள்:</span><br>{meaning}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("இந்த சொல்லிற்கான பொருள் கிடைக்கவில்லை. தயவுசெய்து வேறு சொல்லை முயற்சிக்கவும்.")

st.markdown(
    "<p style='text-align:center;color:#800000;font-weight:bold;margin-top:50px;'>தமிழ் இனிது | ஆய்வகம் 2026</p>",
    unsafe_allow_html=True
)
