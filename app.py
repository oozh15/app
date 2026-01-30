import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re
import base64

# --- Page Setup ---
st.set_page_config(page_title="Tamil Lexicon Pro", layout="wide")

st.markdown("""
    <style>
    .reader-box { 
        height: 700px; overflow-y: scroll; padding: 20px; 
        background: white; border-radius: 10px; border: 1px solid #ddd;
        font-family: 'Latha', 'Arial', sans-serif; line-height: 2;
    }
    .dictionary-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        border-top: 10px solid #004d99; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

def get_online_meaning(word):
    """Fetch meaning from online Tamil dataset (Non-AI)"""
    clean_word = re.sub(r'[^\u0b80-\u0bff]', '', word)
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={clean_word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

st.title("🏛️ Tamil Document Decoder (Enterprise Edition)")

uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])

if uploaded_file:
    # 1. Display PDF using Base64 (Most stable way for online run)
    pdf_bytes = uploaded_file.read()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("📄 PDF Viewer")
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        st.subheader("🔍 Smart Lexicon")
        
        # 2. Extract Text for interaction
        with st.spinner("Processing Tamil lines..."):
            images = convert_from_bytes(pdf_bytes)
            text_lines = []
            for img in images:
                page_text = pytesseract.image_to_string(img, lang='tam')
                text_lines.extend([l.strip() for l in page_text.split('\n') if len(l.strip()) > 5])

        if text_lines:
            selected_line = st.selectbox("Select a line you find difficult:", text_lines)
            
            if selected_line:
                st.write(f"**Selected Line:** {selected_line}")
                words = selected_line.split()
                target_word = st.radio("Choose word to decode:", words, horizontal=True)

                if target_word:
                    with st.status(f"Searching dataset for '{target_word}'..."):
                        meaning = get_online_meaning(target_word)
                    
                    if meaning:
                        st.markdown(f"""
                            <div class="dictionary-card">
                                <h2 style='color: #004d99;'>{target_word}</h2>
                                <p><b>Meaning:</b> {meaning}</p>
                                <hr>
                                <p><b>Lexicon Note:</b> Standard academic meaning retrieved from online dataset.</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Meaning not found in online dataset.")
        else:
            st.error("No Tamil text detected. Ensure the PDF is clear.")

st.markdown("---")
st.caption("Standard 2026 Deployment | Non-AI | Real-time Dataset")
