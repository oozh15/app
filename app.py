import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests
import json
from googletrans import Translator

# --- Page Config ---
st.set_page_config(page_title="Tamil OCR Pro", layout="wide")

# --- System Status ---
st.sidebar.title("⚙️ System Status")
try:
    ver = pytesseract.get_tesseract_version()
    langs = pytesseract.get_languages()
    st.sidebar.success(f"Tesseract {ver} Active")
    if 'tam' in langs:
        st.sidebar.success("✅ Tamil Language Loaded")
    else:
        st.sidebar.error("❌ Tamil Data Missing")
except Exception as e:
    st.sidebar.error("Tesseract not found")

# --- Load Dictionary from GitHub ---
@st.cache_data
def load_dictionary():
    url = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"
    try:
        response = requests.get(url)
        data = response.json()
        return data  # { "word": "meaning", ... }
    except:
        return {}

tamil_dict = load_dictionary()

# --- OCR Preprocessing ---
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

# --- Meaning Lookup ---
translator = Translator()

@st.cache_data
def get_meaning(word):
    word = word.strip()
    if word in tamil_dict:
        return tamil_dict[word]
    else:
        try:
            # Fallback: Google Translate API
            result = translator.translate(word, src='ta', dest='en')
            return result.text
        except:
            return "❌ Meaning not found"

# --- App UI ---
st.title("📘 Tamil OCR Pro")
st.markdown("Extract text from PDFs/Images & get meanings of Tamil words instantly.")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    extracted_full = ""
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    img = page.to_image(resolution=500).original
                    page_text = extract_tamil_text(img)
                    extracted_full += f"--- Page {i+1} ---\n{page_text}\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_full = extract_tamil_text(img)

    # Display extracted text
    st.subheader("📄 Extracted Content")
    text_area = st.text_area("Final Output", extracted_full, height=400)

    # Split words and let user select
    st.subheader("🔍 Select Word to Get Meaning")
    words = list(set(re.findall(r'\w+', extracted_full)))  # unique words
    selected_word = st.selectbox("Select Tamil Word", [""] + words)

    if selected_word:
        meaning = get_meaning(selected_word)
        st.markdown(f"**Meaning of '{selected_word}':** {meaning}")

    # Download full text
    st.download_button(
        label="Download as Text File",
        data=extracted_full,
        file_name="extracted_tamil_text.txt",
        mime="text/plain"
    )
