import streamlit as st
import pdfplumber
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2
import numpy as np
import re

def refine_image_for_tamil(img):
    # Convert PIL to OpenCV format
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 1. Increase contrast significantly
    # This helps Tesseract distinguish between 'r' (ர) and 'p' (ப) in low quality scans
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    
    # 2. Resizing with INTER_CUBIC (Crucial for Tamil fonts like 'Latha' or 'Bamini')
    height, width = gray.shape
    gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    # 3. Bilateral filtering (Removes noise but keeps edge sharpness)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # 4. Thresholding: Using a mix of Gaussian and Otsu
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 31, 10)
    
    return thresh

def ocr_tamil_engine(image):
    processed_img = refine_image_for_tamil(image)
    
    # CONFIGURATION EXPLANATION:
    # --oem 3: LSTM Neural Net (Best for Tamil)
    # --psm 4: Assume a single column of text of variable sizes (Best for G.O. formats)
    # -c preserve_interword_spaces=1: Maintains the tabular/indented look of Govt orders
    custom_config = r'--oem 3 --psm 4 -l tam --allow_blob_division T'
    
    text = pytesseract.image_to_string(processed_img, config=custom_config)
    
    # Post-Processing: Fix common OCR artifacts in Tamil
    text = text.replace('|', '')  # Removes vertical line artifacts
    text = re.sub(r'([0-9])\s+([0-9])', r'\1\2', text)  # Fixes broken numbers
    
    return text

def process_pdf(file):
    extracted_pages = []
    with pdfplumber.open(file) as pdf:
        total = len(pdf.pages)
        status = st.empty()
        for i, page in enumerate(pdf.pages):
            status.info(f"Processing Page {i+1} of {total}...")
            # Resolution 600 is the sweet spot for official documents
            img = page.to_image(resolution=600).original
            page_text = ocr_tamil_engine(img)
            extracted_pages.append(f"--- Page {i+1} ---\n{page_text}")
    return "\n\n".join(extracted_pages)

# --- Streamlit UI ---
st.title("🏛 Official Tamil Document OCR")
uploaded_file = st.file_uploader("Upload Government Order (PDF/Image)", type=["pdf", "jpg", "png"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        result = process_pdf(uploaded_file)
    else:
        img = Image.open(uploaded_file)
        result = ocr_tamil_engine(img)
    
    st.subheader("📝 Extracted Content")
    # Using height=800 to make it easier to compare with original
    st.text_area("Tamil Text Output", result, height=800)
    
    st.download_button("Save as .txt", result, file_name="Tamil_Extracted.txt")
