import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests

# --- Page Config ---
st.set_page_config(page_title="Tamil OCR + Meaning & Antonyms", layout="wide")
st.title("📘 Tamil OCR & Word Meaning Tool")
st.markdown("""
Upload a Tamil PDF/Image document to extract text.  
Click or enter any unknown Tamil word to get its **meaning** and **antonyms** in Tamil.
""")

# --- OCR Functions ---
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
    clean_text = raw_text.replace('|','').replace('I','')
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- Meaning & Antonyms Functions ---
def fetch_english_antonyms(word_en):
    url = f"https://api.datamuse.com/words?rel_ant={word_en}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        antonyms = [item['word'] for item in data]
        return antonyms if antonyms else ["❌ Antonyms not found"]
    except:
        return ["❌ Antonyms not found"]

def get_tamil_meaning(word_tam):
    try:
        meaning_en = GoogleTranslator(source='ta', target='en').translate(word_tam)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(meaning_en)
        return meaning_en, meaning_ta
    except:
        return None, "❌ Meaning not found"

def get_antonyms_tamil(meaning_en):
    antonyms_en = fetch_english_antonyms(meaning_en)
    antonyms_ta = []
    for ant in antonyms_en:
        if ant == "❌ Antonyms not found":
            antonyms_ta.append(ant)
        else:
            try:
                ant_ta = GoogleTranslator(source='en', target='ta').translate(ant)
                antonyms_ta.append(ant_ta)
            except:
                antonyms_ta.append("❌ Antonyms not found")
    return antonyms_ta

# --- Upload Section ---
uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

extracted_text = ""
if uploaded_file:
    with st.spinner("Processing Tamil Text..."):
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    img = page.to_image(resolution=500).original
                    extracted_text += extract_tamil_text(img) + "\n\n"
        else:
            img = Image.open(uploaded_file)
            extracted_text = extract_tamil_text(img)

    st.subheader("📄 Extracted Tamil Text")
    st.text_area("OCR Output", extracted_text, height=400)

# --- Word Meaning & Antonyms Section ---
st.subheader("🔍 Get Meaning & Antonyms")
word_tam = st.text_input("Enter Tamil word (அறியாத சொல்)")

if word_tam:
    with st.spinner("Fetching meaning and antonyms..."):
        meaning_en, meaning_ta = get_tamil_meaning(word_tam)
        antonyms_ta = get_antonyms_tamil(meaning_en)

        st.write(f"**சொல்:** {word_tam}")
        st.write(f"**அர்த்தம் (தமிழ்):** {meaning_ta}")
        st.write(f"**எதிர்மறை சொல் (தமிழ்):** {', '.join(antonyms_ta)}")
