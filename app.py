import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests

# --- Configuration ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Sense-Aware Tamil Lexicon", layout="wide")

# --- 1. Sense-Filtering Logic ---
@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def detect_sense_category(english_word, context_text=""):
    """Improved Sense detection using word keywords and context."""
    text = (english_word + " " + context_text).lower()
    
    quantity_keywords = ['low', 'less', 'small', 'big', 'much', 'many', 'short', 'few', 'amount', 'income', 'price']
    quality_keywords = ['good', 'bad', 'superior', 'inferior', 'high', 'poor', 'rich', 'standard']
    character_keywords = ['humble', 'arrogant', 'kind', 'cruel', 'brave', 'coward', 'modest']
    
    if any(k in text for k in quantity_keywords): return "அளவு சார்ந்த பொருள் (Quantity)"
    if any(k in text for k in quality_keywords): return "தரம் சார்ந்த பொருள் (Quality)"
    if any(k in text for k in character_keywords): return "பண்பு சார்ந்த பொருள் (Character)"
    return "பொதுவான பொருள் (General)"

def get_production_meaning(word_tam, context=""):
    word_tam = word_tam.strip()
    
    # Tier 1: Local Dataset First
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            if entry.get("word") == word_tam or entry.get("tamil") == word_tam:
                return (f"**வகை:** உங்களது தரவுத்தளம்\n\n**விளக்கம்:** {entry.get('meaning')}\n\n"
                        f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                        f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"), "Verified Dataset"

    # Tier 2: Sense-Aware English Bridge
    try:
        to_en = GoogleTranslator(source='ta', target='en')
        root_en = to_en.translate(word_tam).lower()
        context_en = to_en.translate(context[:100]) if context else ""
        
        category = detect_sense_category(root_en, context_en)
        
        # Fetch Synonyms/Antonyms
        syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=5").json()
        ant_resp = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=5").json()
        
        to_ta = GoogleTranslator(source='en', target='ta')
        meaning_ta = to_ta.translate(root_en)
        
        syns_ta = list(set([to_ta.translate(i['word']) for i in syn_resp if to_ta.translate(i['word']) != word_tam]))
        ants_ta = list(set([to_ta.translate(i['word']) for i in ant_resp]))

        res = (f"**வகை:** {category}\n\n"
               f"**விளக்கம்:** {meaning_ta}\n\n"
               f"**இணையான சொற்கள்:** {', '.join(syns_ta) if syns_ta else 'இல்லை'}\n\n"
               f"**எதிர்ச்சொல்:** {', '.join(ants_ta) if ants_ta else 'நேரடி எதிர்ச்சொல் இல்லை'}")
        
        return res, "Sense-Filtered Engine"
    except:
        return "**விளக்கம்:** தகவல் கிடைக்கவில்லை.", "Error"

# --- 2. Professional OCR Pipeline ---
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    
    
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 3. UI and Logic ---
if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 ஆவணப் பதிவேற்றம் (OCR)")
    f = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    extracted_text = ""
    if f:
        with st.spinner("Extracting..."):
            if f.type == "application/pdf":
                with pdfplumber.open(f) as pdf:
                    for p in pdf.pages:
                        extracted_text += process_ocr(p.to_image(resolution=500).original) + "\n\n"
            else:
                extracted_text = process_ocr(Image.open(f))
            st.text_area("கண்டறியப்பட்ட உரை:", extracted_text, height=450, key="ocr_output")

with col2:
    st.subheader("🔍 சொல் ஆய்வு (Context-Aware)")
    with st.form("sense_search", clear_on_submit=True):
        word_input = st.text_input("தேட வேண்டிய சொல்:")
        # New: Optional Context Window
        context_input = st.text_input("சூழல் (விருப்பத்தேர்வு):", placeholder="எ.கா: வருமானம் குறைந்துள்ளது")
        
        if st.form_submit_button("ஆராய்க"):
            if word_input:
                # Use provided context or grab snippet from OCR
                final_context = context_input if context_input else extracted_text[:200]
                res_block, src = get_production_meaning(word_input, final_context)
                st.session_state.history.insert(0, {"word": word_input, "block": res_block, "src": src})

    # --- SAFETY FIX FOR KEYERROR ---
    for item in st.session_state.history:
        # Using .get() ensures that if 'block' is missing, it returns a default string instead of crashing
        word = item.get('word', 'Unknown')
        block = item.get('block', item.get('exp', 'பழைய தரவு - தயவுசெய்து Reset செய்யவும்.'))
        src = item.get('src', 'Unknown')
        
        with st.expander(f"📖 {word} ({src})", expanded=True):
            st.markdown(block)

if st.sidebar.button("🗑️ Reset All (Fix Errors)"):
    st.session_state.history = []
    st.rerun()
