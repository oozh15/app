import streamlit as st
import pdfplumber
import re
import tempfile
import os

st.set_page_config(page_title="Tamil PDF Text Extractor", layout="wide")
st.title("📄 Tamil PDF → Text Extractor (No OCR)")

uploaded_pdf = st.file_uploader("Upload TEXT-based Tamil PDF", type=["pdf"])

def clean_tamil_text(text):
    if not text:
        return ""

    # Keep only Tamil letters, spaces & punctuation
    text = re.sub(r"[^\u0B80-\u0BFF\s.,;:/()\-\n]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

if uploaded_pdf:
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, uploaded_pdf.name)

        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        extracted_text = ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    cleaned = clean_tamil_text(page_text)

                    extracted_text += f"\n--- Page {i+1} ---\n"
                    extracted_text += cleaned + "\n"

            if extracted_text.strip():
                st.success("✅ Tamil text extracted successfully")

                st.text_area(
                    "📜 Extracted Tamil Text",
                    extracted_text,
                    height=400
                )

                st.download_button(
                    "⬇ Download Text",
                    extracted_text,
                    file_name="tamil_text_output.txt",
                    mime="text/plain"
                )
            else:
                st.error("❌ PDF has no extractable text (likely scanned PDF)")

        except Exception as e:
            st.error(f"Failed to extract text: {e}")
