import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests

# --- Configuration & JSON Fetching ---
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

@st.cache_data
def load_tamil_dictionary():
    try:
        response = requests.get(JSON_URL)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

# --- OCR Engine Functions ---
def preprocess_for_tamil(img):
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    processed = preprocess_for_tamil(image)
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    clean_text = raw_text.replace('|', '').replace('I', '')
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- UI Setup ---
st.set_page_config(page_title="Tamil OCR & Dictionary", layout="wide")
st.title("📘 Tamil OCR with Vocabulary Lookup")

# Load Dictionary Data
tamil_dict = load_tamil_dictionary()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Extract Text")
    uploaded_file = st.file_uploader("Upload Tamil PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    
    extracted_full = ""
    if uploaded_file:
        with st.spinner("Processing..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        img = page.to_image(resolution=500).original
                        page_text = extract_tamil_text(img)
                        extracted_full += f"{page_text}\n\n"
            else:
                img = Image.open(uploaded_file)
                extracted_full = extract_tamil_text(img)

        st.text_area("Extracted Tamil Content", extracted_full, height=500, key="main_text")

with col2:
    st.subheader("2. Word Meaning Lookup")
    st.info("Find meanings for difficult words found in the text.")
    
    # Search box for "Tough" words
    lookup_word = st.text_input("Type or paste a Tamil word here:")
    
    if lookup_word:
        # Search in the JSON data
        # Assuming JSON structure is {"word": "meaning"} or list of dicts
        meaning = tamil_dict.get(lookup_word.strip())
        
        if meaning:
            st.success(f"**Meaning for {lookup_word}:**")
            st.write(meaning)
        else:
            st.warning("Word not found in your GitHub dictionary.")
            
    st.divider()
    with st.expander("View Entire Dictionary"):
        st.json(tamil_dict)

# --- System Sidebar ---
st.sidebar.title("Status")
if tamil_dict:
    st.sidebar.success(f"Dictionary Loaded: {len(tamil_dict)} words")
else:
    st.sidebar.error("Dictionary Load Failed")
