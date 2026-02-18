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
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

# ---------------- SIMPLE ROOT NORMALIZATION ----------------
def normalize_word(word):
    suffixes = ["இல்", "இன்", "ஆல்", "உடன்", "க்கு", "கள்", "து", "தை", "ன்", "யை", "இய", "ஆ"]
    for suf in suffixes:
        if word.endswith(suf) and len(word) > len(suf) + 1:
            return word[:-len(suf)]
    return word

# ---------------- DATASET (OPTIONAL) ----------------
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def search_dataset(word):
    try:
        data = requests.get(JSON_URL, timeout=5).json()
        for entry in data:
            if entry.get("word", "").strip() == word:
                return entry.get("meaning"), "Lexical Dataset"
    except:
        pass
    return None, None

# ---------------- WIKIPEDIA (VERSION-SAFE INIT) ----------------
wiki_ta = wikipediaapi.Wikipedia(
    "TamilLexiconApp/1.0",   # user_agent (POSITIONAL)
    "ta",                    # language
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

wiki_en = wikipediaapi.Wikipedia(
    "TamilLexiconApp/1.0",   # user_agent (POSITIONAL)
    "en",                    # language
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

def search_wikipedia(word):
    page = wiki_ta.page(word)
    if page.exists():
        return page.summary[:800], "Tamil Wikipedia"

    page = wiki_en.page(word)
    if page.exists():
        return page.summary[:800], "English Wikipedia"

    return None, None

# ---------------- MAIN SEARCH ----------------
def get_meaning(word):
    word = word.strip()
    root = normalize_word(word)

    # 1) Dataset
    meaning, source = search_dataset(word)
    if meaning:
        return meaning, source

    if root != word:
        meaning, source = search_dataset(root)
        if meaning:
            return meaning, f"{source} (Root: {root})"

    # 2) Wikipedia
    meaning, source = search_wikipedia(word)
    if meaning:
        return meaning, source

    if root != word:
        meaning, source = search_wikipedia(root)
        if meaning:
            return meaning, f"{source} (Root: {root})"

    return None, None

# ---------------- UI ----------------
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
                <p style="font-size:0.85rem;color:#555;">Source: {source}</p>
                <h2 style="color:#800000">{query}</h2>
                <hr>
                <p><span class="label">பொருள்:</span><br>{meaning}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(
                "இந்த சொல் நேரடியாக இல்லை. "
                "இது ஒரு மாற்று / விகுதி சேர்க்கப்பட்ட வடிவமாக இருக்கலாம்."
            )

st.markdown(
    "<p style='text-align:center;color:#800000;font-weight:bold;'>தமிழ் இனிது | ஆய்வகம் 2026</p>",
    unsafe_allow_html=True
)
