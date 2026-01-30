import streamlit as st
import pdfplumber
import pytesseract
import requests
import json
from PIL import Image
import cv2
import numpy as np
from docx import Document

# --------------------------------
# APP CONFIG
# --------------------------------
st.set_page_config(page_title="Tamil Professional Reader", layout="wide")

# --------------------------------
# DATASET URL (YOUR GITHUB RAW)
# --------------------------------
DATASET_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# --------------------------------
# LOAD + AUTO-FIX JSON DATASET
# --------------------------------
@st.cache_data
def load_dictionary():
    try:
        res = requests.get(DATASET_URL, timeout=10)
        res.raise_for_status()
        text = res.text.strip()

        # Try normal JSON load
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # AUTO-FIX: extract valid JSON array
        start = text.find("[")
        end = text.rfind("]") + 1

        if start != -1 and end != -1:
            fixed_text = text[start:end]
            data = json.loads(fixed_text)
            st.warning("⚠️ Dataset had errors – auto-fixed successfully")
            return data

        st.error("❌ Dataset is not valid JSON")
        return []

    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return []

dictionary = load_dictionary()

# --------------------------------
# OCR FOR IMAGES (TAMIL)
# --------------------------------
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
    return pytesseract.image_to_string(
        processed,
        lang="tam",
        config="--psm 6"
    )

# --------------------------------
# PDF TEXT EXTRACTION (NO OCR)
# --------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# --------------------------------
# WORD LOOKUP
# --------------------------------
def lookup_word(word):
    word = word.strip()
    for item in dictionary:
        if item.get("word") == word:
            return (
                item.get("meaning", "Not available"),
                item.get("synonym", "Not available"),
                item.get("antonym", "Not available"),
            )
    return None, None, None

# --------------------------------
# DOCX EXPORT
# --------------------------------
def save_to_docx(word, meaning, synonym, antonym):
    doc = Document()
    doc.add_heading("Tamil Word Meaning", level=1)
    doc.add_paragraph(f"Word: {word}")
    doc.add_paragraph(f"Meaning: {meaning}")
    doc.add_paragraph(f"Synonym: {synonym}")
    doc.add_paragraph(f"Antonym: {antonym}")
    file_name = "tamil_meaning.docx"
    doc.save(file_name)
    return file_name

# --------------------------------
# UI
# --------------------------------
st.title("📘 Tamil Professional Reader (Non-AI)")
st.caption("PDF / Image → Extract Text → Word Meaning (From GitHub Dataset)")

if dictionary:
    st.success(f"✅ Dataset loaded: {len(dictionary)} entries")
else:
    st.warning("⚠️ Dataset not loaded")

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
    st.text_area(
        "Copy a Tamil word from below:",
        extracted_text,
        height=250
    )

# --------------------------------
# LOOKUP SECTION
# --------------------------------
st.subheader("🔍 Word Meaning Lookup")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Meaning"):
    if not selected_word.strip():
        st.warning("Please enter a Tamil word")
    elif not dictionary:
        st.error("Dataset unavailable")
    else:
        meaning, synonym, antonym = lookup_word(selected_word)

        if meaning:
            st.success("Meaning Found ✅")
            st.markdown(f"**📌 Word:** {selected_word}")
            st.markdown(f"**📖 Meaning:** {meaning}")
            st.markdown(f"**🔁 Synonym:** {synonym}")
            st.markdown(f"**⛔ Antonym:** {antonym}")

            docx_file = save_to_docx(
                selected_word, meaning, synonym, antonym
            )

            with open(docx_file, "rb") as f:
                st.download_button(
                    "⬇️ Download as DOCX",
                    f,
                    file_name=docx_file,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.error("Word not found in dataset ❌")
