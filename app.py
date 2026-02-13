import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import re

# --- CONFIG & CLASSIC TAMIL STYLING ---
st.set_page_config(page_title="நிகண்டு | Digital Tamil Lexicon", layout="wide")

def apply_nigandu_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
        
        .stApp {
            background-color: #F4ECE1; /* Sandalwood/Old Paper tint */
            color: #3E2723;
        }

        /* The Main Header */
        .main-title {
            font-family: 'Arima Madurai', cursive;
            color: #800000;
            text-align: center;
            font-size: 3.5rem;
            margin-bottom: 0px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        /* Decorative Border like a Temple Pillar */
        .title-divider {
            height: 5px;
            background: linear-gradient(90deg, transparent, #D4AF37, #800000, #D4AF37, transparent);
            margin-bottom: 30px;
        }

        /* Result Card styling */
        .result-card {
            background-color: #FFFDF9;
            padding: 25px;
            border-radius: 4px;
            border: 1px solid #D4AF37;
            border-left: 10px solid #800000;
            box-shadow: 8px 8px 0px #D4AF37;
            margin-top: 10px;
        }

        .label {
            font-weight: bold;
            color: #5D4037;
            text-transform: uppercase;
            font-size: 0.8rem;
        }

        /* Sidebar & Inputs */
        .stTextInput input {
            border: 2px solid #800000 !important;
            border-radius: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_nigandu_theme()

# --- BACKEND LOGIC ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def get_word_info(target_word):
    target_word = target_word.strip()
    
    # 1. Dataset Fetch
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        dataset = r.json() if r.status_code == 200 else []
    except:
        dataset = []

    # 2. Search Dataset
    for entry in dataset:
        if str(entry.get("word", "")).strip() == target_word:
            return {
                "source": "Verified Manuscript (தரவுத்தளம்)",
                "meaning": entry.get("meaning"),
                "synonym": entry.get("synonym", "இல்லை"),
                "antonym": entry.get("antonym", "இல்லை"),
                "type": "verified"
            }

    # 3. AI Fallback (Guarantees a Meaning)
    try:
        en_val = GoogleTranslator(source='ta', target='en').translate(target_word)
        ta_val = GoogleTranslator(source='en', target='ta').translate(en_val)
        return {
            "source": "AI Inference (தானியங்கிப் பொருள்)",
            "meaning": ta_val,
            "synonym": "கிடைக்கவில்லை",
            "antonym": "கிடைக்கவில்லை",
            "type": "ai"
        }
    except:
        return None

# --- UI LAYOUT ---
st.markdown('<h1 class="main-title">நிகண்டு</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin-top:-20px;'>The Classic Digital Tamil Lexicon</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📜 ஆவணப் பதிவேற்றம்")
    uploaded_file = st.file_uploader("Upload Document (Image/PDF)", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        st.info("ஆவணம் பெறப்பட்டது. உரையைக் கண்டறிய OCR கருவியைப் பயன்படுத்தவும்.")
        # [Insert OCR Processing code block here as previously provided]

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    query = st.text_input("தேட வேண்டிய சொல்:", placeholder="எ.கா: அறம்")

    if query:
        res = get_word_info(query)
        if res:
            source_style = "color: #2E7D32;" if res['type'] == 'verified' else "color: #E65100;"
            
            st.markdown(f"""
                <div class="result-card">
                    <p style="{source_style} font-size: 0.7rem; font-weight: bold;">{res['source']}</p>
                    <h2 style="border:none; margin-top:0; color:#800000;">{query}</h2>
                    <hr>
                    <p><span class="label">பொருள்:</span><br><b style="font-size:1.3rem;">{res['meaning']}</b></p>
                    <p><span class="label">இணையான சொல்:</span> {res['synonym']}</p>
                    <p><span class="label">எதிர்ச்சொல்:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("மன்னிக்கவும், அந்தச் சொல் நிகண்டில் இல்லை.")

st.markdown("""
    <br><br>
    <div style="text-align: center; border-top: 1px solid #D4AF37; padding-top: 10px;">
        <p style="color: #8B4513; font-size: 0.9rem;">கல் தோன்றி மண் தோன்றாக் காலத்தே முன் தோன்றிய மூத்த தமிழ்</p>
    </div>
""", unsafe_allow_html=True)
