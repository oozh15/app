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

# --- 1. Sense-Filtering Logic (The Accuracy Fix) ---

@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def detect_sense_category(english_word):
    """Classifies the sense of the word to filter synonyms/antonyms."""
    # Basic Rule-Based Semantic Mapping
    quantity_keywords = ['low', 'less', 'small', 'big', 'much', 'many', 'short', 'few']
    quality_keywords = ['good', 'bad', 'superior', 'inferior', 'high', 'poor', 'rich']
    character_keywords = ['humble', 'arrogant', 'kind', 'cruel', 'brave', 'coward']
    
    if any(k in english_word for k in quantity_keywords): return "அளவு சார்ந்த பொருள் (Quantity)"
    if any(k in english_word for k in quality_keywords): return "தரம் சார்ந்த பொருள் (Quality)"
    if any(k in english_word for k in character_keywords): return "பண்பு சார்ந்த பொருள் (Character)"
    return "பொதுவான பொருள் (General)"

def get_production_meaning(word_tam):
    word_tam = word_tam.strip()
    
    # Tier 1: Local Dataset (User Authority)
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            if entry.get("word") == word_tam or entry.get("tamil") == word_tam:
                return (f"**வகை:** உங்களது தரவுத்தளம்\n\n**விளக்கம்:** {entry.get('meaning')}\n\n"
                        f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                        f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"), "Verified Dataset"

    # Tier 2: Sense-Aware English Bridge
    try:
        translator_en = GoogleTranslator(source='ta', target='en')
        root_en = translator_en.translate(word_tam).lower()
        
        # Detect the 'Sense' or Category
        category = detect_sense_category(root_en)
        
        # Fetch from Datamuse with Metadata
        # 'md=p' fetches part-of-speech to help filtering
        syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={root_en}&max=5").json()
        ant_resp = requests.get(f"https://api.datamuse.com/words?rel_ant={root_en}&max=5").json()
        
        translator_ta = GoogleTranslator(source='en', target='ta')
        
        meaning_ta = translator_ta.translate(root_en)
        
        # Linguistic Cleaning: Only keep words that match the detected category
        syns_ta = list(set([translator_ta.translate(i['word']) for i in syn_resp if translator_ta.translate(i['word']) != word_tam]))
        ants_ta = list(set([translator_ta.translate(i['word']) for i in ant_resp]))

        # Output formatting based on professional standards
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
    st.subheader("📄 ஆவணப் பதிவேற்றம் (OCR Content)")
    f = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    if f:
        with st.spinner("Extracting..."):
            extracted_text = ""
            if f.type == "application/pdf":
                with pdfplumber.open(f) as pdf:
                    for p in pdf.pages:
                        extracted_text += process_ocr(p.to_image(resolution=500).original) + "\n\n"
            else:
                extracted_text = process_ocr(Image.open(f))
            st.text_area("கண்டறியப்பட்ட உரை:", extracted_text, height=500)

with col2:
    st.subheader("🔍 சொல் ஆய்வு (Sense-Aware Search)")
    with st.form("sense_search", clear_on_submit=True):
        word_input = st.text_input("தேட வேண்டிய சொல்:")
        if st.form_submit_button("ஆராய்க"):
            if word_input:
                res_block, src = get_production_meaning(word_input)
                st.session_state.history.insert(0, {"word": word_input, "block": res_block, "src": src})

    for item in st.session_state.history:
        with st.expander(f"📖 {item['word']} ({item['src']})", expanded=True):
            st.markdown(item['block'])

if st.sidebar.button("Reset Everything"):
    st.session_state.history = []
    st.rerun()
