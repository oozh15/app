import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import re

# --- CONFIG & RUSTIC STYLING ---
st.set_page_config(page_title="செந்தமிழ் அகராதி", layout="wide")

def apply_custom_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pavanam&display=swap');
        .stApp { background-color: #FDF5E6; color: #4A2C2A; font-family: 'Pavanam', sans-serif; }
        h1, h2, h3 { color: #800000 !important; border-bottom: 2px solid #D4AF37; }
        .result-card {
            background-color: #FFFFFF; padding: 20px; border-radius: 10px;
            border-left: 8px solid #800000; box-shadow: 3px 3px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .data-label { font-weight: bold; color: #800000; }
        .stButton>button { background-color: #800000; color: #D4AF37; border: 1px solid #D4AF37; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_theme()

# --- BACKEND FUNCTIONS ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

def fetch_data():
    try:
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        return r.json() if r.status_code == 200 else []
    except: return []

def get_word_info(target_word):
    target_word = target_word.strip()
    dataset = fetch_data()
    
    # 1. Search in Verified Dataset
    if dataset:
        for entry in dataset:
            if str(entry.get("word", "")).strip() == target_word:
                return {
                    "source": "Verified Dataset (அங்கீகரிக்கப்பட்டது)",
                    "meaning": entry.get("meaning"),
                    "synonym": entry.get("synonym", "இல்லை"),
                    "antonym": entry.get("antonym", "இல்லை"),
                    "status": "success"
                }

    # 2. Fallback to AI Translation (Meaning Guaranteed)
    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(to_en)
        return {
            "source": "AI Bridge (தானியங்கி முறை)",
            "meaning": meaning_ta,
            "synonym": "தகவல் இல்லை",
            "antonym": "தகவல் இல்லை",
            "status": "warning"
        }
    except:
        return None

def process_ocr_advanced(image):
    # Convert to OpenCV format
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Pre-processing for "Real" Documents (Denoising + Adaptive Threshold)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    config = r'--oem 3 --psm 6 -l tam+eng'
    return pytesseract.image_to_string(thresh, config=config).strip()

def auto_extract_details(text):
    # Search for common certificate patterns
    cert_no = re.search(r'TN-\d+', text)
    date = re.search(r'\d{2}-\d{2}-\d{4}', text)
    return {
        "Cert No": cert_no.group(0) if cert_no else "Not detected",
        "Date": date.group(0) if date else "Not detected"
    }

# --- UI LAYOUT ---
st.markdown("<h1 style='text-align: center;'>📜 முன்னுரிமை அகராதி (Lexicon)</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📄 ஆவண ஆய்வு (Document Analysis)")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        with st.spinner("Processing..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    raw_text = "\n".join([process_ocr_advanced(p.to_image(resolution=300).original) for p in pdf.pages])
            else:
                raw_text = process_ocr_advanced(Image.open(uploaded_file))
            
            # Show Extracted Details
            details = auto_extract_details(raw_text)
            st.info(f"📍 கண்டறியப்பட்ட எண்: {details['Cert No']} | நாள்: {details['Date']}")
            st.text_area("கண்டறியப்பட்ட உரை:", raw_text, height=200)

with col2:
    st.subheader("🔍 சொல் தேடல் (Dictionary)")
    word_query = st.text_input("சொல்லைத் தட்டச்சு செய்யவும்:", placeholder="எ.கா: சான்றிதழ்")

    if word_query:
        res = get_word_info(word_query)
        if res:
            # Displaying the Result Card
            st.markdown(f"""
                <div class="result-card">
                    <small style="color:gray;">மூலம்: {res['source']}</small>
                    <h2 style="border:none; color:#800000; margin-top:5px;">{word_query}</h2>
                    <p style="font-size:1.2rem;"><span class="data-label">பொருள் (Meaning):</span> {res['meaning']}</p>
                    <p><span class="data-label">இணையான சொல்:</span> {res['synonym']}</p>
                    <p><span class="data-label">எதிர்ச்சொல்:</span> {res['antonym']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if res['status'] == "warning":
                st.caption("⚠️ குறிப்பு: இந்தத் தகவல் AI மூலம் மொழிபெயர்க்கப்பட்டது.")
        else:
            st.error("தகவல் கிடைக்கவில்லை.")

st.divider()
st.markdown("<p style='text-align:center; color:brown;'>தமிழ் இனிது | ஆய்வகம் 2024</p>", unsafe_allow_html=True)
