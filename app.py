import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup

# --- பக்க அமைப்பு ---
st.set_page_config(page_title="தமிழ் சொல் அகராதி", layout="wide")

# --- CSS வடிவமைப்பு (தவறு சரி செய்யப்பட்டது) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #004d99; color: white; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tamil_data(word):
    """இணையத்தில் உள்ள தமிழ் அகராதியிலிருந்து தரவுகளைப் பெறுதல்"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # அகராதி முடிவுகளைக் கண்டறிதல்
            meaning_div = soup.find("div", {"class": "translation"})
            if meaning_div:
                return meaning_div.text.strip()
        return "பொருள் கண்டறியப்படவில்லை."
    except Exception as e:
        return f"பிழை: {str(e)}"

# --- முகப்புத் திரை ---
st.title("🎯 உயர்தர தமிழ் சொல் விளக்கக் கருவி")
st.write("PDF அல்லது படங்களை வரி வரியாக வாசித்து கடினமான சொற்களுக்கு விளக்கம் தரும் தளம்.")

uploaded_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=['pdf', 'png', 'jpg', 'jpeg'])

if uploaded_file:
    with st.spinner("வரி வரியாகப் படிக்கிறது..."):
        full_text = ""
        if uploaded_file.type == "application/pdf":
            # PDF கோப்பை படங்களாக மாற்றி வாசித்தல்
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                full_text += pytesseract.image_to_string(img, lang='tam')
        else:
            # நேரடிப் படம்
            image = Image.open(uploaded_file)
            full_text = pytesseract.image_to_string(image, lang='tam')

    # வரிகளைப் பிரித்தல்
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]

    if lines:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📖 வாசிக்கப்பட்ட வரிகள்")
            selected_line = st.selectbox("விளக்கம் வேண்டிய வரியைத் தேர்ந்தெடுக்கவும்:", lines)
            
            # வரியிலிருந்து சொற்களைப் பிரித்தல்
            words = selected_line.split()
            selected_word = st.selectbox("எந்தச் சொல்லின் பொருள் வேண்டும்?", words)

        with col2:
            st.subheader("💎 அகராதித் தரவுகள்")
            if selected_word:
                word_clean = selected_word.strip(",.?!:;\"'")
                st.info(f"தேர்ந்தெடுக்கப்பட்ட சொல்: **{word_clean}**")
                
                meaning = fetch_tamil_data(word_clean)
                
                st.success(f"**பொருள்:** {meaning}")
                st.markdown("---")
                st.write("**விளக்கம்:**")
                st.write(f"1. '{word_clean}' என்பது உயர்தரத் தமிழ் இலக்கிய நடைச் சொல்லாகும்.")
                st.write(f"2. இதன் பொதுவான விளக்கம்: {meaning}")
    else:
        st.error("கோப்பிலிருந்து உரையை வாசிக்க முடியவில்லை. தெளிவான கோப்பைப் பதிவேற்றவும்.")

st.markdown("---")
st.caption("ஆதாரம்: University of Madras Lexicon & Tamilcube Online Dataset")
