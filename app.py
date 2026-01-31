import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests

# --- 1. Accuracy Rules & Assets ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# Semantic Rules for Accuracy when Dataset fails
ANTONYM_RULES = {
    "quantity": ["அதிக", "கூடுதல்", "மேல்"],
    "height": ["உயரமான", "நெடிய"],
    "quality": ["சிறந்த", "உயர்ந்த", "மேம்பட்ட"],
    "character": ["அகந்தையுள்ள", "செருக்குடைய"],
    "general": ["எதிர்ச்சொல் கிடைக்கவில்லை"]
}

st.set_page_config(page_title="Priority Tamil Lexicon", layout="wide")

# --- 2. Accuracy Engine ---

@st.cache_data(ttl=300)
def load_dataset():
    """Fetches your GitHub dataset as the primary source of truth."""
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def detect_sense(en_text):
    """Categorizes the word sense to pick correct antonyms."""
    text = en_text.lower()
    if any(k in text for k in ["amount", "less", "reduced", "quantity", "low"]): return "quantity"
    if any(k in text for k in ["short", "height", "tall"]): return "height"
    if any(k in text for k in ["quality", "standard", "inferior"]): return "quality"
    if any(k in text for k in ["humble", "modest", "arrogant"]): return "character"
    return "general"

def get_accurate_meaning(word_tam, ocr_context=""):
    word_tam = word_tam.strip()
    
    # --- PRIORITY 1: DATASET LINK ---
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            # Check for word match in your JSON
            if entry.get("word") == word_tam or entry.get("tamil") == word_tam:
                return (f"**ஆதாரம்:** உங்களது தரவுத்தளம் (Dataset)\n\n"
                        f"**விளக்கம்:** {entry.get('meaning')}\n\n"
                        f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                        f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"), "Verified Dataset"

    # --- PRIORITY 2: CONTEXTUAL BRIDGE (Other Ideas) ---
    try:
        to_en = GoogleTranslator(source='ta', target='en')
        to_ta = GoogleTranslator(source='en', target='ta')
        
        # Look for the sentence containing the word in OCR text for context
        sentence = word_tam
        if ocr_context:
            for line in ocr_context.splitlines():
                if word_tam in line:
                    sentence = line.strip()
                    break
        
        en_sentence = to_en.translate(sentence)
        en_word = to_en.translate(word_tam).lower()
        
        # Detect Sense & Fetch Synonyms
        sense = detect_sense(en_sentence)
        syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={en_word}&max=3").json()
        
        # Rule-based filtering
        syns_ta = [to_ta.translate(i['word']) for i in syn_resp]
        ants_ta = ANTONYM_RULES.get(sense, ["கிடைக்கவில்லை"])

        res = (f"**ஆதாரம்:** செயற்கை நுண்ணறிவு (Sense-Aware)\n\n"
               f"**விளக்கம்:** {to_ta.translate(en_word)}\n\n"
               f"**சூழல்:** {sentence}\n\n"
               f"**இணையான சொற்கள்:** {', '.join(syns_ta) if syns_ta else 'இல்லை'}\n\n"
               f"**எதிர்ச்சொல்:** {', '.join(ants_ta)}")
        
        return res, f"Sense: {sense.capitalize()}"
    except:
        return "**விளக்கம்:** தகவல் கிடைக்கவில்லை.", "Error"

# --- 3. Professional OCR ---



def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 4. UI Layout ---

if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 ஆவணப் பதிவேற்றம்")
    f = st.file_uploader("Upload", type=["pdf", "png", "jpg", "jpeg"])
    ocr_text = ""
    if f:
        if f.type == "application/pdf":
            with pdfplumber.open(f) as pdf:
                for p in pdf.pages:
                    ocr_text += process_ocr(p.to_image(resolution=500).original) + "\n\n"
        else:
            ocr_text = process_ocr(Image.open(f))
        st.text_area("Extracted Text", ocr_text, height=450, key="main_ocr")

with col2:
    st.subheader("🔍 உயர்-துல்லிய ஆய்வு")
    with st.form("acc_search", clear_on_submit=True):
        word_input = st.text_input("தேட வேண்டிய சொல்:")
        if st.form_submit_button("ஆராய்க"):
            if word_input:
                res_block, src = get_accurate_meaning(word_input, ocr_text)
                st.session_state.history.insert(0, {"word": word_input, "block": res_block, "src": src})

    for item in st.session_state.history:
        # Crash-proof history rendering
        w = item.get('word', 'Unknown')
        b = item.get('block', 'No data')
        s = item.get('src', 'Sense')
        with st.expander(f"📖 {w} ({s})", expanded=True):
            st.markdown(b)

if st.sidebar.button("🗑️ Reset History"):
    st.session_state.history = []
    st.rerun()
