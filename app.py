import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests

# --- தரவுத்தளம் லிங்க் ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil Precision Lexicon", layout="wide")

# --- 1. தரவுத்தளத்தை முதலில் தேடும் முறை ---
@st.cache_data(ttl=60)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_word_analysis(word_tam):
    # தேடும் சொல்லில் உள்ள தேவையில்லாத இடைவெளிகளை நீக்குதல்
    word_query = word_tam.strip()
    
    # --- முதல் முன்னுரிமை: DATASET (MUST DO FIRST) ---
    dataset = load_dataset()
    if dataset:
        for entry in dataset:
            # தரவுத்தளத்தில் உள்ள சொல்லையும் சுத்தம் செய்து ஒப்பிடுதல்
            db_word = str(entry.get("word", entry.get("tamil", ""))).strip()
            
            if db_word == word_query:
                return {
                    "source": "உங்களது தரவுத்தளம் (Dataset)",
                    "meaning": entry.get("meaning"),
                    "antonym": entry.get("antonym", "இல்லை"),
                    "synonym": entry.get("synonym", "இல்லை")
                }

    # --- இரண்டாம் முன்னுரிமை: AI BRIDGE (If not in dataset) ---
    try:
        to_en = GoogleTranslator(source='ta', target='en').translate(word_query).lower()
        to_ta = GoogleTranslator(source='en', target='ta')
        
        # 'அக்கறை' போன்ற சொற்களுக்கு AI தவறான பொருள் தருவதைத் தடுக்க கூடுதல் பாதுகாப்பு
        if "care" in to_en or "concern" in to_en:
            meaning = "கவனிப்பு / ஆர்வம்"
            ant = "அலட்சியம்"
        else:
            meaning = to_ta.translate(to_en)
            ant = "நேரடி எதிர்ச்சொல் இல்லை"

        return {
            "source": "செயற்கை நுண்ணறிவு (AI)",
            "meaning": meaning,
            "antonym": ant,
            "synonym": "இல்லை"
        }
    except:
        return None

# --- 2. பிழை இல்லாத OCR செயல்பாடுகள் ---
def preprocess_image(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_text(image):
    processed = preprocess_image(image)
    config = r'--oem 3 --psm 4 -l tam'
    return pytesseract.image_to_string(processed, config=config).strip()

# --- 3. UI அமைப்பு ---
st.title("📘 Tamil Word Precision Tool")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

extracted_text = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted_text += extract_text(page.to_image(resolution=500).original) + "\n\n"
    else:
        extracted_text = extract_text(Image.open(uploaded_file))
    
    st.subheader("📄 Extracted Text")
    st.text_area("OCR Result", extracted_text, height=300)

st.divider()

# சொல் தேடல் பகுதி
st.subheader("🔍 Search Word")
search_word = st.text_input("Enter Tamil word (எ.கா: அக்கறை):")

if search_word:
    res = get_word_analysis(search_word)
    if res:
        st.success(f"தேடல் ஆதாரம்: {res['source']}")
        st.markdown(f"### **விளக்கம்:** {res['meaning']}")
        st.markdown(f"**இணையான சொற்கள்:** {res.get('synonym', 'இல்லை')}")
        st.markdown(f"**எதிர்ச்சொல்:** {res['antonym']}")
    else:
        st.error("தகவல் கிடைக்கவில்லை.")
