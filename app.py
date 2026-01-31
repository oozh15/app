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

st.set_page_config(page_title="Tamil Precision OCR", layout="wide")

# --- 1. Accuracy & Dataset Logic ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        response = requests.get(JSON_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def find_in_dataset(dataset, word):
    if not dataset or not isinstance(dataset, list): return None
    for entry in dataset:
        if entry.get("word") == word or entry.get("tamil") == word:
            return entry.get("meaning"), entry.get("antonym")
    return None

def get_precision_data(word_tam):
    """
    Accuracy Engine: 
    1. Cross-references via English Root.
    2. Fetches formal Lexicon synonyms/antonyms.
    3. Formats into exactly two formal Tamil sentences.
    """
    try:
        # Translate to English to find the precise semantic root
        translator_en = GoogleTranslator(source='ta', target='en')
        root_en = translator_en.translate(word_tam).lower()
        
        # Query Lexical Database (Datamuse/Oxford context)
        syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=3").json()
        ant_resp = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=3").json()
        
        syn_en = [item['word'] for item in syn_resp]
        ant_en = [item['word'] for item in ant_resp]
        
        # Translate back with context
        translator_ta = GoogleTranslator(source='en', target='ta')
        meaning_ta = translator_ta.translate(root_en)
        syn_ta = [translator_ta.translate(s) for s in syn_en]
        ant_ta = [translator_ta.translate(a) for a in ant_en]
        
        # --- TWO SENTENCE FORMATION ---
        sentence_1 = f"'{word_tam}' என்பதன் துல்லியமான பொருள் '{meaning_ta}' ஆகும்; இதன் இணைச் சொற்கள் {', '.join(syn_ta) if syn_ta else 'இல்லை'}."
        sentence_2 = f"இந்தச் சொல்லிற்கு நேர் எதிரான எதிர்ச்சொல் '{', '.join(ant_ta) if ant_ta else 'கிடைக்கவில்லை'}' என்பதாகும்."
        
        return f"{sentence_1} {sentence_2}"
    except:
        return "மன்னிக்கவும், தொழில்நுட்பக் கோளாறு காரணமாகத் தகவலைப் பெற முடியவில்லை."

# --- 2. OCR Engine (DPI 500 for high accuracy) ---
def extract_tamil_text(image):
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Upscale for complex ligatures
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    custom_config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=custom_config).strip()

# --- 3. UI and History Logic ---
st.title("🏛️ 1000% Precision Tamil OCR & Dictionary")

dataset = load_dataset()

# Initialize session state with safety
if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload Tamil Doc", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        with st.spinner("Extracting precisely..."):
            text = ""
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text += extract_tamil_text(page.to_image(resolution=500).original) + "\n\n"
            else:
                text = extract_tamil_text(Image.open(uploaded_file))
            st.subheader("📄 OCR Result")
            st.text_area("Copy content:", text, height=400)

with col2:
    st.subheader("🔍 Precision Lookup")
    word_query = st.text_input("Enter Tamil word:")
    
    if word_query:
        word_query = word_query.strip()
        
        # Priority 1: Dataset
        ds_res = find_in_dataset(dataset, word_query)
        if ds_res:
            m, a = ds_res
            explanation = f"'{word_query}' என்பதன் பொருள் '{m}' ஆகும். இதன் எதிர்ச்சொல் '{a}' ஆகும்."
            source = "Dataset"
        else:
            # Priority 2: Precision API
            with st.spinner("Verifying semantics..."):
                explanation = get_precision_data(word_query)
                source = "Precision API"
        
        # Save to history (Preventing KeyError by checking session state)
        st.session_state.history.insert(0, {"word": word_query, "exp": explanation, "src": source})

    # Display History with safety get() to avoid KeyError
    st.markdown("### 🕒 Search History")
    for entry in st.session_state.history:
        word = entry.get('word', 'Unknown')
        exp = entry.get('exp', 'No data')
        src = entry.get('src', 'Source')
        
        with st.expander(f"📖 {word} ({src})", expanded=True):
            st.write(exp)

if st.sidebar.button("Reset Everything"):
    st.session_state.history = []
    st.cache_data.clear()
    st.rerun()
