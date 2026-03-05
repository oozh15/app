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
        font-size: 3.2rem;
        margin-bottom: 0;
    }}
    .card {{
        background: #fff;
        padding: 20px;
        border-left: 10px solid #800000;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
        margin-bottom: 20px;
    }}
    .label {{
        font-weight: bold;
        color: #1B5E20;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ---------------- API 1: WIKTIONARY ----------------
def search_wiktionary(word):
    url = "https://ta.wiktionary.org/w/api.php"
    params = {
        "action": "query", "format": "json", "titles": word,
        "prop": "extracts", "explaintext": True, "exintro": True
    }
    try:
        res = requests.get(url, params=params, timeout=5).json()
        pages = res.get("query", {}).get("pages", {})
        for pid, val in pages.items():
            if pid != "-1" and val.get("extract"):
                return val["extract"], "Wiktionary"
    except: pass
    return None, None

# ---------------- API 2: GLOSBE (FALLBACK) ----------------
def search_glosbe(word):
    # Using Glosbe to find meanings/translations
    url = f"https://glosbe.com/gapi/translate?from=ta&dest=en&format=json&phrase={word}&pretty=true"
    try:
        res = requests.get(url, timeout=5).json()
        if "tuc" in res:
            meanings = []
            for item in res["tuc"]:
                if "phrase" in item:
                    meanings.append(item["phrase"]["text"])
            if meanings:
                return " / ".join(meanings[:3]), "Glosbe Dictionary"
    except: pass
    return None, None

# ---------------- API 3: WIKIPEDIA (CONCEPT SEARCH) ----------------
wiki_ta = wikipediaapi.Wikipedia(user_agent="TamilLexicon/1.0", language="ta")

def search_wikipedia(word):
    page = wiki_ta.page(word)
    if page.exists():
        return page.summary[:600] + "...", "Tamil Wikipedia"
    return None, None

# ---------------- VOICE PRONUNCIATION (TTS) ----------------
def play_voice(word):
    tts = gTTS(text=word, lang='ta')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# ---------------- MAIN SEARCH LOGIC ----------------
def get_meaning(word):
    word = word.strip()
    
    # 1. Try Wiktionary
    meaning, src = search_wiktionary(word)
    if meaning: return meaning, src
    
    # 2. Try Glosbe
    meaning, src = search_glosbe(word)
    if meaning: return meaning, src
    
    # 3. Try Wikipedia
    meaning, src = search_wikipedia(word)
    if meaning: return meaning, src
    
    return None, None

# ---------------- OCR ENGINE ----------------
def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

# ---------------- UI LAYOUT ----------------
st.markdown("<h1 class='title'>நிகண்டு</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Digital Tamil Lexicon & OCR Explorer</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📜 ஆவண ஆய்வு (OCR)")
    file = st.file_uploader("Upload Image or PDF", type=["pdf", "png", "jpg", "jpeg"])
    if file:
        with st.spinner("Processing..."):
            if file.type == "application/pdf":
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(process_ocr(p.to_image(resolution=200).original) for p in pdf.pages)
            else:
                text = process_ocr(Image.open(file))
        st.text_area("Extracted Text:", text, height=300)
        st.info("Tip: Copy a word from here and paste it in the search box!")

with col2:
    st.subheader("🔍 சொற்பொருள் தேடல்")
    query = st.text_input("Enter a Tamil word:", placeholder="e.g., அக்கறை, அறம்")

    if query:
        meaning, source = get_meaning(query)
        
        if meaning:
            st.markdown(f"""
            <div class="card">
                <p style="font-size:0.8rem; color:grey;">Source: {source}</p>
                <h2 style="color:#800000; margin:0;">{query}</h2>
                <hr>
                <p><span class="label">பொருள் (Meaning):</span><br>{meaning}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Voice Button
            st.write("🔊 **Hear Pronunciation:**")
            audio_fp = play_voice(query)
            st.audio(audio_fp, format='audio/mp3')
            
        else:
            st.error("No direct meaning found. Trying similar suggestions...")
            # Fallback to simple Wikipedia search suggestions
            URL = "https://ta.wikipedia.org/w/api.php"
            params = {"action": "opensearch", "format": "json", "search": query, "limit": 3}
            suggestions = requests.get(URL, params=params).json()[1]
            if suggestions:
                st.write("Did you mean?")
                for s in suggestions:
                    if st.button(s):
                        st.session_state.query = s
                        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align:center; font-weight:bold; color:#800000;'>தமிழ் இனிது | ஆய்வகம் 2026</p>", unsafe_allow_html=True)
