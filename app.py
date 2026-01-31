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

st.set_page_config(page_title="Tamil Precision Bridge", layout="wide")

# --- 1. The English Bridge Logic (The Accuracy Core) ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_bridge_meaning(word_tam):
    word_tam = word_tam.strip()
    
    # Tier 1: Local Dataset First (User override)
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            if entry.get("word") == word_tam or entry.get("tamil") == word_tam:
                return (f"**விளக்கம்:** {entry.get('meaning')}\n\n"
                        f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                        f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"), "Verified Dataset"

    # Tier 2: The English Intelligence Bridge
    try:
        # A. Tamil -> English (Root Concept)
        to_en = GoogleTranslator(source='ta', target='en')
        root_en = to_en.translate(word_tam).lower()
        
        # B. Query English Lexical Database (Datamuse API)
        # This provides "Machine-Level" accuracy for Synonyms (rel_syn) and Antonyms (rel_ant)
        syn_data = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=3").json()
        ant_data = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=3").json()
        
        to_ta = GoogleTranslator(source='en', target='ta')
        
        # C. English -> Tamil (Return Path)
        meaning_ta = to_ta.translate(root_en)
        syns_ta = [to_ta.translate(i['word']) for i in syn_data if to_ta.translate(i['word']) != word_tam]
        ants_ta = [to_ta.translate(i['word']) for i in ant_data]

        # Formatting Output
        res = (f"**விளக்கம்:** {meaning_ta}\n\n"
               f"**இணையான சொற்கள்:** {', '.join(syns_ta) if syns_ta else 'இல்லை'}\n\n"
               f"**எதிர்ச்சொல்:** {', '.join(ants_ta) if ants_ta else 'கிடைக்கவில்லை'}")
        
        return res, "Lexical Bridge (En-Ta)"
    except:
        return "**விளக்கம்:** தகவல் கிடைக்கவில்லை.", "System Error"

# --- 2. Professional OCR Engine ---

def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # 2x Scaling for Tamil script clarity
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI Layout ---
if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 ஆவணப் பதிவேற்றம்")
    f = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    if f:
        with st.spinner("Extracting text..."):
            text = ""
            if f.type == "application/pdf":
                with pdfplumber.open(f) as pdf:
                    for p in pdf.pages:
                        text += process_ocr(p.to_image(resolution=500).original) + "\n\n"
            else:
                text = process_ocr(Image.open(f))
            st.text_area("கண்டறியப்பட்ட உரை:", text, height=500)

with col2:
    st.subheader("🔍 சொல் ஆய்வு (Bridge Analysis)")
    with st.form("bridge_search", clear_on_submit=True):
        word_input = st.text_input("தேட வேண்டிய சொல்:")
        if st.form_submit_button("ஆராய்க"):
            if word_input:
                res_block, src = get_bridge_meaning(word_input)
                st.session_state.history.insert(0, {"word": word_input, "block": res_block, "src": src})

    for item in st.session_state.history:
        with st.expander(f"📖 {item['word']} ({item['src']})", expanded=True):
            st.markdown(item['block'])

if st.sidebar.button("Reset Session"):
    st.session_state.history = []
    st.rerun()
