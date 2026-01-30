import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Tamil OCR Pro + Dictionary", layout="wide")

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

# --- Load Tamil Dictionary ---
@st.cache_data
def load_dictionary():
    # Sample CSV format: word,meaning
    # Replace 'tamil_dict.csv' with your full dataset
    df = pd.read_csv("tamil_dict.csv")
    return dict(zip(df['word'], df['meaning']))

tamil_dict = load_dictionary()

# --- App UI ---
st.title("📘 Tamil OCR + Word Meaning Lookup")
st.markdown("Extract text from Tamil PDFs/Images and check meanings of unknown words.")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    extracted_full = ""
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    img = page.to_image(resolution=500).original
                    page_text = extract_tamil_text(img)
                    extracted_full += f"--- Page {i+1} ---\n{page_text}\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_full = extract_tamil_text(img)

    st.subheader("📄 Extracted Content")
    text_area = st.text_area("Final Output", extracted_full, height=500)

    st.download_button(
        label="Download as Text File",
        data=extracted_full,
        file_name="extracted_tamil_text.txt",
        mime="text/plain"
    )

    # --- Unknown Word Lookup ---
    st.subheader("🔍 Check Word Meaning")
    user_word = st.text_input("Enter a Tamil word to check meaning:")
    
    if user_word:
        meaning = tamil_dict.get(user_word.strip())
        if meaning:
            st.success(f"✅ Meaning: {meaning}")
        else:
            st.warning("❌ Word not found in dictionary. Consider adding it to dataset.")
