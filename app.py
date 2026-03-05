import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
import wikipediaapi
from gtts import gTTS
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="நிகண்டு | Digital Tamil Lexicon",
    layout="wide"
)

# ---------------- THEME & CSS ----------------
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
        font-size: 3rem;
        margin-bottom: 0;
    }}
    .card {{
        background: #fff;
        padding: 20px;
        border-left: 10px solid #800000;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
    }}
    .label {{
        font-weight: bold;
        color: #1B5E20;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ---------------- API 1: WIKTIONARY (ONE-LINE) ----------------
def search_wiktionary(word):
    url = "https://ta.wiktionary.org/w/api.php"
    params = {
        "action": "query", "format": "json", "titles": word,
        "prop": "extracts", "explaintext": True, "exintro": True
    }
    try:
        res = requests.get(url, params=params, timeout=3).json()
        pages = res.get("query", {}).get("pages", {})
        for pid, val in pages.items():
            if pid != "-1" and val.get("extract"):
                # Extract only the first sentence
                full_text = val["extract"].split('\n')[0]
                first_sentence = full_text.split('.')[0]
                return first_sentence + ".", "Wiktionary"
    except: pass
    return None, None

# ---------------- API 2: GLOSBE (SYNONYMS) ----------------
def search_glosbe(word):
    url = f"https://glosbe.com/gapi/translate?from=ta&dest=en&format=json&phrase={word}&pretty=true"
    try:
        res = requests.get(url, timeout=3).json()
        if "tuc" in res:
            synonyms = []
            for item in res["tuc"]:
                if "phrase" in item:
                    synonyms.append(item["phrase"]["text"])
            if synonyms:
                return ", ".join(synonyms[:3]), "Glosbe Synonyms"
    except: pass
    return None, None

# ---------------- API 3: WIKIPEDIA (FALLBACK) ----------------
wiki_ta = wikipediaapi.Wikipedia(user_agent="NiganduLexicon/1.0", language="ta")

def search_wikipedia(word):
    try:
        page = wiki_ta.page(word)
        if page.exists():
            # Trim to the first 150 characters for a clean look
            return page.summary[:150].split('.')[0] + ".", "Wikipedia"
    except: pass
    return None, None

# ---------------- MAIN SEARCH ENGINE ----------------
def get_meaning(word):
    word = word.strip()
    
    # Priority 1: Wiktionary (Definition)
    meaning, src = search_wiktionary(word)
    if meaning: return meaning, src
    
    # Priority 2: Glosbe (Short Synonyms)
    meaning, src = search_glosbe(word)
    if meaning: return meaning, src
    
    # Priority 3: Wikipedia (Short Summary)
    meaning, src = search_wikipedia(word)
    if meaning: return meaning, src
    
    return None, None

# ---------------- OCR & VOICE ----------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

def get_audio(word):
    tts = gTTS(text=word, lang='ta')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    return audio_io

# ---------------- UI LAYOUT ----------------
st.markdown("<h1 class='title'>நிகண்டு</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Simple & Fast Tamil Digital Lexicon</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📜 OCR Scanner")
    file = st.file_uploader("Upload Image/PDF", type=["pdf", "png", "jpg", "jpeg"])
    if file:
        with st.spinner("Scanning..."):
            if file.type == "application/pdf":
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(process_ocr(p.to_image(resolution=200).original) for p in pdf.pages)
            else:
                text = process_ocr(Image.open(file))
        st.text_area("Extracted Text:", text, height=250)

with col2:
    st.subheader("🔍 Quick Search")
    query = st.text_input("Enter Tamil word:", placeholder="e.g. முயற்சி")

    if query:
        meaning, source = get_meaning(query)
        
        if meaning:
            st.markdown(f"""
            <div class="card">
                <p style="font-size:0.75rem; color:grey; margin:0;">Source: {source}</p>
                <h2 style="color:#800000; margin:5px 0;">{query}</h2>
                <p><span class="label">One-line Meaning:</span><br>{meaning}</p>
            </div>
            """, unsafe_allow_html=True)
            
            audio = get_audio(query)
            st.audio(audio, format='audio/mp3')
        else:
            st.error("Meaning not found in live dictionaries.")

st.markdown("<p style='text-align:center; margin-top:50px; color:#800000; font-size:0.8rem;'>Madurai IT Lab | 2026</p>", unsafe_allow_html=True)
