import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="Tamil OCR PDF Reader", layout="wide")
st.title("📘 Tamil OCR PDF Reader")
st.caption("Upload Tamil PDF or Image → Extract accurate Tamil text")

# ---------------------------
# Image preprocessing for OCR
# ---------------------------
def preprocess_image(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Remove noise
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )
    return thresh

# ---------------------------
# OCR Tamil text from image
# ---------------------------
def ocr_image(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang='tam', config='--psm 6')
    # Clean unwanted characters
    text = re.sub(r'[^\u0B80-\u0BFF\s]', '', text)  # Keep only Tamil Unicode and spaces
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    return text.strip()

# ---------------------------
# PDF → OCR text extraction
# ---------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages):
            # Convert page to high-res image
            pil_image = page.to_image(resolution=400).original
            page_text = ocr_image(pil_image)
            text += page_text + "\n\n"
    return text.strip()

# ---------------------------
# File upload
# ---------------------------
uploaded_file = st.file_uploader("Upload Tamil PDF or Image", type=["pdf","png","jpg","jpeg"])
extracted_text = ""

if uploaded_file:
    st.info("Extracting Tamil text... Please wait.")
    if uploaded_file.type == "application/pdf":
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        image = Image.open(uploaded_file)
        extracted_text = ocr_image(image)
    
    st.subheader("📄 Extracted Tamil Text")
    st.text_area("Copy Tamil text below:", extracted_text, height=400)
