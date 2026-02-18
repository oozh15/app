import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests

# --------------------------------------------------
# 1. PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="நிகண்டு | Digital Tamil Lexicon",
    layout="wide"
)

# --------------------------------------------------
# 2. THEME
# --------------------------------------------------
def apply_rustic_theme():
    bg_pattern = "https://www.transparenttextures.com/patterns/papyrus.png"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');

    .stApp {{
        background-image: url("{bg_pattern}");
        background-color: #F7E7CE;
        font-family: 'Pavanam', sans-serif;
        color: #3E2723;
    }}

    .main-title {{
        font-family: 'Arima Madurai', cursive;
        color: #800000;
        text-align: center;
        font-size: 4rem;
    }}

    .title-divider {{
        height: 4px;
        background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
        margin-bottom: 30px;
    }}

    .result-card {{
        background: white;
        padding: 20px;
        border-left: 10px solid #800000;
        border-radius: 5px;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
        margin-top: 15px;
    }}

    .label {{
        color: #1B5E20;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --------------------------------------------------
# 3. LOAD TAMIL LEXICAL DATASET (CACHED)
# --------------------------------------------------
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

@st.cache_data(show_spinner=False)
def load_lexical_data():
    try:
        r = requests.get(JSON_URL, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

LEXICAL_DATA = load_lexical_data()

# --------------------------------------------------
# 4. EXACT MEANING FETCH (NO AI)
# --------------------------------------------------
def get_word_info(word):
    word = word.strip()

    for entry in LEXICAL_DATA:
        if entry.get("word", "").strip() == word:
            return {
                "source": "Tamil Lexical Dataset (WordNet)",
                "meaning": entry.get("meaning", "தகவல் இல்லை"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை")
            }

    return None

# --------------------------------------------------
# 5. OCR PROCESS
# --------------------------------------------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    config = r'--oem 3 --psm 6 -l tam'
    return pytesseract.image_to_string(thresh, config=config)

# --------------------------------------------------
# 6. UI
# --------------------------------------------------
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# -------- LEFT: EXTRACTION --------
with col1:
    st.subheader("📜 ஆவண ஆய்வு (Text Extraction)")
    uploaded_file = st.file_uploader("PDF / Image தேர்வு செய்க", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file:
        with st.spinner("உரை பெறப்படுகிறது..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    extracted_text = "\n".join(
                        process_ocr(p.to_image(resolution=300).original)
                        for p in pdf.pages
                    )
            else:
                extracted_text = process_ocr(Image.open(uploaded_file))

        st.text_area("பிரித்தெடுக்கப்பட்ட உரை", extracted_text, height=350)

# -------- RIGHT: SEARCH --------
with col2:
    st.subheader("🔍 சொற்பொருள் தேடல் (Exact Meaning)")
    word_query = st.text_input("ஒரு தமிழ் சொல்லை உள்ளிடவும்")

    if word_query:
        result = get_word_info(word_query)

        if result:
            st.markdown(f"""
            <div class="result-card">
                <p style="color:#1B5E20; font-weight:bold;">
                    {result['source']}
                </p>
                <h2 style="color:#800000;">{word_query}</h2>
                <hr>
                <p><span class="label">பொருள்:</span><br>
                <span style="font-size:1.5rem;">{result['meaning']}</span></p>
                <p><span class="label">இணையான சொல்:</span> {result['synonym']}</p>
                <p><span class="label">எதிர்ச்சொல்:</span> {result['antonym']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("இந்த சொல் தரவுத்தளத்தில் இல்லை")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown(
    "<br><p style='text-align:center; color:#800000; font-weight:bold;'>தமிழ் இனிது | ஆய்வகம் 2026</p>",
    unsafe_allow_html=True
)
