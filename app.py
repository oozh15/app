import streamlit as st
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
import tempfile
import os

# 👉 Change if needed (Windows example)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Tamil PDF OCR", layout="wide")
st.title("📄 Tamil Government PDF → OCR Extractor")

uploaded_pdf = st.file_uploader("Upload Tamil PDF", type=["pdf"])

def preprocess_image(pil_img):
    img = np.array(pil_img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise
    denoise = cv2.medianBlur(gray, 3)

    # Improve contrast
    thresh = cv2.adaptiveThreshold(
        denoise, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )

    return thresh

if uploaded_pdf:
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, uploaded_pdf.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        st.info("🔄 Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)

        full_text = ""

        for i, img in enumerate(images):
            st.subheader(f"📄 Page {i+1}")

            processed_img = preprocess_image(img)
            st.image(processed_img, caption=f"Processed Page {i+1}", use_container_width=True)

            text = pytesseract.image_to_string(
                processed_img,
                lang="tam",
                config="--oem 3 --psm 6"
            )

            if text.strip():
                full_text += f"\n--- Page {i+1} ---\n{text}\n"
            else:
                full_text += f"\n--- Page {i+1} ---\n[No readable text]\n"

        st.success("✅ OCR Completed")

        st.text_area("📜 Extracted Tamil Text", full_text, height=400)

        st.download_button(
            "⬇ Download Text",
            data=full_text,
            file_name="tamil_ocr_output.txt",
            mime="text/plain"
        )
