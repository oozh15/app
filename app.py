import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
from deep_translator import GoogleTranslator

# ================= CONFIG =================
st.set_page_config(page_title="Tamil Lexical Analyzer", layout="wide")

JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# ================= DATASET =================
@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def normalize(word):
    return word.strip().replace("்", "")

# ================= CORE LOGIC =================
def analyze_word(word, context=""):
    word = normalize(word)
    dataset = load_dataset()

    # ---------- LEVEL 1: DATASET ----------
    for entry in dataset:
        db_word = normalize(entry.get("word", ""))
        if db_word == word or word in db_word or db_word in word:
            return (
                f"**ஆதாரம்:** Verified Dataset\n\n"
                f"**விளக்கம்:** {entry.get('meaning')}\n\n"
                f"**இணையான சொற்கள்:** {entry.get('synonym', 'இல்லை')}\n\n"
                f"**எதிர்ச்சொல்:** {entry.get('antonym', 'இல்லை')}"
            ), "Dataset"

    # ---------- LEVEL 2: AI BRIDGE ----------
    try:
        ta_en = GoogleTranslator(source="ta", target="en")
        en_ta = GoogleTranslator(source="en", target="ta")

        en_word = ta_en.translate(word).lower()

        meaning = en_ta.translate(en_word)

        # synonyms (Datamuse)
        syn_resp = requests.get(
            f"https://api.datamuse.com/words?rel_syn={en_word}&max=4",
            timeout=5
        ).json()

        syns = [en_ta.translate(i["word"]) for i in syn_resp] if syn_resp else []

        return (
            f"**ஆதாரம்:** செயற்கை நுண்ணறிவு (Lexical Bridge)\n\n"
            f"**விளக்கம்:** {meaning}\n\n"
            f"**இணையான சொற்கள்:** {', '.join(syns) if syns else 'இல்லை'}\n\n"
            f"**எதிர்ச்சொல்:** எதிர்ச்சொல் கிடைக்கவில்லை"
        ), "AI Bridge"

    except:
        return "❌ தகவல் கிடைக்கவில்லை", "Error"

# ================= OCR =================
def ocr_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return pytesseract.image_to_string(thresh, lang="tam")

# ================= UI =================
if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 ஆவணம்")
    file = st.file_uploader("Upload PDF / Image", type=["pdf", "png", "jpg"])

    ocr_text = ""
    if file:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    ocr_text += page.extract_text() or ""
        else:
            ocr_text = ocr_image(Image.open(file))

        st.text_area("OCR Text", ocr_text, height=400)

with col2:
    st.subheader("🔍 துல்லியமான ஆய்வு")
    word = st.text_input("தேட வேண்டிய சொல்")

    if st.button("ஆராய்க"):
        if word:
            result, src = analyze_word(word, ocr_text)
            st.session_state.history.insert(0, {
                "word": word,
                "result": result,
                "src": src
            })

    for h in st.session_state.history:
        with st.expander(f"📖 {h['word']} ({h['src']})", expanded=True):
            st.markdown(h["result"])

if st.sidebar.button("Reset"):
    st.session_state.history = []
    st.rerun()
