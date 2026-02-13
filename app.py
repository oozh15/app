import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import re

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Nigandu | Digital Lexicon", layout="wide")

def apply_rustic_theme():
    bg_pattern = "https://www.transparenttextures.com/patterns/papyrus.png"
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,700;1,400&display=swap');
        
        .stApp {{
            background-image: url("{bg_pattern}");
            background-color: #F7E7CE !important;
            background-attachment: fixed;
            color: #3E2723 !important;
            font-family: 'Crimson Text', serif;
        }}

        .main-title {{
            font-family: 'Crimson Text', serif;
            color: #800000;
            text-align: center;
            font-size: 4.5rem;
            margin-bottom: 0px;
            font-weight: bold;
        }}

        .title-divider {{
            height: 4px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }}

        /* Fix for Black Upload Boxes */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: #FFF9F0 !important;
            border: 2px dashed #800000 !important;
            color: #800000 !important;
        }}
        
        input, textarea {{
            background-color: #FFFDF9 !important;
            color: #3E2723 !important;
            border: 1px solid #800000 !important;
        }}

        .result-card {{
            background-color: #FFFFFF;
            padding: 20px;
            border-left: 10px solid #800000;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
            margin-top: 15px;
            border-radius: 5px;
        }}

        .label {{ color: #1B5E20; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --- 2. BACKEND LOGIC (Modified for English) ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def get_word_info(target_word):
    target_word = target_word.strip().lower()
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except: dataset = []

    # 1. Search Dataset
    for entry in dataset:
        if str(entry.get("word", "")).strip().lower() == target_word:
            return {
                "source": "Verified Manuscript (Database)",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "None"),
                "antonym": entry.get("antonym", "None"),
                "color": "#1B5E20"
            }

    # 2. AI Fallback (Translating to English)
    try:
        # If input is English, translate to Tamil for the meaning, or vice-versa
        translated_meaning = GoogleTranslator(source='auto', target='en').translate(target_word)
        return {
            "source": "AI Inference (Automated)",
            "meaning": translated_meaning,
            "synonym": "Not available",
            "antonym": "Not available",
            "color": "#E65100"
        }
    except: return None

def process_ocr(image):
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # Configured for English + Tamil OCR
    config = r'--oem 3 --psm 6 -l eng+tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI LAYOUT (English UI) ---
st.markdown('<h1 class="main-title">Nigandu</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📜 Document Extraction")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        with st.spinner("Reading document..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    ocr_text = "\n".join([process_ocr(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        
        st.markdown("<p class='label'>Extracted Text:</p>", unsafe_allow_html=True)
        st.text_area("", ocr_text, height=350)

with col2:
    st.subheader("🔍 Lexicon Search")
    word_query = st.text_input("Enter a word to search:")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {res['color']}; font-size: 0.8rem; font-weight: bold;">{res['source']}</p>
                    <h2 style="border:none; color:#800000; margin-top:0;">{word_query.capitalize()}</h2>
                    <hr>
                    <p><span class="label">Meaning:</span><br><b style="font-size:1.5rem;">{res['meaning']}</b></p>
                    <p><span class="label">Synonyms:</span> {res['synonym']}</p>
                    <p><span class="label">Antonyms:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Word not found in the Lexicon.")

st.markdown("<br><br><p style='text-align:center; color:#800000; font-weight:bold;'>Digital Lexicon | Research Lab 2026</p>", unsafe_allow_html=True)
