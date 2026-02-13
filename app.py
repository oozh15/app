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
st.set_page_config(page_title="நிகண்டு | Digital Tamil Lexicon", layout="wide")

def apply_rustic_theme():
    # Parchment texture for a traditional feel
    bg_pattern = "https://www.transparenttextures.com/patterns/papyrus.png"
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
        
        /* Main background - Overriding dark mode defaults */
        .stApp {{
            background-image: url("{bg_pattern}");
            background-color: #F7E7CE !important;
            background-attachment: fixed;
            color: #3E2723 !important;
        }}

        /* Heading Style */
        .main-title {{
            font-family: 'Arima Madurai', cursive;
            color: #800000;
            text-align: center;
            font-size: 4rem;
            margin-bottom: 0px;
        }}

        .title-divider {{
            height: 4px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }}

        /* FIXING THE BLACK BOXES: Forcing Widget Backgrounds */
        /* This targets the file uploader and text input containers */
        [data-testid="stFileUploader"], [data-testid="stTextInput"], [data-testid="stTextArea"] {{
            background-color: rgba(255, 255, 255, 0.4) !important;
            padding: 10px;
            border-radius: 10px;
        }}

        /* Specific fix for the file dropzone area */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: #FFF9F0 !important;
            border: 2px dashed #800000 !important;
            color: #3E2723 !important;
        }}

        /* Specific fix for Input fields */
        input, textarea {{
            background-color: #FFFDF9 !important;
            color: #3E2723 !important;
            border: 1px solid #800000 !important;
        }}

        /* Result Card */
        .result-card {{
            background-color: #FFFFFF;
            padding: 20px;
            border-left: 10px solid #800000;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
            margin-top: 15px;
        }}

        .label {{ color: #1B5E20; font-weight: bold; }}
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
                "source": "Verified Manuscript (தரவுத்தளம்)",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை"),
                "color": "#1B5E20"
            }

    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(to_en)
        return {
            "source": "AI Inference (தானியங்கிப் பொருள்)",
            "meaning": meaning_ta,
            "synonym": "தகவல் இல்லை",
            "antonym": "தகவல் இல்லை",
            "color": "#E65100"
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
    st.subheader("📜 ஆவண ஆய்வு (Extraction)")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        with st.spinner("Processing..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    ocr_text = "\n".join([process_ocr(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        
        st.markdown("<p class='label'>பிரித்தெடுக்கப்பட்ட உரை:</p>", unsafe_allow_html=True)
        st.text_area("", ocr_text, height=300)

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    word_query = st.text_input("தேட வேண்டிய சொல்:")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {res['color']}; font-size: 0.8rem; font-weight: bold;">{res['source']}</p>
                    <h2 style="border:none; color:#800000; margin-top:0;">{word_query}</h2>
                    <hr>
                    <p><span class="label">பொருள்:</span><br><b style="font-size:1.4rem;">{res['meaning']}</b></p>
                    <p><span class="label">இணையான சொல்:</span> {res['synonym']}</p>
                    <p><span class="label">எதிர்ச்சொல்:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("தகவல் கிடைக்கவில்லை.")

st.markdown("<br><br><p style='text-align:center; color:#800000;'>தமிழ் இனிது | ஆய்வகம் 2026</p>", unsafe_allow_html=True)
