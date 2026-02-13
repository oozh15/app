import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests

# --- CONFIG & STYLING ---
st.set_page_config(page_title="செந்தமிழ் அகராதி | Priority Lexicon", layout="wide")

def apply_rustic_theme():
    st.markdown("""
        <style>
        /* Main background and font */
        @import url('https://fonts.googleapis.com/css2?family=Latha&family=Pavanam&display=swap');
        
        .stApp {
            background-color: #FDF5E6; /* Old Parchment / Off-white */
            color: #4A2C2A;
        }

        /* Sidebar and Headers */
        h1, h2, h3 {
            color: #800000 !important; /* Deep Maroon / Kumkum */
            font-family: 'Pavanam', sans-serif;
            border-bottom: 2px solid #D4AF37; /* Gold separator */
            padding-bottom: 10px;
        }

        /* Input boxes */
        .stTextInput input, .stTextArea textarea {
            background-color: #FFF9F0 !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 5px;
            color: #4A2C2A !important;
        }

        /* Buttons */
        .stButton>button {
            background-color: #800000;
            color: #D4AF37;
            border: 2px solid #D4AF37;
            border-radius: 8px;
            font-weight: bold;
            transition: 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #D4AF37;
            color: #800000;
        }

        /* Decorative Card for results */
        .result-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            border-left: 10px solid #800000;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
            margin-top: 20px;
        }

        /* Footer Decoration */
        .footer {
            text-align: center;
            font-size: 0.8rem;
            color: #8B4513;
            margin-top: 50px;
            border-top: 1px solid #D4AF37;
            padding-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

apply_rustic_theme()

# --- LOGIC ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def fetch_data():
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_word_info(target_word):
    target_word = target_word.strip()
    dataset = fetch_data()
    if dataset:
        for entry in dataset:
            db_word = str(entry.get("word", "")).strip()
            if db_word == target_word:
                return {
                    "source": "Verified Dataset (அங்கீகரிக்கப்பட்டது)",
                    "meaning": entry.get("meaning"),
                    "synonym": entry.get("synonym", "இல்லை"),
                    "antonym": entry.get("antonym", "இல்லை")
                }, True

    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word).lower()
        if "tender" in to_en and target_word == "அக்கறை": to_en = "care/concern"
        to_ta = GoogleTranslator(source='en', target='ta')
        
        return {
            "source": "AI Bridge (தானியங்கி முறை)",
            "meaning": to_ta.translate(to_en),
            "synonym": "இல்லை",
            "antonym": "நேரடி எதிர்ச்சொல் இல்லை"
        }, False
    except:
        return None, False

def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- UI LAYOUT ---
st.markdown("<h1 style='text-align: center;'>📜 முன்னுரிமை அகராதி</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>Priority Lexicon - Classic Tamil Research Tool</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📖 ஆவணப் பதிவேற்றம் (Upload)")
    uploaded_file = st.file_uploader("படங்கள் அல்லது PDF கோப்புகளைத் தேர்ந்தெடுக்கவும்", type=["pdf", "png", "jpg", "jpeg"])
    
    ocr_text = ""
    if uploaded_file:
        with st.spinner("உரையைக் கண்டறியும் பணி நடக்கிறது..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        ocr_text += process_ocr(page.to_image(resolution=500).original) + "\n"
            else:
                ocr_text = process_ocr(Image.open(uploaded_file))
        st.text_area("கண்டறியப்பட்ட உரை (Extracted Text):", ocr_text, height=300)

with col2:
    st.subheader("🔍 சொல் தேடல் (Word Search)")
    word_query = st.text_input("தேட வேண்டிய சொல்லைத் தட்டச்சு செய்யவும்:", placeholder="எ.கா: அக்கறை")

    if word_query:
        res, is_dataset = get_word_info(word_query)
        if res:
            source_color = "#2E7D32" if is_dataset else "#BF360C"
            
            st.markdown(f"""
                <div class="result-card">
                    <p style="color: {source_color}; font-weight: bold; font-size: 0.9rem;">📍 மூலம்: {res['source']}</p>
                    <h2 style="border:none; margin-top:0;">{word_query}</h2>
                    <p style="font-size: 1.2rem;"><b>பொருள்:</b> {res['meaning']}</p>
                    <hr style="border: 0.5px solid #EEE;">
                    <p><b>இணையான சொற்கள்:</b> {res['synonym']}</p>
                    <p><b>எதிர்ச்சொல்:</b> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("மன்னிக்கவும், தகவல் கிடைக்கவில்லை.")

st.markdown("""
    <div class="footer">
        தமிழ் இனிது | செந்தமிழ் ஆய்வகம் © 2024
    </div>
""", unsafe_allow_html=True)
