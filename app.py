import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests
import json

# --- Configuration ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(page_title="Tamil OCR & Smart Dictionary", layout="wide")

# --- 1. Robust JSON Auto-Fixer ---
@st.cache_data(ttl=300)
def load_tamil_dictionary():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Force raw content link
        raw_url = JSON_URL.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        response = requests.get(raw_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text.strip()
            
            # AUTO-FIX: Remove trailing commas before closing braces/brackets
            content = re.sub(r',\s*([\]}])', r'\1', content)
            # AUTO-FIX: Remove BOM or weird invisible characters
            content = content.encode('utf-8-sig').decode('utf-8-sig')
            
            return json.loads(content)
        else:
            return None
    except Exception:
        return None

# --- 2. Advanced Tamil OCR Engine ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Upscale 2x for better curve detection
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Denoise and Otsu Thresholding
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    # PSM 4: Best for layouts with columns/headers (like G.O.s)
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    
    # Clean OCR noise
    clean_text = re.sub(r'[|I\[\]\\]', '', raw_text)
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- 3. UI Layout ---
st.title("📘 Tamil OCR + Smart Meaning Lookup")

# Sidebar Status & Debug
st.sidebar.title("Dictionary Status")
tamil_dict = load_tamil_dictionary()

if tamil_dict:
    st.sidebar.success(f"✅ {len(tamil_dict)} words loaded")
    if st.sidebar.button("Refresh Dictionary"):
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.error("❌ Dictionary Load Failed")
    st.sidebar.info("Possible issues: Trailing commas, missing quotes, or private GitHub repo.")
    st.sidebar.code(JSON_URL)

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload Tamil PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    extracted_full = ""

    if uploaded_file:
        with st.spinner("Processing..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        img = page.to_image(resolution=500).original
                        page_text = extract_tamil_text(img)
                        extracted_full += f"--- Page {i+1} ---\n{page_text}\n\n"
            else:
                img = Image.open(uploaded_file)
                extracted_full = extract_tamil_text(img)

        st.subheader("📄 Extracted Text")
        st.text_area("Tamil Content:", extracted_full, height=500)

with col2:
    st.subheader("🔍 Smart Lookup")
    if extracted_full and tamil_dict:
        # Find dictionary words inside the extracted text
        found_tokens = re.findall(r'[\u0B80-\u0BFF]+', extracted_full)
        matches = sorted(list(set([w for w in found_tokens if w in tamil_dict])))

        if matches:
            st.write("Click a word to see its meaning:")
            for word in matches:
                if st.button(f"📖 {word}", key=f"btn_{word}"):
                    st.info(f"**{word}**: {tamil_dict[word]}")
                    st.toast(f"{word}: {tamil_dict[word]}")
        else:
            st.write("No dictionary words found in this text.")
    else:
        st.write("Process a file to see meanings.")

    st.divider()
    manual = st.text_input("Manual Search:")
    if manual and tamil_dict:
        m_res = tamil_dict.get(manual.strip())
        if m_res: st.success(m_res)
        else: st.warning("Not in dictionary.")
