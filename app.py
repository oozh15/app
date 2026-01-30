import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests
import json

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Tamil OCR + Online Dictionary", layout="wide")

# ------------------------
# LOAD GITHUB JSON DICTIONARY
# ------------------------
DICT_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

@st.cache_data
def load_dictionary():
    try:
        res = requests.get(DICT_URL, timeout=10)
        res.raise_for_status()
        text = res.text

        # Try parsing entire JSON
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback: extract valid { ... } objects
        matches = re.findall(r"\{[\s\S]*?\}", text)
        valid = []
        for m in matches:
            try:
                obj = json.loads(m)
                if "word" in obj and "meaning" in obj:
                    valid.append(obj)
            except:
                continue
        return valid

    except Exception as e:
        st.error(f"Failed to load dictionary: {e}")
        return []

dictionary = load_dictionary()

if dictionary:
    st.sidebar.success(f"Dictionary Loaded ({len(dictionary)} entries)")
else:
    st.sidebar.warning("Dictionary not loaded or empty")

# ------------------------
# OCR HELPERS
# ------------------------
def preprocess_for_tamil(img):
    try:
        img_arr = np.array(img)
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        _, thresh = cv2.threshold(
            denoised, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return thresh
    except Exception as e:
        st.error(f"OCR Preprocessing failed: {e}")
        return img  # fallback

def extract_tamil_text(image):
    try:
        processed = preprocess_for_tamil(image)
        cfg = r'--oem 3 --psm 4 -l tam'
        raw_text = pytesseract.image_to_string(processed, config=cfg)
        clean_text = raw_text.replace("|", "").replace("I", "")
        clean_text = re.sub(r"\n\s*\n", "\n\n", clean_text)
        return clean_text.strip()
    except Exception as e:
        st.error(f"OCR Extraction failed: {e}")
        return ""

# ------------------------
# PDF → OCR
# ------------------------
def extract_text_from_pdf(file):
    full_text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for i, page in enumerate(pdf.pages):
                img = page.to_image(resolution=400).original
                page_text = extract_tamil_text(img)
                full_text += f"--- Page {i+1} ---\n{page_text}\n\n"
    except Exception as e:
        st.error(f"PDF processing failed: {e}")
    return full_text

# ------------------------
# WORD LOOKUP
# ------------------------
def lookup_word(word):
    word = word.strip()
    for item in dictionary:
        if item.get("word") == word:
            return (
                item.get("meaning", "Meaning not available"),
                item.get("synonym", "Synonym not available"),
                item.get("antonym", "Antonym not available")
            )
    return None, None, None

# ------------------------
# UI
# ------------------------
st.title("📘 Tamil OCR + Online Dictionary")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf","png","jpg","jpeg"])
extracted_text = ""

if uploaded_file:
    st.info("Extracting Tamil text (OCR)...")
    if uploaded_file.type == "application/pdf":
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        try:
            img = Image.open(uploaded_file)
            extracted_text = extract_tamil_text(img)
        except Exception as e:
            st.error(f"Image processing failed: {e}")

    st.subheader("📄 Extracted Text")
    st.text_area("Copy a Tamil word from below:", extracted_text, height=400)

# ------------------------
# LOOKUP SECTION
# ------------------------
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
        else:
            st.error("Word not found in the dictionary ❌")
