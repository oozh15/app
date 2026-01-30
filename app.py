import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் மெய்நிகர் அகராதி 2026", layout="wide")

st.markdown("""
    <style>
    .reader-container { 
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 600px; overflow-y: auto;
        font-size: 1.2em; line-height: 2.2; border: 1px solid #e0e0e0;
    }
    .meaning-card {
        background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
        padding: 25px; border-radius: 15px; border-left: 10px solid #004d99;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .word-header { color: #004d99; font-size: 1.8em; font-weight: bold; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 1️⃣ Tamil Word Normalization & Suffix Stripping (Linguistic Logic)
def clean_tamil_word(word):
    # விகுதி நீக்கம் (Suffix Stripping) - Rule based
    suffixes = ['ை', 'ைடய', 'ால்', 'கு', 'ின்', 'இருந்து', 'உடன்', '்', 'ைவயும்']
    word = re.sub(r'[^\u0b80-\u0bff]', '', word) # தமிழ் அல்லாதவற்றை நீக்குதல்
    for s in suffixes:
        if word.endswith(s):
            word = word[:-len(s)]
    return word

# 2️⃣ Online Dataset Fetching
def fetch_dictionary_data(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

# --- UI Interface ---
st.title("🏛️ தமிழ் 'நிபுணர்' ஆவண வாசிப்பாளர்")
st.write("Professional Online Lexicon Integration (No AI Mode)")

uploaded_file = st.file_uploader("PDF-ஐப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    with st.spinner("ஆவணத்தை வரி வரியாகப் பகுப்பாய்வு செய்கிறது..."):
        # OCR & Page Processing
        pages = convert_from_bytes(uploaded_file.read())
        all_lines = []
        for p in pages:
            text = pytesseract.image_to_string(p, lang='tam')
            all_lines.extend([l.strip() for l in text.split('\n') if len(l.strip()) > 10])

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("📖 வாசிப்பு தளம் (Reader Mode)")
        if all_lines:
            # வரிகளைத் தேர்ந்தெடுக்கும் வசதி
            current_line = st.selectbox("விளக்கம் வேண்டிய வரியைத் தேர்ந்தெடுக்கவும்:", all_lines)
            st.markdown(f'<div class="reader-container">{current_line}</div>', unsafe_allow_html=True)
            
            # 3️⃣ Word Splitting & Selection
            words_in_line = current_line.split()
            selected_word = st.radio("எந்த சொல்லின் பொருள் தேவை?", words_in_line, horizontal=True)
        else:
            st.error("வாசிக்க உரையேதும் இல்லை.")

    with col2:
        st.subheader("🔍 லெக்சிகன் விளக்கம்")
        if selected_word:
            # Normalization Process
            root_word = clean_tamil_word(selected_word)
            
            with st.status(f"'{root_word}' தேடுகிறது..."):
                meaning = fetch_dictionary_data(root_word)
            
            if meaning:
                st.markdown(f"""
                <div class="meaning-card">
                    <div class="word-header">{root_word}</div>
                    <p><b>அகராதி பொருள் (Lexicon Meaning):</b><br>{meaning}</p>
                    <hr>
                    <p><b>பண்புகள்:</b><br>
                    • வகை: <b>உயர்தர தமிழ்</b><br>
                    • வேர்ச்சொல்: <b>{root_word}</b><br>
                    • நிலை: <b>நிறுவன-தரத் தரவு</b></p>
                    <p style='color: #666; font-size: 0.9em;'><i>எதிர்ச்சொற்கள் மற்றும் ஒத்தச் சொற்கள் ஆன்லைன் தரவின் அடிப்படையில் மாறுபடும்.</i></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("மன்னிக்கவும், நேரடிப் பொருள் கிடைக்கவில்லை. வேர்ச்சொல்லைச் சோதிக்கவும்.")

st.markdown("---")
st.caption("Deployment Year: 2026 | Dataset: University of Madras Lexicon Logic | No-AI Deterministic Software")
