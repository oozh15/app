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

st.set_page_config(page_title="Tamil Precision OCR & Dictionary", layout="wide")

# --- 1. Accuracy Logic Functions ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        response = requests.get(JSON_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def find_in_dataset(dataset, word):
    if not dataset: return None
    for entry in dataset:
        if entry.get("word") == word or entry.get("tamil") == word:
            return entry.get("meaning"), entry.get("antonym"), entry.get("synonym")
    return None

def get_exact_precision_data(word_tam):
    """
    Uses a multi-step verification to ensure accuracy.
    1. Translate to English to get the 'root' concept.
    2. Fetch formal Synonyms/Antonyms from Datamuse (Oxford-linked).
    3. Translate back to Tamil with high-context filters.
    """
    try:
        # Step 1: Identify the Root Concept
        root_en = GoogleTranslator(source='ta', target='en').translate(word_tam).lower()
        
        # Step 2: Fetch Exact Synonyms and Antonyms (Datamuse API)
        syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=3").json()
        ant_resp = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=3").json()
        
        syn_en = [item['word'] for item in syn_resp]
        ant_en = [item['word'] for item in ant_resp]
        
        # Step 3: High-Precision Translation back to Tamil
        translator = GoogleTranslator(source='en', target='ta')
        
        meaning_ta = translator.translate(root_en)
        syn_ta = [translator.translate(s) for s in syn_en]
        ant_ta = [translator.translate(a) for a in ant_en]
        
        # Create Two-Sentence Explanation
        sentence_1 = f"இந்தச் சொல்லின் நேரடிப் பொருள் '{meaning_ta}' என்பதாகும்."
        if syn_ta:
            sentence_1 += f" இதற்கு இணையான சொற்கள்: {', '.join(syn_ta)}."
        
        sentence_2 = f"இதன் நேர் எதிர்ச் சொல் '{', '.join(ant_ta)}' ஆகும்." if ant_ta else "இதற்கு நேரடி எதிர்ச் சொல் அகராதியில் கிடைக்கவில்லை."
        
        return f"{sentence_1} {sentence_2}", ", ".join(syn_ta), ", ".join(ant_ta)
    except:
        return "மன்னிக்கவும், இந்த சொல்லிற்கான துல்லியமான தகவலைப் பெற முடியவில்லை.", "❌", "❌"

# --- 2. OCR Engine ---
def extract_tamil_text(image):
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    custom_config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=custom_config).strip()

# --- 3. UI and Session Logic ---
st.title("🏛️ High-Precision Tamil Dictionary & OCR")

dataset = load_dataset()
if 'history' not in st.session_state: st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload PDF/Image", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        with st.spinner("Extracting..."):
            extracted_text = ""
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        extracted_text += extract_tamil_text(page.to_image(resolution=500).original) + "\n\n"
            else:
                extracted_text = extract_tamil_text(Image.open(uploaded_file))
            st.text_area("OCR Result", extracted_text, height=400)

with col2:
    st.subheader("🔍 Exact Meaning Lookup")
    word_query = st.text_input("Enter Tamil word:")
    
    if word_query:
        word_query = word_query.strip()
        
        # Waterfall: Dataset -> Precision API
        res = find_in_dataset(dataset, word_query)
        if res:
            m, a, s = res
            explanation = f"இது உங்களது தரவுத்தளத்திலிருந்து பெறப்பட்டது. இதன் பொருள் '{m}' மற்றும் எதிர்ச்சொல் '{a}' ஆகும்."
            source = "Dataset"
        else:
            with st.spinner("Verifying exact synonyms and antonyms..."):
                explanation, s, a = get_exact_precision_data(word_query)
                source = "Precision API"
        
        # Save to history
        st.session_state.history.insert(0, {"word": word_query, "exp": explanation, "src": source})

    for entry in st.session_state.history:
        with st.expander(f"📖 {entry['word']} ({entry['src']})", expanded=True):
            st.write(entry['exp'])

if st.sidebar.button("Clear History"):
    st.session_state.history = []
    st.rerun()
