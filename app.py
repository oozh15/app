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

st.set_page_config(page_title="Tamil Precision Dictionary v2", layout="wide")

# --- 1. Accuracy Engine ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_exact_meaning(word_tam):
    word_tam = word_tam.strip()
    
    # Tier 1: Local Dataset Check
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            if entry.get("word") == word_tam or entry.get("tamil") == word_tam:
                return (f"இந்தச் சொல்லின் துல்லியமான பொருள் '{entry.get('meaning')}' ஆகும். "
                        f"இதன் எதிர்ச்சொல் '{entry.get('antonym')}' ஆகும்."), "Dataset"

    # Tier 2: Precision Lexicon Bridge (Wikipedia & Semantic Sync)
    try:
        # Step A: Get Root in English for precise mapping
        root_en = GoogleTranslator(source='ta', target='en').translate(word_tam).lower()
        
        # Step B: Fetch verified Synonyms/Antonyms
        syn_data = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=3").json()
        ant_data = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=3").json()
        
        syns_en = [i['word'] for i in syn_data]
        ants_en = [i['word'] for i in ant_data]
        
        # Step C: Re-Translate to Tamil with context
        translator = GoogleTranslator(source='en', target='ta')
        exact_meaning = translator.translate(root_en)
        syns_ta = [translator.translate(s) for s in syns_en]
        ants_ta = [translator.translate(a) for a in ants_en]

        # Formatting exactly two sentences
        s1 = f"'{word_tam}' என்பதன் துல்லியமான பொருள் '{exact_meaning}' ஆகும்; இதன் இணைச் சொற்கள்: {', '.join(syns_ta) if syns_ta else 'இல்லை'}."
        s2 = f"இதன் நேர் எதிரான எதிர்ச்சொல் '{', '.join(ants_ta) if ants_ta else 'கிடைக்கவில்லை'}' ஆகும்."
        
        return f"{s1} {s2}", "Precision Engine"
    except:
        return "மன்னிக்கவும், இச்சொல்லிற்கான துல்லியமான தரவு கிடைக்கவில்லை.", "Error"

# --- 2. Advanced OCR Pipeline ---
def extract_high_precision_text(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Scaling for exact character detection
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Image enhancement for Tesseract
    
    
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI Setup ---
if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    f = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])
    if f:
        with st.spinner("Extracting..."):
            text = ""
            if f.type == "application/pdf":
                with pdfplumber.open(f) as pdf:
                    for p in pdf.pages:
                        text += extract_high_precision_text(p.to_image(resolution=500).original) + "\n\n"
            else:
                text = extract_high_precision_text(Image.open(f))
            st.text_area("Extracted Tamil Text", text, height=500)

with col2:
    st.subheader("🔍 Precision Word Search")
    word_query = st.text_input("எந்தச் சொல்லின் பொருள் வேண்டும்?")
    
    if word_query:
        meaning, src = get_exact_meaning(word_query)
        # Prevent KeyErrors by cleaning history entries
        st.session_state.history.insert(0, {"word": word_query, "exp": meaning, "src": src})

    # Display History
    for entry in st.session_state.history:
        with st.expander(f"📖 {entry.get('word')} (Source: {entry.get('src')})", expanded=True):
            st.write(entry.get('exp'))

if st.sidebar.button("Clear Search History"):
    st.session_state.history = []
    st.rerun()
