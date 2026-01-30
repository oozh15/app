import streamlit as st
import pdfplumber
import pytesseract
import requests
import json
import re
from PIL import Image
import cv2
import numpy as np
from docx import Document

# --------------------------------
# CONFIG
# --------------------------------
st.set_page_config(page_title="Tamil Professional Reader", layout="wide")

DATASET_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# --------------------------------
# ULTRA AUTO-FIX JSON LOADER
# --------------------------------
@st.cache_data
def load_dictionary():
    try:
        res = requests.get(DATASET_URL, timeout=10)
        res.raise_for_status()
        text = res.text

        valid_entries = []

        # Extract every JSON object {...}
        objects = re.findall(r"\{[\s\S]*?\}", text)

        for obj in objects:
            try:
                item = json.loads(obj)
                if "word" in item and "meaning" in item:
                    valid_entries.append(item)
            except json.JSONDecodeError:
                continue  # skip broken entry

        if valid_entries:
            st.warning(f"⚠️ Dataset auto-fixed: {len(valid_entries)} valid entries loaded")
            return valid_entries

        st.error("❌ No valid entries found in dataset")
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
# PDF TEXT EXTRACTION
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
st.caption("PDF / Image → Extract Text → Word Meaning (Auto-Fixed Dataset)")

if dictionary:
    st.success(f"✅ Dictionary ready ({len(dictionary)} words)")
else:
    st.warning("⚠️ Dictionary empty")

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
# LOOKUP
# --------------------------------
st.subheader("🔍 Word Meaning Lookup")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Meaning"):
    if not selected_word.strip():
        st.warning("Please enter a Tamil word")
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
                    file_name=docx_file
                )
        else:
            st.error("Word not found in dataset ❌")
