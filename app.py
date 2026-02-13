import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import re

# --- 1. பக்க வடிவமைப்பு மற்றும் ஸ்டைலிங் ---
st.set_page_config(page_title="நிகண்டு | Digital Tamil Lexicon", layout="wide")

def apply_rustic_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
        
        /* பின்னணி நிறம் - பழைய காகித நிறம் */
        .stApp {
            background-color: #F7E7CE; 
            color: #3E2723;
            font-family: 'Pavanam', sans-serif;
        }

        /* தலைப்பு - குங்குமச் சிவப்பு */
        .main-title {
            font-family: 'Arima Madurai', cursive;
            color: #800000;
            text-align: center;
            font-size: 4rem;
            margin-bottom: 0px;
        }

        /* கோடு அலங்காரம் */
        .title-divider {
            height: 4px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }

        /* உள்ளீடு பெட்டிகள் (Search Box) - சந்தன நிறம் */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #FFF9F0 !important;
            border: 2px solid #800000 !important;
            color: #3E2723 !important;
            border-radius: 0px !important;
        }

        /* முடிவு அட்டை (Result Card) */
        .result-card {
            background-color: #FFFFFF;
            padding: 20px;
            border: 1px solid #D4AF37;
            border-left: 10px solid #800000;
            box-shadow: 5px 5px 0px #800000;
            margin-top: 15px;
        }

        /* டேட்டா லேபிள்கள் - பச்சை நிறம் */
        .data-label {
            color: #1B5E20;
            font-weight: bold;
            font-size: 0.9rem;
        }

        /* பட்டன் ஸ்டைல் */
        .stButton>button {
            background-color: #800000;
            color: #D4AF37;
            border: 1px solid #D4AF37;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --- 2. தரவு மற்றும் செயலாக்க செயல்பாடுகள் ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def get_word_info(target_word):
    target_word = target_word.strip()
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except: dataset = []

    # 1. முதலில் டேட்டாசெட்டில் தேடவும்
    for entry in dataset:
        if str(entry.get("word", "")).strip() == target_word:
            return {
                "source": "Verified Manuscript (தரவுத்தளம்)",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை"),
                "color": "#1B5E20"
            }

    # 2. இல்லை எனில் AI மூலம் பொருள் கண்டறியவும்
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
    # தெளிவான எழுத்துக்களுக்கு Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    config = r'--oem 3 --psm 6 -l tam+eng'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. பயனர் இடைமுகம் (UI) ---
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📜 ஆவண ஆய்வு (Extraction)")
    uploaded_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=["pdf", "png", "jpg", "jpeg"])
    
    ocr_text = ""
    if uploaded_file:
        with st.spinner("உரையைக் கண்டறிகிறது..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    ocr_text = "\n".join([process_ocr(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        
        # பிரித்தெடுக்கப்பட்ட உரையை பயனர் பார்ப்பதற்கு
        st.markdown("<p class='data-label'>கண்டறியப்பட்ட உரை (Extracted Text):</p>", unsafe_allow_html=True)
        st.text_area("", ocr_text, height=300, key="ocr_output")

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    word_query = st.text_input("தேட வேண்டிய சொல் (எ.கா: சான்றிதழ்):")

    if word_query:
        res = get_word_info(word_query)
        if res:
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {res['color']}; font-size: 0.8rem; font-weight: bold;">{res['source']}</p>
                    <h2 style="border:none; color:#800000; margin-top:0;">{word_query}</h2>
                    <hr style="border: 0.5px solid #D4AF37;">
                    <p><span class="data-label">பொருள்:</span><br><b style="font-size:1.4rem;">{res['meaning']}</b></p>
                    <p><span class="data-label">இணையான சொல்:</span> {res['synonym']}</p>
                    <p><span class="data-label">எதிர்ச்சொல்:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("மன்னிக்கவும், தகவல் கிடைக்கவில்லை.")

st.markdown("<br><br><p style='text-align:center; color:#800000; opacity:0.7;'>© 2026 நிகண்டு டிஜிட்டல் அகராதி</p>", unsafe_allow_html=True)
