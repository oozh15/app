import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests

# --- Configuration ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil OCR & Smart Dictionary", layout="wide")

# --- 1. Robust Dictionary Loader ---
@st.cache_data(ttl=600)  # Refresh cache every 10 mins
def load_tamil_dictionary():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(JSON_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

# --- 2. Advanced Tamil OCR Engine ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    # Grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Upscale 2x for intricate Tamil characters
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Denoise & Threshold
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    # PSM 4: Best for handling Gov Orders with headers/columns
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    
    # Cleanup artifacts
    clean_text = re.sub(r'[|I\[\]]', '', raw_text) # Remove common OCR noise symbols
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text) # Keep paragraphs
    return clean_text.strip()

# --- 3. UI Layout ---
st.title("📘 Tamil OCR + Smart Meaning Lookup")
st.markdown("Upload a Tamil document. Detected 'tough' words from your dictionary will appear as interactive buttons.")

# Sidebar Status
tamil_dict = load_tamil_dictionary()
if tamil_dict:
    st.sidebar.success(f"✅ Dictionary: {len(tamil_dict)} words loaded")
else:
    st.sidebar.error("❌ Dictionary Load Failed. Check GitHub JSON link or format.")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    extracted_full = ""

    if uploaded_file:
        with st.spinner("Extracting Tamil text with high precision..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        # High res 500 dpi for official documents
                        img = page.to_image(resolution=500).original
                        page_text = extract_tamil_text(img)
                        extracted_full += f"--- Page {i+1} ---\n{page_text}\n\n"
            else:
                img = Image.open(uploaded_file)
                extracted_full = extract_tamil_text(img)

        st.subheader("📄 Extracted Text")
        st.text_area("Copy text here:", extracted_full, height=450, key="ocr_output")

with col2:
    st.subheader("🔍 Smart Dictionary")
    
    if extracted_full and tamil_dict:
        st.info("Click a word below to see its meaning:")
        
        # Extract unique Tamil words from the OCR result
        found_words = re.findall(r'[\u0B80-\u0BFF]+', extracted_full)
        unique_matches = sorted(list(set([w for w in found_words if w in tamil_dict])))

        if unique_matches:
            # Display matching words as clickable buttons
            for word in unique_matches:
                if st.button(f"📖 {word}"):
                    st.success(f"**{word}**: {tamil_dict[word]}")
                    st.toast(f"{word}: {tamil_dict[word]}", icon="💡")
        else:
            st.write("No dictionary words detected in this document.")
    
    else:
        st.write("Process a document to see word definitions here.")

    # Manual Search
    st.divider()
    manual_search = st.text_input("Manual Search:")
    if manual_search and tamil_dict:
        res = tamil_dict.get(manual_search.strip())
        if res: st.success(res)
        else: st.warning("Not in dictionary.")
