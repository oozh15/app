import streamlit as st
import pdfplumber
import pytesseract
import requests
from PIL import Image
import cv2
import numpy as np
from docx import Document
import json
from difflib import get_close_matches

# -------------------------------
# Streamlit page setup
# -------------------------------
st.set_page_config(page_title="Tamil Professional Reader", layout="wide")
st.title("📘 Tamil Professional Reader (Non‑AI)")
st.caption("PDF / Image → Copy Word → Lookup Meaning (from word list)")

# -------------------------------
# OCR PREPROCESSING
# -------------------------------
def preprocess_image(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 2)
    return thresh

def extract_tamil_from_image(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(
        processed, lang="tam", config="--psm 6"
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
# LOAD WORD LIST FROM GITHUB
# -------------------------------
GITHUB_WORDLIST = "https://raw.githubusercontent.com/linuxkathirvel/eng2tamildictionary/master/dictionary.json"

@st.cache_data
def load_wordlist():
    try:
        res = requests.get(GITHUB_WORDLIST, timeout=10)
        res.raise_for_status()
        data = json.loads(res.text)
        return data
    except Exception as e:
        st.error(f"Failed to load word list: {e}")
        return {}

wordlist = load_wordlist()
tamil_words = list(wordlist.values())  # Tamil words list

# -------------------------------
# NORMALIZE WORD
# -------------------------------
def normalize_word(word):
    return word.strip()

# -------------------------------
# LOOKUP (FUZZY)
# -------------------------------
def lookup_word(word):
    word = normalize_word(word)
    if word in tamil_words:
        return f"Found in word list (no meaning): {word}", "—"
    
    # Fuzzy match suggestions
    matches = get_close_matches(word, tamil_words, n=3, cutoff=0.6)
    if matches:
        return "No exact match found. Suggestions: " + ", ".join(matches), "—"
    
    return "Word not found in word list", "—"

# -------------------------------
# DOCX EXPORT
# -------------------------------
def save_to_docx(word, meaning, antonym):
    doc = Document()
    doc.add_heading("Tamil Word Lookup", level=1)
    doc.add_paragraph(f"Word: {word}")
    doc.add_paragraph(f"Result: {meaning}")
    doc.add_paragraph(f"Antonym: {antonym}")
    file_name = "tamil_word_lookup.docx"
    doc.save(file_name)
    return file_name

# -------------------------------
# UI
# -------------------------------
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
    st.text_area("Copy any Tamil word from below:", extracted_text, height=300)

st.subheader("🔍 Word Lookup (no meanings available yet)")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Lookup"):
    if selected_word.strip():
        meaning, antonym = lookup_word(selected_word)

        st.success("Result")
        st.markdown(f"**📌 Word:** {selected_word}")
        st.markdown(f"**📖 Result:** {meaning}")
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
