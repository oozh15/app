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
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
        
        /* Main background and global text color */
        .stApp {{
            background-image: url("{bg_pattern}");
            background-color: #F7E7CE !important;
            background-attachment: fixed;
            color: #3E2723 !important; /* Dark Wood Brown */
            font-family: 'Pavanam', sans-serif;
        }}

        /* Titles and Subheaders */
        .main-title {{
            font-family: 'Arima Madurai', cursive;
            color: #800000 !important; /* Deep Kumkum Red */
            text-align: center;
            font-size: 4rem;
            margin-bottom: 0px;
        }}
        
        h1, h2, h3, p, span, label {{
            color: #3E2723 !important; /* Ensure no system white text */
        }}

        .title-divider {{
            height: 4px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }}

        /* Widget Fixes (Inputs & Uploaders) */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: #FFF9F0 !important;
            border: 2px dashed #800000 !important;
        }}
        
        /* Forcing text inside boxes to be dark brown, never white */
        input, textarea, [data-testid="stMarkdownContainer"] p {{
            background-color: #FFFDF9 !important;
            color: #3E2723 !important; 
            border: 1px solid #800000 !important;
        }}

        /* Result Card - Replaced white background with light cream */
        .result-card {{
            background-color: #FFF9F0; 
            padding: 25px;
            border: 1px solid #D4AF37;
            border-left: 12px solid #800000;
            box-shadow: 8px 8px 0px rgba(128, 0, 0, 0.1);
            margin-top: 15px;
            color: #3E2723 !important;
        }}

        .meaning-text {{
            color: #800000 !important; /* Meanings stand out in Maroon */
            font-size: 1.5rem;
            font-weight: bold;
        }}

        .label-green {{
            color: #1B5E20 !important; /* Labels in Deep Forest Green */
            font-weight: bold;
        }}

        /* Button Text */
        .stButton>button {{
            background-color: #800000 !important;
            color: #D4AF37 !important; /* Gold text on Maroon button */
            border: 1px solid #D4AF37;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --- 2. BACKEND LOGIC ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def get_word_info(target_word):
    target_word = target_word.strip()
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except: dataset = []

    for entry in dataset:
        if str(entry.get("word", "")).strip() == target_word:
            return {
                "source": "Verified Manuscript",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "None"),
                "antonym": entry.get("antonym", "None"),
                "source_color": "#1B5E20"
            }

    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(to_en)
        return {
            "source": "AI Inference",
            "meaning": meaning_ta,
            "synonym": "N/A",
            "antonym": "N/A",
            "source_color": "#E65100"
        }
    except: return None

def process_ocr(image):
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    config = r'--oem 3 --psm 6 -l tam+eng'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI LAYOUT ---
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📜 Document Extraction")
    uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        with st.spinner("Processing..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    ocr_text = "\n".join([process_ocr(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        
        st.markdown("<p class='label-green'>Extracted Content:</p>", unsafe_allow_html=True)
        st.text_area("", ocr_text, height=300)

with col2:
    st.subheader("🔍 Lexicon Search")
    word_query = st.text_input("Enter word:")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {res['source_color']}; font-size: 0.8rem; font-weight: bold;">{res['source']}</p>
                    <h2 style="border:none; color:#800000; margin-top:0;">{word_query}</h2>
                    <hr style="border: 0.5px solid #D4AF37;">
                    <p><span class="label-green">Meaning:</span><br><span class="meaning-text">{res['meaning']}</span></p>
                    <p><span class="label-green">Synonym:</span> {res['synonym']}</p>
                    <p><span class="label-green">Antonym:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("No data found.")

st.markdown("<br><br><p style='text-align:center; color:#800000;'>தமிழ் இனிது | 2026</p>", unsafe_allow_html=True)
