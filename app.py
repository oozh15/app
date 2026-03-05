import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
import wikipediaapi

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="நிகண்டு | Digital Tamil Lexicon",
    layout="wide"
)

# ---------------- THEME ----------------
def apply_theme():
    bg = "https://www.transparenttextures.com/patterns/papyrus.png"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pavanam&family=Arima+Madurai:wght@700&display=swap');
    .stApp {{
        background-image: url("{bg}");
        background-color: #F7E7CE;
        font-family: 'Pavanam', sans-serif;
        color: #3E2723;
    }}
    .title {{
        font-family: 'Arima Madurai', cursive;
        text-align: center;
        color: #800000;
        font-size: 3.2rem;
    }}
    .card {{
        background: #fff;
        padding: 18px;
        border-left: 8px solid #800000;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
        border-radius: 6px;
        margin-bottom: 20px;
    }}
    .label {{
        font-weight: bold;
        color: #1B5E20;
    }}
    .suggestion-box {{
        background-color: #FFF3E0;
        padding: 10px;
        border-radius: 5px;
        border: 1px dashed #E65100;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ---------------- OCR ENGINE ----------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

# ---------------- ROOT NORMALIZATION ----------------
def normalize_word(word):
    suffixes = ["இல்", "இன்", "ஆல்", "உடன்", "க்கு", "கள்", "து", "தை", "ன்", "யை", "இய", "ஆ"]
    for suf in suffixes:
        if word.endswith(suf) and len(word) > len(suf) + 1:
            return word[:-len(suf)]
    return word

# ---------------- API SEARCH FUNCTIONS ----------------

def search_wiktionary(word):
    """Real-time Dictionary Search via Wiktionary API"""
    URL = "https://ta.wiktionary.org/w/api.php"
    params = {
        "action": "query", "format": "json", "titles": word,
        "prop": "extracts", "explaintext": True, "exintro": True
    }
    try:
        res = requests.get(URL, params=params, timeout=5).json()
        pages = res.get("query", {}).get("pages", {})
        for pid, val in pages.items():
            if pid != "-1" and val.get("extract"):
                return val["extract"], "Live Wiktionary"
    except: pass
    return None, None

def get_suggestions(word):
    """Search for similar words if direct meaning is not found"""
    URL = "https://ta.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch", "format": "json", "search": word, "limit": 5
    }
    try:
        res = requests.get(URL, params=params, timeout=5).json()
        return res[1] # Returns list of similar titles
    except: return []

# ---------------- MAIN LOGIC ----------------
def get_meaning(word):
    word = word.strip()
    root = normalize_word(word)

    # 1. Exact Wiktionary Match
    meaning, src = search_wiktionary(word)
    if meaning: return meaning, src

    # 2. Root Word Wiktionary Match
    if root != word:
        meaning, src = search_wiktionary(root)
        if meaning: return meaning, f"Wiktionary (Root: {root})"

    return None, None

# ---------------- UI LAYOUT ----------------
st.markdown("<h1 class='title'>நிகண்டு</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📜 ஆவண ஆய்வு (OCR)")
    file = st.file_uploader("Upload Image/PDF", type=["pdf", "png", "jpg", "jpeg"])
    if file:
        with st.spinner("எழுத்துக்களைப் பிரித்தெடுக்கிறது..."):
            if file.type == "application/pdf":
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(process_ocr(p.to_image(resolution=200).original) for p in pdf.pages)
            else:
                text = process_ocr(Image.open(file))
        st.text_area("கண்டறியப்பட்ட உரை:", text, height=250)

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    query = st.text_input("ஒரு தமிழ் சொல்லை உள்ளிடவும்", placeholder="எ.கா: அறம், கணினி")

    if query:
        meaning, source = get_meaning(query)
        
        if meaning:
            st.markdown(f"""
            <div class="card">
                <p style="font-size:0.8rem; color:grey;">ஆதாரம்: {source}</p>
                <h2 style="color:#800000; margin-top:0;">{query}</h2>
                <hr>
                <p><span class="label">பொருள்:</span><br>{meaning}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("இந்த சொல்லிற்கான நேரடிப் பொருள் கிடைக்கவில்லை.")
            
            # Suggestion Logic
            suggestions = get_suggestions(query)
            if suggestions:
                st.info("நீங்கள் இவற்றைத் தேடுகிறீர்களா?")
                cols = st.columns(len(suggestions))
                for i, sug in enumerate(suggestions):
                    if cols[i].button(sug):
                        # Re-run search with the suggested word
                        st.session_state.query = sug
                        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align:center; font-weight:bold; color:#800000;'>தமிழ் இனிது | ஆய்வகம் 2026</p>", unsafe_allow_html=True)
