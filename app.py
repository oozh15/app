import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import requests
import json
import re
from pdf2image import convert_from_bytes

# -----------------------------
# LOAD DICTIONARY (AUTO-FIX)
# -----------------------------
@st.cache_data
def load_dictionary():
    url = "https://github.com/oozh15/app/raw/refs/heads/main/tamil.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text

        # Extract all JSON objects from broken file
        matches = re.findall(r'\{.*?\}', text, re.DOTALL)
        data = [json.loads(m) for m in matches]

        if not data:
            st.warning("Dataset loaded but no valid entries found.")
        else:
            st.success(f"Loaded {len(data)} words from dataset ✅")
        return data

    except requests.RequestException as e:
        st.error(f"Failed to load dataset from GitHub: {e}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON objects: {e}")
        return []

dictionary = load_dictionary()

# -----------------------------
# APP CONFIG
# -----------------------------
st.set_page_config(page_title="Tamil Professional Reader", layout="wide")
st.title("📘 Tamil Professional Reader (Non-AI)")
st.caption("Upload PDF / Image → Extract Tamil Text → Lookup Word Meaning")

# -----------------------------
# OCR PREPROCESSING
# -----------------------------
def preprocess_image(img):
    """
    Preprocess PIL image for better Tamil OCR:
    - Convert to grayscale
    - Resize for better recognition
    - Denoise
    - Adaptive threshold
    """
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )
    return thresh

def extract_tamil_from_image(image):
    """
    OCR a single PIL image to Tamil text
    """
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang='tam', config='--psm 6')
    # Remove non-Tamil and unwanted characters
    text = re.sub(r'[^அ-ஹா-௿\s.,/-]', '', text)
    return text

# -----------------------------
# PDF → IMAGE → OCR
# -----------------------------
def extract_text_from_pdf(file):
    """
    Convert scanned PDF pages to images and OCR each page
    """
    text = ""
    try:
        pages = convert_from_bytes(file.read())
        for page_num, page in enumerate(pages, start=1):
            page_text = extract_tamil_from_image(page)
            text += f"\n--- Page {page_num} ---\n" + page_text
    except Exception as e:
        st.error(f"Failed to extract text from PDF: {e}")
    return text

# -----------------------------
# WORD LOOKUP
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
