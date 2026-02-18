import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
import wikipedia

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="நிகண்டு | Digital Tamil Lexicon", layout="wide")

# ---------------- THEME ----------------
def apply_rustic_theme():
    bg_pattern = "https://www.transparenttextures.com/patterns/papyrus.png"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
    .stApp {{
        background-image: url("{bg_pattern}");
        background-color: #F7E7CE;
        color: #3E2723;
        font-family: 'Pavanam', sans-serif;
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
        background-color: #FFFFFF;
        padding: 20px;
        border-left: 10px solid #800000;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        border-radius: 5px;
    }}
    .label {{ color: #1B5E20; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# ---------------- DATASET ----------------
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# ---------------- OCR ----------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config = r'--oem 3 --psm 6 -l tam+eng'
    return pytesseract.image_to_string(gray, config=config).strip()

# ---------------- WIKIPEDIA SEARCH ----------------
def get_wikipedia_meaning(word):
    try:
        wikipedia.set_lang("ta")
        results = wikipedia.search(word)
        if results:
            return wikipedia.summary(results[0], sentences=3), "Tamil Wikipedia"
    except:
        pass

    try:
        wikipedia.set_lang("en")
        results = wikipedia.search(word)
        if results:
            return wikipedia.summary(results[0], sentences=3), "English Wikipedia"
    except:
        pass

    return None, None

# ---------------- MAIN LOGIC ----------------
def get_word_info(target_word):
    target_word = target_word.strip()

    # 1️⃣ Dataset Search
    try:
        r = requests.get(JSON_URL, timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except:
        dataset = []

    for entry in dataset:
        if entry.get("word", "").strip() == target_word:
            return {
                "source": "Verified Lexical Dataset",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை"),
                "color": "#1B5E20"
            }

    # 2️⃣ Wikipedia Search
    wiki_text, wiki_source = get_wikipedia_meaning(target_word)
    if wiki_text:
        return {
            "source": f"Wikipedia Online ({wiki_source})",
            "meaning": wiki_text,
            "synonym": "—",
            "antonym": "—",
            "color": "#0D47A1"
        }

    return None

# ---------------- UI ----------------
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📜 ஆவண ஆய்வு")
    uploaded_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                ocr_text = "\n".join(process_ocr(p.to_image(resolution=300).original) for p in pdf.pages)
        else:
            ocr_text = process_ocr(Image.open(uploaded_file))

        st.text_area("பிரித்தெடுக்கப்பட்ட உரை:", ocr_text, height=350)

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    word_query = st.text_input("ஒரு தமிழ் சொல்லை உள்ளிடவும்")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
            <div class="result-card">
                <p style="color:{res['color']}; font-weight:bold;">{res['source']}</p>
                <h2 style="color:#800000">{word_query}</h2>
                <hr>
                <p><span class="label">பொருள்:</span><br>{res['meaning']}</p>
                <p><span class="label">இணையான சொல்:</span> {res['synonym']}</p>
                <p><span class="label">எதிர்ச்சொல்:</span> {res['antonym']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("இந்த சொல்லுக்கான தகவல் கிடைக்கவில்லை.")

st.markdown("<p style='text-align:center; color:#800000; font-weight:bold;'>தமிழ் இனிது | ஆய்வகம் 2026</p>", unsafe_allow_html=True)
