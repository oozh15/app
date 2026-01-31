import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import requests
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

st.set_page_config(
    page_title="Tamil Lexicon Pro",
    layout="wide"
)

# ---------------- DATASET ----------------
@st.cache_data(ttl=3600)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=10)
        if r.status_code == 200:
            return r.json()   # must be dict format
    except:
        pass
    return {}

# ---------------- NORMALIZATION ----------------
def normalize_tamil(word):
    suffixes = [
        "கள்","வில்","இல்","ஆல்","க்கு","உம்",
        "ஐ","ஆக","இன்","உடன்","பால்"
    ]
    for s in suffixes:
        if word.endswith(s):
            return word[:-len(s)]
    return word

# ---------------- WIKTIONARY ----------------
def wiktionary_lookup(word):
    try:
        url = f"https://ta.wiktionary.org/wiki/{word}"
        html = requests.get(url, timeout=10).text
        match = re.search(r"<ol>.*?<li>(.*?)</li>", html, re.S)
        if match:
            clean = re.sub("<.*?>", "", match.group(1))
            return clean.strip()
    except:
        pass
    return None

# ---------------- MEANING ENGINE ----------------
def get_precision_meaning(word_tam):
    word_tam = normalize_tamil(word_tam.strip())

    dataset = load_dataset()

    # TIER 1 — DATASET (HIGHEST ACCURACY)
    if word_tam in dataset:
        entry = dataset[word_tam]
        meaning = entry.get("meaning", "—")
        antonyms = ", ".join(entry.get("antonym", [])) or "கிடைக்கவில்லை"

        return (
            f"'{word_tam}' என்பதன் துல்லியமான பொருள் '{meaning}' ஆகும். "
            f"இதன் எதிர்ச்சொல்(கள்): {antonyms}.",
            "Tamil Dictionary Dataset"
        )

    # TIER 2 — WIKTIONARY
    wiki = wiktionary_lookup(word_tam)
    if wiki:
        return (
            f"'{word_tam}' என்பதன் பொருள் '{wiki}' ஆகும். "
            f"எதிர்ச்சொல் தகவல் இல்லை.",
            "Tamil Wiktionary"
        )

    # TIER 3 — TRANSLATION (LAST RESORT)
    try:
        en = GoogleTranslator(source="ta", target="en").translate(word_tam)
        ta = GoogleTranslator(source="en", target="ta").translate(en)

        return (
            f"'{word_tam}' என்பதன் பொதுவான பொருள் '{ta}' ஆகும். "
            f"இது மொழிபெயர்ப்பு அடிப்படையிலான விளக்கம்.",
            "Translator (Fallback)"
        )
    except:
        return (
            "மன்னிக்கவும், இந்தச் சொல்லிற்கான பொருள் கிடைக்கவில்லை.",
            "Not Found"
        )

# ---------------- OCR ENGINE ----------------
def ocr_engine(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    config = r"--oem 3 --psm 4 -l tam"
    return pytesseract.image_to_string(thresh, config=config).strip()

# ---------------- UI STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 1])

# ---------------- LEFT PANEL ----------------
with col1:
    st.subheader("📄 ஆவணப் பதிவேற்றம்")
    file = st.file_uploader(
        "PDF / Image பதிவேற்றுக",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if file:
        with st.spinner("தமிழ் உரை பிரித்தெடுக்கப்படுகிறது..."):
            text = ""
            if file.type == "application/pdf":
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text += ocr_engine(
                            page.to_image(resolution=500).original
                        ) + "\n\n"
            else:
                text = ocr_engine(Image.open(file))

            st.text_area("Extracted Tamil Text", text, height=450)

# ---------------- RIGHT PANEL ----------------
with col2:
    st.subheader("🔍 சொல் தேடல்")

    with st.form("search_form", clear_on_submit=True):
        word = st.text_input("தேட வேண்டிய சொல்")
        submit = st.form_submit_button("தேடுக")

        if submit and word:
            meaning, src = get_precision_meaning(word)
            st.session_state.history.insert(
                0, {"word": word, "exp": meaning, "src": src}
            )

    for item in st.session_state.history:
        with st.expander(f"📖 {item['word']} ({item['src']})", expanded=True):
            st.write(item["exp"])

# ---------------- SIDEBAR ----------------
if st.sidebar.button("🧹 Clear History"):
    st.session_state.history = []
    st.rerun()
