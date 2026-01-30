import streamlit as st
import pdfplumber
from PIL import Image, ImageOps
import pytesseract
import cv2
import numpy as np
import re

# --- Page Config ---
st.set_page_config(page_title="Tamil OCR Pro", layout="wide")

# --- System Check (Helpful for Debugging) ---
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
    """Enhances image for better Tamil character recognition."""
    img_array = np.array(img)
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Scale up (Tamil curves need more pixels)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    # Binarization (Otsu's method is excellent for scanned documents)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    
    # --oem 3: LSTM engine (Neural Network)
    # --psm 4: Assume variable sizes and column detection (Best for Govt Orders)
    custom_config = r'--oem 3 --psm 4 -l tam'
    
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    
    # Post-OCR Cleanup
    # 1. Remove weird vertical bars often seen in OCR
    clean_text = raw_text.replace('|', '').replace('I', '')
    # 2. Normalize spacing
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    
    return clean_text.strip()

# --- App UI ---
st.title("📘 Tamil OCR PDF Reader")
st.markdown("Extracts text from Tamil Government Orders and Documents with high precision.")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    extracted_full = ""
    
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    # Higher resolution (500) for cleaner extraction
                    img = page.to_image(resolution=500).original
                    page_text = extract_tamil_text(img)
                    extracted_full += f"--- Page {i+1} ---\n{page_text}\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_full = extract_tamil_text(img)

    st.subheader("📄 Extracted Content")
    st.text_area("Final Output", extracted_full, height=500)
    
    st.download_button(
        label="Download as Text File",
        data=extracted_full,
        file_name="extracted_tamil_text.txt",
        mime="text/plain"
    )
