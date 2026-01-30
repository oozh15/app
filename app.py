import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup

# --- Setup ---
st.set_page_config(page_title="தமிழ் OCR ரீடர்", layout="wide")

def fetch_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning_div = soup.find("div", {"class": "translation"})
        return meaning_div.text.strip() if meaning_div else None
    except:
        return None

st.title("🎯 தமிழ் ஆவண ஸ்கேனர் & அகராதி")
st.info("PDF அல்லது படத்தில் இருந்து சொற்களைக் காப்பி செய்ய முடியாவிட்டாலும், இது தானாகவே வாசித்து விளக்கம் தரும்.")

file = st.file_uploader("கோப்பை அப்லோட் செய்யவும் (Image/PDF)", type=['pdf', 'png', 'jpg', 'jpeg'])

if file:
    with st.spinner("OCR மூலம் எழுத்துக்களை வாசிக்கிறது..."):
        extracted_text = ""
        if file.type == "application/pdf":
            images = convert_from_bytes(file.read())
            for img in images:
                extracted_text += pytesseract.image_to_string(img, lang='tam')
        else:
            img = Image.open(file)
            extracted_text = pytesseract.image_to_string(img, lang='tam')

    # வரிகளைப் பிரித்தல்
    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]

    if lines:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📖 வாசிக்கப்பட்ட வரிகள்")
            selected_line = st.selectbox("வரியைத் தேர்வு செய்யவும்:", lines)
            words = selected_line.split()
            target_word = st.selectbox("சொல்லைத் தேர்வு செய்யவும்:", words)

        with col2:
            st.subheader("🔍 அகராதி விளக்கம்")
            if target_word:
                word_clean = target_word.strip(",.?!\"'")
                meaning = fetch_meaning(word_clean)
                if meaning:
                    st.success(f"**சொல்:** {word_clean}\n\n**பொருள்:** {meaning}")
                    st.write("---")
                    st.write("**உயர்தர விளக்கம்:**")
                    st.write(f"1. இது ஆவணத்தில் '{word_clean}' என்ற சூழலில் வருகிறது.")
                    st.write(f"2. இதன் அகராதிப் பொருள்: {meaning}")
                else:
                    st.warning("பொருள் கண்டறியப்படவில்லை.")
    else:
        st.error("மன்னிக்கவும், இந்த ஆவணத்திலிருந்து எழுத்துக்களை வாசிக்க முடியவில்லை.")

st.markdown("---")
st.caption("Standard High-Level OCR Lexicon Project 2026")
