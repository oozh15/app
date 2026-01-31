import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests
import json

# --- Configuration ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil OCR & Smart Word Tool", layout="wide")

# --- 1. Core Logic Functions ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        response = requests.get(JSON_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def find_in_dataset(dataset, word):
    """Searches your specific GitHub JSON for the word."""
    if not dataset: return None
    for entry in dataset:
        if entry.get("word") == word or entry.get("tamil") == word:
            return entry.get("meaning"), entry.get("antonym")
    return None

def get_web_meaning(word):
    """Fallback 1: Fetches from a formal encyclopedia source."""
    url = f"https://ta.wikipedia.org/api/rest_v1/page/summary/{word}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('extract')
        return None
    except:
        return None

def translate_fallback(word_tam):
    """Fallback 2: Deep translation bridge for antonyms and simplified meaning."""
    try:
        translator_en = GoogleTranslator(source='ta', target='en')
        meaning_en = translator_en.translate(word_tam)
        
        translator_ta = GoogleTranslator(source='en', target='ta')
        meaning_ta = translator_ta.translate(meaning_en)
        
        # Antonyms via English bridge
        ant_url = f"https://api.datamuse.com/words?rel_ant={meaning_en}"
        resp = requests.get(ant_url, timeout=5).json()
        ant_en = [item['word'] for item in resp][:3]
        ant_ta = [translator_ta.translate(a) for a in ant_en]
        
        return meaning_ta, ", ".join(ant_ta) if ant_ta else "❌ Not found"
    except:
        return "❌ Error", "❌ Error"

# --- 2. OCR Engine ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    custom_config = r'--oem 3 --psm 4 -l tam'
    text = pytesseract.image_to_string(processed, config=custom_config)
    return re.sub(r'[|I\[\]\\]', '', text).strip()

# --- 3. UI and Session Logic ---
st.title("📘 Advanced Tamil OCR & Word Intelligence")

dataset = load_dataset()

# Initialize search history
if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        with st.spinner("Extracting text..."):
            extracted_text = ""
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        img = page.to_image(resolution=500).original
                        extracted_text += extract_tamil_text(img) + "\n\n"
            else:
                img = Image.open(uploaded_file)
                extracted_text = extract_tamil_text(img)
            
            st.subheader("📄 Extracted Document")
            st.text_area("OCR Output", extracted_text, height=450)

with col2:
    st.subheader("🔍 Smart Meaning Search")
    word_query = st.text_input("Enter Tamil word to search:", placeholder="e.g. வேளாண்மை")
    
    if word_query:
        word_query = word_query.strip()
        
        # --- WATERFALL SEARCH LOGIC ---
        # 1. Check Dataset
        res = find_in_dataset(dataset, word_query)
        if res:
            m, a = res
            source = "Primary Dataset"
        else:
            # 2. Check Web/Encyclopedia
            with st.spinner("Searching advanced sources..."):
                web_m = get_web_meaning(word_query)
                # 3. Translation Backup (for antonyms)
                backup_m, a = translate_fallback(word_query)
                m = web_m if web_m else backup_m
                source = "Encyclopedia Search" if web_m else "Translation Service"
        
        # Add to session history
        st.session_state.history.insert(0, {"word": word_query, "meaning": m, "antonym": a, "source": source})

    # History Display (Scrollable)
    st.markdown("### 🕒 Search History")
    for entry in st.session_state.history:
        with st.expander(f"📖 {entry['word']} - {entry['source']}", expanded=True):
            st.info(f"**பொருள்:** {entry['meaning']}")
            st.warning(f"**எதிர்ச்சொல்:** {entry['antonym']}")

if st.sidebar.button("Clear History"):
    st.session_state.history = []
    st.rerun()
