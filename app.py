import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from deep_translator import GoogleTranslator
import requests

# --- 1. தரவுத்தளம் மற்றும் விதிகள் ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# AI முறைக்கான எதிர்ச்சொல் விதிகள்
ANTONYM_RULES = {
    "emotions": ["அலட்சியம்", "வெறுப்பு", "கவலையின்மை"],
    "quantity": ["அதிக", "கூடுதல்", "மேல்"],
    "quality": ["சிறந்த", "உயர்ந்த", "மேம்பட்ட"],
    "general": ["எதிர்ச்சொல் கிடைக்கவில்லை"]
}

st.set_page_config(page_title="Dataset-First Lexicon", layout="wide")

# --- 2. துல்லியமான தேடல் செயல்பாடுகள் ---

@st.cache_data(ttl=60)
def load_verified_data():
    """உங்களது GitHub JSON தரவை பதிவிறக்கம் செய்யும்."""
    try:
        r = requests.get(JSON_URL, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_word_analysis(word_tam, ocr_context=""):
    word_tam = word_tam.strip() # தேடும் சொல்லில் உள்ள தேவையில்லாத ஸ்பேஸை நீக்குதல்
    
    # --- LEVEL 1: DATASET (முதல் முன்னுரிமை) ---
    dataset = load_verified_data()
    if dataset:
        for entry in dataset:
            # தரவுத்தளத்தில் உள்ள சொல்லுடன் துல்லியமாக ஒப்பிடுதல்
            db_word = str(entry.get("word", entry.get("tamil", ""))).strip()
            if db_word == word_tam:
                return (f"**ஆதாரம்:** உங்களது தரவுத்தளம் (Verified Dataset)\n\n"
                        f"**விளக்கம்:** {entry.get('meaning')}\n\n"
                        f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                        f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"), "Dataset Match"

    # --- LEVEL 2: SENSE-AWARE AI (தரவுத்தளத்தில் இல்லை எனில் மட்டும்) ---
    try:
        to_en = GoogleTranslator(source='ta', target='en')
        to_ta = GoogleTranslator(source='en', target='ta')
        
        # சூழலை கண்டறிதல் (Context)
        context_sentence = word_tam
        if ocr_context:
            for line in ocr_context.splitlines():
                if word_tam in line:
                    context_sentence = line.strip()
                    break
        
        en_word = to_en.translate(word_tam).lower()
        en_context = to_en.translate(context_sentence).lower()

        # துல்லியத்தன்மை திருத்தம்: Care/Concern பிழைகளைத் தவிர்த்தல்
        sense = "general"
        if any(k in en_word or k in en_context for k in ["care", "concern", "worry"]):
            sense = "emotions"
            meaning_ta = "கவனிப்பு / ஆர்வம்"
            syns_ta = ["கவனம்", "ஈடுபாடு", "பற்று"]
        else:
            meaning_ta = to_ta.translate(en_word)
            # API மூலம் இணையான சொற்களைப் பெறுதல்
            syn_resp = requests.get(f"https://api.datamuse.com/words?rel_syn={en_word}&max=3").json()
            syns_ta = [to_ta.translate(i['word']) for i in syn_resp]

        ants_ta = ANTONYM_RULES.get(sense, ["கிடைக்கவில்லை"])

        res = (f"**ஆதாரம்:** செயற்கை நுண்ணறிவு (Lexical Bridge)\n\n"
               f"**விளக்கம்:** {meaning_ta}\n\n"
               f"**இணையான சொற்கள்:** {', '.join(syns_ta) if syns_ta else 'இல்லை'}\n\n"
               f"**எதிர்ச்சொல்:** {', '.join(ants_ta)}")
        
        return res, "AI Bridge"
    except:
        return "மன்னிக்கவும், தகவல் கிடைக்கவில்லை.", "Error"

# --- 3. மேம்படுத்தப்பட்ட OCR ---

def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # தெளிவுக்காக 2 மடங்கு பெரிதாக்குதல்
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # இரைச்சலை நீக்குதல் (Denoising)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(thresh, config=config).strip()

# --- 4. பயனர் இடைமுகம் (UI) ---

if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 ஆவணப் பதிவேற்றம்")
    f = st.file_uploader("Upload", type=["pdf", "png", "jpg", "jpeg"])
    ocr_text = ""
    if f:
        with st.spinner("OCR தரவைப் பிரிக்கிறது..."):
            if f.type == "application/pdf":
                with pdfplumber.open(f) as pdf:
                    for p in pdf.pages:
                        ocr_text += process_ocr(p.to_image(resolution=500).original) + "\n\n"
            else:
                ocr_text = process_ocr(Image.open(f))
            st.text_area("கண்டறியப்பட்ட உரை:", ocr_text, height=450)

with col2:
    st.subheader("🔍 துல்லியமான ஆய்வு")
    with st.form("search_form", clear_on_submit=True):
        word_input = st.text_input("தேட வேண்டிய சொல்:")
        if st.form_submit_button("ஆராய்க"):
            if word_input:
                res_block, src = get_word_analysis(word_input, ocr_text)
                st.session_state.history.insert(0, {"word": word_input, "block": res_block, "src": src})

    for item in st.session_state.history:
        with st.expander(f"📖 {item.get('word')} ({item.get('src')})", expanded=True):
            st.markdown(item.get('block'))

if st.sidebar.button("🗑️ Reset"):
    st.session_state.history = []
    st.rerun()
