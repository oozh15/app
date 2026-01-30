import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests

# --- Page Config ---
st.set_page_config(page_title="Tamil OCR Pro with Meaning", layout="wide")

# --- System Check ---
st.sidebar.title("⚙️ System Status")
try:
    ver = pytesseract.get_tesseract_version()
    langs = pytesseract.get_languages()
    st.sidebar.success(f"Tesseract {ver} Active")
    if 'tam' in langs:
        st.sidebar.success("✅ Tamil Language Loaded")
    else:
        st.sidebar.error("❌ Tamil Data Missing")
        st.sidebar.info("Add tesseract-ocr-tam to packages.txt")
except Exception as e:
    st.sidebar.error("Tesseract not found on system")

# --- OCR Engine ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    clean_text = raw_text.replace('|', '').replace('I', '')
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- Google Translate API ---
def tamil_to_english(word):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ta&tl=en&dt=t&q={word}"
    try:
        res = requests.get(url).json()
        return res[0][0][0]
    except:
        return None

def english_to_tamil(word):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ta&dt=t&q={word}"
    try:
        res = requests.get(url).json()
        return res[0][0][0]
    except:
        return None

def get_meaning_antonyms(word_ta):
    word_en = tamil_to_english(word_ta)
    if not word_en:
        return "❌ Meaning not found", "❌ Antonyms not found"
    
    meaning_ta = english_to_tamil(word_en)
    
    # Simple antonym fallback: use a static small dictionary for demo
    antonym_dict = {
        "good": "பொறாமை",
        "bad": "நல்ல",
        "hot": "சல்பு",
        "cold": "சூடு"
    }
    antonym_en = antonym_dict.get(word_en.lower(), "❌ Antonyms not found")
    antonym_ta = english_to_tamil(antonym_en) if antonym_en != "❌ Antonyms not found" else antonym_en
    
    return meaning_ta, antonym_ta

# --- App UI ---
st.title("📘 Tamil OCR with Meaning & Antonyms")
st.markdown("Upload Tamil PDF/Image → Extract text → Enter unknown word → Get Tamil meaning + antonyms.")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    extracted_full = ""
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    img = page.to_image(resolution=500).original
                    page_text = extract_tamil_text(img)
                    extracted_full += f"--- பக்கம் {i+1} ---\n{page_text}\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_full = extract_tamil_text(img)

    st.subheader("📄 Extracted Content")
    st.text_area("Final Output", extracted_full, height=400)

    # --- Word Meaning Input ---
    st.subheader("🔍 Get Meaning & Antonyms")
    word_input = st.text_input("Enter Tamil word (அறியாத சொல்)")
    if word_input:
        meaning, antonym = get_meaning_antonyms(word_input)
        st.write(f"**சொல்:** {word_input}")
        st.write(f"**அர்த்தம் (தமிழ்):** {meaning}")
        st.write(f"**எதிர்மறை சொல் (தமிழ்):** {antonym}")

    # --- Download ---
    st.download_button(
        label="Download as Text File",
        data=extracted_full,
        file_name="extracted_tamil_text.txt",
        mime="text/plain"
    )
