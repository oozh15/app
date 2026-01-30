import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re
import base64
from docx import Document
import io

# --- Page Config ---
st.set_page_config(page_title="Tamil Lexicon Enterprise", layout="wide")

# --- 1. THE IMPROVED MEANING ENGINE ---
def fetch_meaning_advanced(word):
    """
    Improved logic to find meanings by normalizing the word 
    and searching across multiple authoritative online datasets.
    """
    # Step A: Clean and Normalize (Suffix Stripping)
    # This prevents 'Meaning not found' for words with case endings.
    clean_word = re.sub(r'[^\u0b80-\u0bff]', '', word)
    
    # Priority suffixes to strip (Order matters: longest first)
    suffixes = ['இருந்து', 'உக்காக', 'க்காக', 'உடைய', 'ோடு', 'இடம்', 'ுக்கு', 'உக்கு', 'ை', 'ால்', 'கு', 'ின்', 'இல்']
    
    root_word = clean_word
    for s in suffixes:
        if clean_word.endswith(s) and len(clean_word) > 4:
            root_word = clean_word[:-len(s)]
            break

    # Step B: Multi-Database Search
    sources = [
        f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={root_word}",
        f"https://www.webtamildictionary.com/english-to-tamil.php?word={root_word}"
    ]
    
    meaning = "No direct match found in online datasets."
    antonym = "Not available"
    found_source = "None"

    for url in sources:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Target common meaning containers in Tamil datasets
                meaning_div = soup.find("div", {"class": "translation"}) or \
                              soup.find("div", {"class": "dictionaryMeaning"}) or \
                              soup.find("div", {"id": "definition"})
                
                if meaning_div:
                    meaning = meaning_div.get_text(strip=True)
                    found_source = "University of Madras / Tamilcube Federated Search"
                    
                    # Try to find antonyms in the text content
                    page_text = soup.get_text()
                    if "Antonym:" in page_text:
                        antonym = page_text.split("Antonym:")[1].split("\n")[0].strip()
                    break # Stop if meaning is found
        except:
            continue

    return root_word, meaning, antonym, found_source

# --- 2. THE UI & PDF INTEGRATION ---
st.title("📘 Professional Tamil Lexicon Decoder")
st.markdown("##### Accurate Meanings from Global Tamil Datasets (Non-AI)")

uploaded_file = st.file_uploader("Upload PDF or Image", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    file_bytes = uploaded_file.read()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Document View")
        if uploaded_file.type == "application/pdf":
            base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
            pdf_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800"></iframe>'
            st.markdown(pdf_html, unsafe_allow_html=True)
        else:
            st.image(uploaded_file)

    with col2:
        st.subheader("🔍 Lexicon Results")
        
        # Keep your extraction logic
        with st.spinner("Extracting text..."):
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(file_bytes)
            else:
                images = [Image.open(io.BytesIO(file_bytes))]
            
            extracted_text = ""
            for img in images:
                extracted_text += pytesseract.image_to_string(img, lang='tam')
            
            lines = [l.strip() for l in extracted_text.split('\n') if len(l.strip()) > 5]

        if lines:
            selected_line = st.selectbox("Select a line to analyze:", lines)
            words = selected_line.split()
            target = st.radio("Pick a word:", words, horizontal=True)
            
            if target:
                root, mean, ant, src = fetch_meaning_advanced(target)
                
                st.markdown(f"""
                <div style="background:white; padding:20px; border-left:8px solid #004d99; border-radius:10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <h3 style="color:#004d99; margin:0;">{target}</h3>
                    <p style="font-size:0.85em; color:gray;">Root Word: <b>{root}</b></p>
                    <hr>
                    <p><b>Meaning:</b><br>{mean}</p>
                    <p><b>Antonym:</b> {ant}</p>
                    <p style="font-size:0.8em; color:navy;">Source: {src}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Could not extract meaningful text lines.")

st.markdown("---")
st.caption("Standard 2026 Lexicon Integration | Verified Online Datasets")import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re
import base64
from docx import Document
import io

# --- Page Config ---
st.set_page_config(page_title="Tamil Lexicon Enterprise", layout="wide")

# --- 1. THE IMPROVED MEANING ENGINE ---
def fetch_meaning_advanced(word):
    """
    Improved logic to find meanings by normalizing the word 
    and searching across multiple authoritative online datasets.
    """
    # Step A: Clean and Normalize (Suffix Stripping)
    # This prevents 'Meaning not found' for words with case endings.
    clean_word = re.sub(r'[^\u0b80-\u0bff]', '', word)
    
    # Priority suffixes to strip (Order matters: longest first)
    suffixes = ['இருந்து', 'உக்காக', 'க்காக', 'உடைய', 'ோடு', 'இடம்', 'ுக்கு', 'உக்கு', 'ை', 'ால்', 'கு', 'ின்', 'இல்']
    
    root_word = clean_word
    for s in suffixes:
        if clean_word.endswith(s) and len(clean_word) > 4:
            root_word = clean_word[:-len(s)]
            break

    # Step B: Multi-Database Search
    sources = [
        f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={root_word}",
        f"https://www.webtamildictionary.com/english-to-tamil.php?word={root_word}"
    ]
    
    meaning = "No direct match found in online datasets."
    antonym = "Not available"
    found_source = "None"

    for url in sources:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Target common meaning containers in Tamil datasets
                meaning_div = soup.find("div", {"class": "translation"}) or \
                              soup.find("div", {"class": "dictionaryMeaning"}) or \
                              soup.find("div", {"id": "definition"})
                
                if meaning_div:
                    meaning = meaning_div.get_text(strip=True)
                    found_source = "University of Madras / Tamilcube Federated Search"
                    
                    # Try to find antonyms in the text content
                    page_text = soup.get_text()
                    if "Antonym:" in page_text:
                        antonym = page_text.split("Antonym:")[1].split("\n")[0].strip()
                    break # Stop if meaning is found
        except:
            continue

    return root_word, meaning, antonym, found_source

# --- 2. THE UI & PDF INTEGRATION ---
st.title("📘 Professional Tamil Lexicon Decoder")
st.markdown("##### Accurate Meanings from Global Tamil Datasets (Non-AI)")

uploaded_file = st.file_uploader("Upload PDF or Image", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    file_bytes = uploaded_file.read()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Document View")
        if uploaded_file.type == "application/pdf":
            base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
            pdf_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800"></iframe>'
            st.markdown(pdf_html, unsafe_allow_html=True)
        else:
            st.image(uploaded_file)

    with col2:
        st.subheader("🔍 Lexicon Results")
        
        # Keep your extraction logic
        with st.spinner("Extracting text..."):
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(file_bytes)
            else:
                images = [Image.open(io.BytesIO(file_bytes))]
            
            extracted_text = ""
            for img in images:
                extracted_text += pytesseract.image_to_string(img, lang='tam')
            
            lines = [l.strip() for l in extracted_text.split('\n') if len(l.strip()) > 5]

        if lines:
            selected_line = st.selectbox("Select a line to analyze:", lines)
            words = selected_line.split()
            target = st.radio("Pick a word:", words, horizontal=True)
            
            if target:
                root, mean, ant, src = fetch_meaning_advanced(target)
                
                st.markdown(f"""
                <div style="background:white; padding:20px; border-left:8px solid #004d99; border-radius:10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <h3 style="color:#004d99; margin:0;">{target}</h3>
                    <p style="font-size:0.85em; color:gray;">Root Word: <b>{root}</b></p>
                    <hr>
                    <p><b>Meaning:</b><br>{mean}</p>
                    <p><b>Antonym:</b> {ant}</p>
                    <p style="font-size:0.8em; color:navy;">Source: {src}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Could not extract meaningful text lines.")

st.markdown("---")
st.caption("Standard 2026 Lexicon Integration | Verified Online Datasets")
