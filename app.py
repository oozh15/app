import streamlit as st
import pdfplumber
import pytesseract
import requests
import json
from PIL import Image
import cv2
import numpy as np

st.set_page_config(page_title="Tamil Professional Reader", layout="wide")

# -----------------------------------
# LOAD DATASET FROM GITHUB (ONLY THIS)
# -----------------------------------
DATASET_URL = "https://raw.githubusercontent.com/oozh15/app/refs/heads/main/tamil.json"

@st.cache_data
def load_dictionary():
    response = requests.get(DATASET_URL)
    response.raise_for_status()
    return json.loads(response.text)

dictionary = load_dictionary()

# -----------------------------------
# OCR FOR TAMIL
# -----------------------------------
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

# -----------------------------------
# PDF TEXT EXTRACTION
# -----------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# -----------------------------------
# WORD LOOKUP (FROM DATASET ONLY)
# -----------------------------------
def lookup_word(word):
    for item in dictionary:
        if item["word"] == word:
            return item["meaning"], item["synonym"], item["antonym"]
    return None, None, None

# -----------------------------------
# UI
# -----------------------------------
st.title("📘 Tamil Professional Reader (Non-AI)")
st.caption("PDF / Image → Copy Word → Meaning (From GitHub Dataset)")

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

# -----------------------------------
# LOOKUP
# -----------------------------------
st.subheader("🔍 Word Meaning Lookup")
selected_word = st.text_input("Paste a Tamil word here:")

if st.button("Get Meaning"):
    meaning, synonym, antonym = lookup_word(selected_word.strip())

    if meaning:
        st.success("Meaning Found")
        st.markdown(f"**📌 Word:** {selected_word}")
        st.markdown(f"**📖 Meaning:** {meaning}")
        st.markdown(f"**🔁 Synonym:** {synonym}")
        st.markdown(f"**⛔ Antonym:** {antonym}")
    else:
        st.error("Word not found in dataset")
