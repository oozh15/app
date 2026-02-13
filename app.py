import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import re

# --- 1. பக்க வடிவமைப்பு மற்றும் பழங்கால பின்னணி அமைப்பு ---
st.set_page_config(page_title="நிகண்டு | Digital Tamil Lexicon", layout="wide")

def apply_rustic_theme():
    # பின்னணி படத்திற்கான URL (Old Paper/Parchment Texture)
    bg_image = "https://www.transparenttextures.com/patterns/papyrus.png" # அல்லது வேறு ஏதேனும் Texture URL
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
        
        /* முழு பக்கத்திற்கான பின்னணி மற்றும் நிறம் */
        .stApp {{
            background-image: url("{bg_image}");
            background-color: #F7E7CE; /* பின்னணி படம் வேலை செய்யவில்லை என்றால் இந்த நிறம் தெரியும் */
            background-attachment: fixed;
            color: #3E2723;
            font-family: 'Pavanam', sans-serif;
        }}

        /* தலைப்பு - குங்குமச் சிவப்பு */
        .main-title {{
            font-family: 'Arima Madurai', cursive;
            color: #800000;
            text-align: center;
            font-size: 4.5rem;
            margin-bottom: 0px;
            text-shadow: 1px 1px 2px #D4AF37;
        }}

        /* கோடு அலங்காரம் */
        .title-divider {{
            height: 5px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }}

        /* உள்ளீடு பெட்டிகள் மற்றும் உரை பகுதிகள் */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: rgba(255, 250, 240, 0.8) !important; /* லேசான ஒளி ஊடுருவும் பின்னணி */
            border: 2px solid #800000 !important;
            color: #3E2723 !important;
            border-radius: 5px !important;
            font-weight: bold;
        }}

        /* முடிவுகள் காட்டும் அட்டை (Result Card) */
        .result-card {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border: 2px solid #D4AF37;
            border-left: 12px solid #800000;
            box-shadow: 10px 10px 20px rgba(0,0,0,0.1);
            margin-top: 15px;
            border-radius: 8px;
        }}

        .data-label {{
            color: #1B5E20; /* கரும்பச்சை */
            font-weight: bold;
            font-size: 1rem;
            margin-bottom: 5px;
        }}

        /* கோப்பு பதிவேற்றும் பகுதி (Uploader) */
        .stFileUploader section {{
            background-color: rgba(255, 255, 255, 0.5) !important;
            border: 1px dashed #800000 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --- 2. தரவுச் செயலாக்கம் ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def get_word_info(target_word):
    target_word = target_word.strip()
    try:
        r = requests.get(f"{{JSON_URL}}?nocache=1", timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except: dataset = []

    for entry in dataset:
        if str(entry.get("word", "")).strip() == target_word:
            return {{
                "source": "Verified Manuscript (தரவுத்தளம்)",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை"),
                "color": "#1B5E20"
            }}

    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(to_en)
        return {{
            "source": "AI Inference (தானியங்கிப் பொருள்)",
            "meaning": meaning_ta,
            "synonym": "தகவல் இல்லை",
            "antonym": "தகவல் இல்லை",
            "color": "#E65100"
        }}
    except: return None

def process_ocr(image):
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    config = r'--oem 3 --psm 6 -l tam+eng'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. பயனர் இடைமுகம் ---
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📜 ஆவண ஆய்வு (Extraction)")
    uploaded_file = st.file_uploader("கோப்பை இங்கே பதிவேற்றவும்", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        with st.spinner("உரையைக் கண்டறிகிறது..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    ocr_text = "\\n".join([process_ocr(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        
        st.markdown("<p class='data-label'>பிரித்தெடுக்கப்பட்ட உரை:</p>", unsafe_allow_html=True)
        st.text_area("", ocr_text, height=350)

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    word_query = st.text_input("தேட வேண்டிய சொல்லைத் தட்டச்சு செய்க:")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {{res['color']}}; font-size: 0.8rem; font-weight: bold;">{{res['source']}}</p>
                    <h2 style="border:none; color:#800000; margin-top:0;">{{word_query}}</h2>
                    <hr style="border: 0.5px solid #D4AF37;">
                    <p><span class="data-label">பொருள்:</span><br><b style="font-size:1.5rem;">{{res['meaning']}}</b></p>
                    <p><span class="data-label">இணையான சொல்:</span> {{res['synonym']}}</p>
                    <p><span class="data-label">எதிர்ச்சொல்:</span> {{res['antonym']}}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("மன்னிக்கவும், நிகண்டில் இச்சொல் காணப்படவில்லை.")

st.markdown("<br><br><p style='text-align:center; color:#800000; font-weight:bold;'>தமிழ் இனிது | ஆய்வகம் 2026</p>", unsafe_allow_html=True)
