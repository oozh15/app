import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests
import json

# --- Config ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Priority Lexicon", layout="wide")

# --- 1. Dataset First Engine ---
def fetch_data():
    try:
        # Adding a cache-buster to the URL to ensure it doesn't fetch old data
        r = requests.get(f"{JSON_URL}?nocache=1", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_word_info(target_word):
    target_word = target_word.strip()
    dataset = fetch_data()
    
    # STEP 1: STRICT DATASET CHECK (MUST DO FIRST)
    if dataset:
        for entry in dataset:
            # Clean the word from JSON to ensure a perfect match
            db_word = str(entry.get("word", "")).strip()
            
            if db_word == target_word:
                return {
                    "source": "Verified Dataset",
                    "meaning": entry.get("meaning"),
                    "synonym": entry.get("synonym", "இல்லை"),
                    "antonym": entry.get("antonym", "இல்லை")
                }, True

    # STEP 2: FALLBACK TO AI (ONLY IF NOT IN DATASET)
    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(target_word).lower()
        # Precision rule: If AI thinks 'Care' is 'Tender', we force correct it
        if "tender" in to_en and target_word == "அக்கறை": to_en = "care/concern"
        
        to_ta = GoogleTranslator(source='en', target='ta')
        
        return {
            "source": "AI Bridge (Fallback)",
            "meaning": to_ta.translate(to_en),
            "synonym": "இல்லை",
            "antonym": "நேரடி எதிர்ச்சொல் இல்லை"
        }, False
    except:
        return None, False

# --- 2. OCR Logic ---
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    
    
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI Implementation ---
st.title("📘 Tamil Precision Dictionary")

uploaded_file = st.file_uploader("Upload Image/PDF", type=["pdf", "png", "jpg", "jpeg"])
ocr_text = ""

if uploaded_file:
    with st.spinner("Processing OCR..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    ocr_text += process_ocr(page.to_image(resolution=500).original) + "\n"
        else:
            ocr_text = process_ocr(Image.open(uploaded_file))
    st.text_area("Extracted Text Content:", ocr_text, height=250)

st.divider()

word_query = st.text_input("Enter Word to Search (e.g., அக்கறை):")

if word_query:
    res, is_dataset = get_word_info(word_query)
    
    if res:
        if is_dataset:
            st.success(f"📌 Found in: {res['source']}")
        else:
            st.warning(f"🤖 Found in: {res['source']}")
            
        st.markdown(f"### **பொருள்:** {res['meaning']}")
        st.write(f"**இணையான சொற்கள்:** {res['synonym']}")
        st.write(f"**எதிர்ச்சொல்:** {res['antonym']}")
    else:
        st.error("தகவல் கிடைக்கவில்லை.")
