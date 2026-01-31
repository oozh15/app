import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests

# --- Configuration ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil Precision Lexicon", layout="wide")

# --- 1. Dataset-First Logic (The Fix) ---
@st.cache_data(ttl=60)
def load_verified_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def get_accurate_word_data(word_tam):
    # Normalize input: remove spaces and hidden characters
    search_term = word_tam.strip()
    
    # 1. MUST CHECK DATASET FIRST
    dataset = load_verified_dataset()
    if dataset:
        for entry in dataset:
            # Normalize database word for comparison
            db_word = str(entry.get("word", "")).strip()
            
            if db_word == search_term:
                return {
                    "source": "உங்களது தரவுத்தளம் (Verified Dataset)",
                    "meaning": entry.get("meaning"),
                    "synonym": entry.get("synonym", "இல்லை"),
                    "antonym": entry.get("antonym", "இல்லை")
                }

    # 2. IF NOT FOUND IN DATASET, USE AI BRIDGE
    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(search_term).lower()
        to_ta = GoogleTranslator(source='en', target='ta')
        
        # Sense-check for common words like 'Care'
        if "care" in to_en or "concern" in to_en:
            meaning = "கவனிப்பு / ஆர்வம்"
            ant = "அலட்சியம்"
            syn = "கவனம்"
        else:
            meaning = to_ta.translate(to_en)
            ant = "நேரடி எதிர்ச்சொல் இல்லை"
            syn = "இல்லை"

        return {
            "source": "செயற்கை நுண்ணறிவு (AI)",
            "meaning": meaning,
            "synonym": syn,
            "antonym": ant
        }
    except:
        return None

# --- 2. Professional OCR Engine ---


def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI Implementation ---
st.title("📘 Tamil Precision Word Tool")

uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])

extracted_text = ""
if uploaded_file:
    with st.spinner("Reading Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extracted_text += process_ocr(page.to_image(resolution=500).original) + "\n\n"
        else:
            extracted_text = process_ocr(Image.open(uploaded_file))
    
    st.subheader("📄 Extracted Text")
    st.text_area("OCR Output", extracted_text, height=250)

st.divider()

# Search Logic
st.subheader("🔍 Search Word")
search_word = st.text_input("Enter Tamil word (e.g., அக்கறை):")

if search_word:
    result = get_accurate_word_data(search_word)
    if result:
        # Visual feedback on source
        if "Dataset" in result['source']:
            st.success(f"✅ {result['source']}")
        else:
            st.warning(f"🤖 {result['source']}")
            
        st.markdown(f"### **விளக்கம்:** {result['meaning']}")
        st.write(f"**இணையான சொற்கள்:** {result['synonym']}")
        st.write(f"**எதிர்ச்சொல்:** {result['antonym']}")
    else:
        st.error("தகவல் கிடைக்கவில்லை.")
