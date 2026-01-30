import streamlit as st
import pdfplumber
import pytesseract
import requests
from PIL import Image
import cv2
import numpy as np
import json

# -----------------------------
# LOAD DICTIONARY
# -----------------------------
@st.cache_data
def load_dictionary():
    url = "https://github.com/oozh15/app/raw/refs/heads/main/tamil.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = []

        # Parse each line as a separate JSON object (handles malformed JSON)
        for line in response.text.splitlines():
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip invalid lines
                    continue
        if not data:
            st.warning("Dataset loaded but no valid entries found.")
        return data

    except requests.RequestException as e:
        st.error(f"Failed to load dataset from GitHub: {e}")
        return []

dictionary = load_dictionary()

# -----------------------------
# APP CONFIG
# -----------------------------
st.set_page_config(page_title="Tamil Professional Reader", layout="wide")
st.title("📘 Tamil Professional Reader (Non-AI)")
st.caption("Upload PDF / Image → Copy Word → Get Meaning (From GitHub Dataset)")

# -----------------------------
# OCR FOR TAMIL
# -----------------------------
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
    return pytesseract.image_to_string(processed, lang="tam", config="--psm 6")

# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# -----------------------------
# WORD LOOKUP (FROM DICTIONARY)
# -----------------------------
def lookup_word(word):
    word = word.strip()
    for item in dictionary:
        if item.get("word") == word:
            return item.get("meaning"), item.get("synonym"), item.get("antonym")
    return None, None, None

# -----------------------------
# FILE UPLOAD
# -----------------------------
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
    st.text_area("Copy a Tamil word:", extracted_text, height=250)

# -----------------------------
# WORD MEANING LOOKUP
# -----------------------------
st.subheader("🔍 Word Meaning Lookup")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Meaning"):
    if not dictionary:
        st.error("Dictionary not loaded, cannot perform lookup.")
    else:
        meaning, synonym, antonym = lookup_word(selected_word)
        if meaning:
            st.success("Meaning Found ✅")
            st.markdown(f"**📌 Word:** {selected_word}")
            st.markdown(f"**📖 Meaning:** {meaning}")
            st.markdown(f"**🔁 Synonym:** {synonym}")
            st.markdown(f"**⛔ Antonym:** {antonym}")
        else:
            st.error("Word not found in dataset ❌")
