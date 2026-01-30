import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re
import base64

# --- Improved Normalization Logic ---
def get_root_word(word):
    """Strips common Tamil suffixes to find the base word for dictionary lookup."""
    # Clean non-Tamil characters and punctuation
    word = re.sub(r'[^\u0b80-\u0bff]', '', word)
    
    # List of common Tamil suffixes (declensions)
    # Ordered by length to strip the longest matches first
    suffixes = ['உக்காக', 'க்காக', 'ிருந்தது', 'உடைய', 'ோடு', 'இடம்', 'ுக்கு', 'உக்கு', 'ை', 'ால்', 'கு', 'ின்', 'இல்']
    
    found_root = word
    for s in suffixes:
        if word.endswith(s):
            # Ensure the root isn't too short after stripping
            potential_root = word[:-len(s)]
            if len(potential_root) >= 2:
                found_root = potential_root
                break
    return found_root

# --- Online Fetch Function ---
def fetch_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

# --- UI Setup ---
st.set_page_config(page_title="Tamil Lexicon Pro", layout="wide")

st.title("🏛️ Tamil Document Decoder")

uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    # Display PDF
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800"></iframe>'

    col1, col2 = st.columns([1.1, 0.9])
    with col1:
        st.subheader("📄 PDF Viewer")
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        st.subheader("🔍 Smart Lexicon")
        
        # OCR extraction
        images = convert_from_bytes(pdf_bytes)
        text_lines = []
        for img in images:
            page_text = pytesseract.image_to_string(img, lang='tam')
            text_lines.extend([l.strip() for l in page_text.split('\n') if len(l.strip()) > 3])

        if text_lines:
            selected_line = st.selectbox("Select a line:", text_lines)
            words = selected_line.split()
            target = st.radio("Choose word:", words, horizontal=True)

            if target:
                # 1. Try exact match
                clean_target = re.sub(r'[^\u0b80-\u0bff]', '', target)
                res = fetch_meaning(clean_target)
                
                # 2. If no match, try root word stripping
                if not res:
                    root = get_root_word(clean_target)
                    if root != clean_target:
                        st.info(f"Exact match not found. Searching for root word: '{root}'")
                        res = fetch_meaning(root)

                if res:
                    st.success(f"**Meaning:** {res}")
                else:
                    st.error("Meaning not found in online dataset.")
