import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np

st.set_page_config(page_title="Tamil OCR PDF Reader", layout="wide")

# ---------------------------
# OCR FUNCTION
# ---------------------------
def preprocess_image(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )
    return thresh

def ocr_image(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang='tam', config='--psm 6')
    return text

# ---------------------------
# PDF → IMAGE → OCR
# ---------------------------
def extract_text_from_pdf_with_ocr(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages):
            # Convert PDF page to image
            pil_image = page.to_image(resolution=300).original
            page_text = ocr_image(pil_image)
            text += page_text + "\n"
    return text

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.title("📘 Tamil OCR PDF Reader")

uploaded_file = st.file_uploader(
    "Upload Tamil PDF",
    type=["pdf"]
)

if uploaded_file:
    st.info("Processing PDF with OCR... This may take a few seconds per page.")
    extracted_text = extract_text_from_pdf_with_ocr(uploaded_file)
    st.subheader("📄 Extracted Tamil Text")
    st.text_area("Copy text below:", extracted_text, height=400)
