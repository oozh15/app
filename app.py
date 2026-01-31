import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests

# --- Configuration & Dataset Link ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil OCR & Lexicon", layout="wide")
st.title("📘 Tamil OCR & Word Meaning Tool")

# --- 1. Dataset Logic (Priority 1) ---
@st.cache_data(ttl=60)
def load_verified_dataset():
    try:
        r = requests.get(JSON_URL, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 2. Meaning & Antonyms Engine ---
def fetch_english_antonyms(word_en):
    url = f"https://api.datamuse.com/words?rel_ant={word_en}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return [item['word'] for item in data[:3]] if data else []
    except:
        return []

def get_word_analysis(word_tam):
    word_tam = word_tam.strip()
    
    # --- LEVEL 1: CHECK DATASET ---
    dataset = load_verified_dataset()
    if dataset:
        for entry in dataset:
            db_word = str(entry.get("word", entry.get("tamil", ""))).strip()
            if db_word == word_tam:
                return {
                    "source": "உங்களது தரவுத்தளம் (Dataset)",
                    "meaning": entry.get("meaning"),
                    "antonyms": [entry.get("antonym", "இல்லை")]
                }

    # --- LEVEL 2: AI BRIDGE ---
    try:
        to_en = GoogleTranslator(source='ta', target='en')
        to_ta = GoogleTranslator(source='en', target='ta')
        
        en_word = to_en.translate(word_tam).lower()
        ta_meaning = to_ta.translate(en_word)
        
        # Sense Check for accuracy (Prevents "Tender" for "Care")
        if "care" in en_word or "concern" in en_word:
            ta_meaning = "கவனிப்பு / ஆர்வம்"
            ta_ants = ["அலட்சியம்", "கவலையின்மை"]
        else:
            en_ants = fetch_english_antonyms(en_word)
            ta_ants = [to_ta.translate(a) for a in en_ants] if en_ants else ["நேரடி எதிர்ச்சொல் இல்லை"]
            
        return {
            "source": "செயற்கை நுண்ணறிவு (AI)",
            "meaning": ta_meaning,
            "antonyms": ta_ants
        }
    except:
        return None

# --- 3. Fixed OCR Functions ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Corrected Indentation below
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    clean_text = raw_text.replace('|','').replace('I','')
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- 4. Streamlit UI Layout ---
uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

extracted_text = ""
if uploaded_file:
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    img = page.to_image(resolution=500).original
                    extracted_text += extract_tamil_text(img) + "\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_text = extract_tamil_text(img)

    st.subheader("📄 Extracted Tamil Text")
    st.text_area("OCR Output", extracted_text, height=300)

st.divider()

st.subheader("🔍 Search Word")
word_query = st.text_input("Enter Tamil word (அறியாத சொல்):")

if word_query:
    result = get_word_analysis(word_query)
    if result:
        st.info(f"ஆதாரம்: {result['source']}")
        st.write(f"**விளக்கம்:** {result['meaning']}")
        st.write(f"**எதிர்ச்சொற்கள்:** {', '.join(result['antonyms'])}")
    else:
        st.error("தகவல் கிடைக்கவில்லை.")
