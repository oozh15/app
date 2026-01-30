import streamlit as st
import pdfplumber
import pytesseract
import requests
from bs4 import BeautifulSoup
from PIL import Image
import cv2
import numpy as np
from docx import Document

st.set_page_config(page_title="Tamil Professional Reader", layout="wide")

# -------------------------------
# OCR IMPROVEMENT FOR TAMIL
# -------------------------------
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

def extract_tamil_from_image(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(
        processed,
        lang="tam",
        config="--psm 6"
    )
    return text

# -------------------------------
# PDF TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# -------------------------------
# ONLINE DICTIONARY FETCH (NO AI)
# -------------------------------
def fetch_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    res = requests.get(url, timeout=10)

    if res.status_code != 200:
        return "Meaning not found", "—"

    soup = BeautifulSoup(res.text, "html.parser")

    meaning_div = soup.find("div", {"class": "dictionaryMeaning"})
    antonym_div = soup.find("div", text=lambda t: t and "Antonym" in t)

    meaning = meaning_div.get_text(strip=True) if meaning_div else "Meaning not available"
    antonym = antonym_div.get_text(strip=True) if antonym_div else "Not available"

    return meaning, antonym

# -------------------------------
# DOCX EXPORT
# -------------------------------
def save_to_docx(word, meaning, antonym):
    doc = Document()
    doc.add_heading("Tamil Word Meaning", level=1)
    doc.add_paragraph(f"Word: {word}")
    doc.add_paragraph(f"Meaning: {meaning}")
    doc.add_paragraph(f"Antonym: {antonym}")
    file_name = "tamil_meaning.docx"
    doc.save(file_name)
    return file_name

# -------------------------------
# UI
# -------------------------------
st.title("📘 Tamil Professional Reader (Non-AI)")
st.caption("PDF / Image → Select Word → Meaning & Antonyms")

uploaded_file = st.file_uploader(
    "Upload Tamil PDF or Image",
    type=["pdf", "png", "jpg", "jpeg"]
)

extracted_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        image = Image.open(uploaded_file)
        extracted_text = extract_tamil_from_image(image)

    st.subheader("📄 Extracted Text")
    st.text_area("Copy any Tamil word from below:", extracted_text, height=250)

# -------------------------------
# WORD LOOKUP
# -------------------------------
st.subheader("🔍 Word Meaning Lookup")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Meaning"):
    if selected_word.strip():
        meaning, antonym = fetch_meaning(selected_word)

        st.success("Result Found")
        st.markdown(f"**📌 Word:** {selected_word}")
        st.markdown(f"**📖 Meaning:** {meaning}")
        st.markdown(f"**🔁 Antonym:** {antonym}")

        docx_file = save_to_docx(selected_word, meaning, antonym)
        with open(docx_file, "rb") as f:
            st.download_button(
                "⬇️ Download as DOCX",
                f,
                file_name=docx_file
            )
    else:
        st.warning("Please enter a Tamil word")
