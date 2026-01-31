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

st.set_page_config(page_title="Tamil OCR & Multi-Source Dictionary", layout="wide")

# --- 1. Dataset & Wikipedia Logic ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        response = requests.get(JSON_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_wikipedia_summary(word):
    """Searches Wikipedia for a more 'Exact' definition."""
    url = f"https://ta.wikipedia.org/api/rest_v1/page/summary/{word}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('extract')
        return None
    except:
        return None

def find_in_dataset(dataset, word):
    if not dataset: return None
    for entry in dataset:
        if entry.get("word") == word or entry.get("tamil") == word:
            return entry.get("meaning"), entry.get("antonym")
    return None

# --- 2. Advanced OCR Logic ---
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

# --- 3. Multi-Source Backup Logic ---
def get_advanced_meaning(word_tam):
    # Stage 1: Wikipedia Search (For exact/formal meaning)
    wiki_desc = get_wikipedia_summary(word_tam)
    
    # Stage 2: Translation Bridge
    try:
        translator_en = GoogleTranslator(source='ta', target='en')
        meaning_en = translator_en.translate(word_tam)
        
        translator_ta = GoogleTranslator(source='en', target='ta')
        meaning_ta = translator_ta.translate(meaning_en)
        
        # Antonyms via Datamuse API
        ant_url = f"https://api.datamuse.com/words?rel_ant={meaning_en}"
        resp = requests.get(ant_url, timeout=5).json()
        ant_en = [item['word'] for item in resp][:3]
        ant_ta = [translator_ta.translate(a) for a in ant_en]
        
        # Combine Wikipedia and Translation for "Exactness"
        final_meaning = f"{wiki_desc}\n\n(Simplified: {meaning_ta})" if wiki_desc else meaning_ta
        final_antonym = ", ".join(ant_ta) if ant_ta else "❌ Not found"
        
        return final_meaning, final_antonym
    except:
        return "❌ Error fetching meaning", "❌ Error fetching antonym"

# --- UI Setup ---
st.title("🏛️ Pro Tamil OCR & Encyclopedia Lookup")
dataset = load_dataset()

# Sidebar
with st.sidebar:
    st.header("Settings")
    if dataset: st.success(f"Dataset: {len(dataset)} words")
    if st.button("Clear Search History"): st.session_state.history = []

# Persistent History
if 'history' not in st.session_state:
    st.session_state.history = []

uploaded_file = st.file_uploader("Upload Tamil PDF/Image", type=["pdf", "png", "jpg", "jpeg"])

col1, col2 = st.columns([1, 1])

with col1:
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
            st.text_area("OCR Output", extracted_text, height=400)

with col2:
    st.subheader("🔍 Smart Meaning Search")
    word_query = st.text_input("Enter Tamil word:")
    
    if word_query:
        word_query = word_query.strip()
        
        # Logic: Dataset -> Wikipedia -> Translation
        res = find_in_dataset(dataset, word_query)
        if res:
            m, a = res
            source = "Your Dataset"
        else:
            with st.spinner(f"Searching Wikipedia & Web for '{word_query}'..."):
                m, a = get_advanced_meaning(word_query)
                source = "Wikipedia/Web Search"
        
        # Add to history
        st.session_state.history.insert(0, {"word": word_query, "meaning": m, "antonym": a, "source": source})

    # Display History (User can search many times)
    for entry in st.session_state.history:
        with st.expander(f"📖 {entry['word']} (from {entry['source']})", expanded=True):
            st.write(f"**Meaning:** {entry['meaning']}")
            st.write(f"**Antonyms:** {entry['antonym']}")
