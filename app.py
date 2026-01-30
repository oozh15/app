import streamlit as st
import pdfplumber
from PIL import Image, ImageOps
import pytesseract
import cv2
import numpy as np
import re

# ---------------------------
# Improved Image Preprocessing
# ---------------------------
def preprocess_image(img):
    img = np.array(img)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Scale up if the image is small (crucial for OCR accuracy)
    height, width = gray.shape
    gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

    # Apply Dilation and Erosion to thicken thin characters
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=1)
    gray = cv2.erode(gray, kernel, iterations=1)

    # Advanced Thresholding: Otsu's Binarization works better for scanned docs
    # than simple adaptive thresholding in many cases.
    processed = cv2.threshold(cv2.medianBlur(gray, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    return processed

# ---------------------------
# OCR Tamil text from image
# ---------------------------
def ocr_image(image):
    processed = preprocess_image(image)
    
    # Tesseract Configuration:
    # --oem 3: Use LSTM OCR Engine (Best for Indic scripts)
    # --psm 3: Fully automatic page segmentation (better for varied layouts)
    custom_config = r'--oem 3 --psm 3 -l tam'
    
    text = pytesseract.image_to_string(processed, config=custom_config)
    
    # Improved Cleaning: 
    # Don't strip punctuation if you want natural text. 
    # Only remove excess weird symbols and fix spacing.
    text = re.sub(r'[^\u0B80-\u0BFF\s.,?!0-9]', '', text) 
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Keep paragraph breaks
    return text.strip()

# ---------------------------
# PDF → OCR text extraction
# ---------------------------
def extract_text_from_pdf(file):
    text_content = []
    with pdfplumber.open(file) as pdf:
        progress_bar = st.progress(0)
        total_pages = len(pdf.pages)
        
        for i, page in enumerate(pdf.pages):
            # Increase resolution to 500 for better Tamil character recognition
            pil_image = page.to_image(resolution=500).original
            page_text = ocr_image(pil_image)
            text_content.append(f"--- Page {i+1} ---\n{page_text}")
            progress_bar.progress((i + 1) / total_pages)
            
    return "\n\n".join(text_content)

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Pro Tamil OCR", layout="wide")
st.title("📘 Pro Tamil OCR Reader")

uploaded_file = st.file_uploader("Upload Tamil PDF or Image", type=["pdf","png","jpg","jpeg"])

if uploaded_file:
    with st.spinner("Processing... This may take a moment for large PDFs."):
        if uploaded_file.type == "application/pdf":
            extracted_text = extract_text_from_pdf(uploaded_file)
        else:
            image = Image.open(uploaded_file)
            # Show a preview of what we're working with
            st.image(image, caption="Uploaded Image", width=300)
            extracted_text = ocr_image(image)
    
    st.subheader("📄 Extracted Tamil Text")
    st.text_area("Result:", extracted_text, height=500)
    
    # Added: Download button for convenience
    st.download_button("Download as Text File", extracted_text, file_name="extracted_tamil.txt")
