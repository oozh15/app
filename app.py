import streamlit as st
import requests
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
from tamil_lemmatizer import TamilLemmatizer
from gtts import gTTS
import io

# Initialize Lemmatizer
# Note: This might take a moment to load on the server
@st.cache_resource
def load_lemmatizer():
    return TamilLemmatizer()

lemmatizer = load_lemmatizer()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="நிகண்டு | Expert Tamil Lexicon", layout="wide")

# ---------------- THEME ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pavanam&display=swap');
    .stApp { background-color: #FDF5E6; font-family: 'Pavanam', sans-serif; }
    .title { text-align: center; color: #800000; font-size: 2.8rem; font-weight: bold; }
    .card { background: white; padding: 15px; border-left: 8px solid #800000; border-radius: 5px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .source-label { font-size: 0.7rem; color: #7f8c8d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- API SEARCH LOGIC ----------------

def search_tamil_dict(word):
    meanings = []
    
    # Pre-processing: Get the root word (Lemma)
    try:
        # Some versions of lemmatizer use .lemmatize(), some use .get_lemma()
        # We use a try-except to handle variations
        root = lemmatizer.lemmatize(word)
    except:
        root = word

    # 1. Tamil Wiktionary (Tamil to Tamil)
    wiki_url = "https://ta.wiktionary.org/w/api.php"
    params = {
        "action": "query", "format": "json", "titles": root,
        "prop": "extracts", "explaintext": True, "exintro": True
    }
    try:
        res = requests.get(wiki_url, params=params, timeout=5).json()
        pages = res.get("query", {}).get("pages", {})
        for pid, val in pages.items():
            if pid != "-1" and val.get("extract"):
                clean_text = val["extract"].split('\n')[0].split('.')[0]
                meanings.append({"text": clean_text + ".", "src": "விக்சனரி (Wiktionary)"})
    except: pass

    # 2. Glosbe Tamil-Tamil (Synonyms)
    glosbe_url = f"https://glosbe.com/gapi/translate?from=ta&dest=ta&format=json&phrase={root}"
    try:
        res = requests.get(glosbe_url, timeout=5).json()
        if "tuc" in res:
            syns = [item["phrase"]["text"] for item in res["tuc"] if "phrase" in item]
            if syns:
                meanings.append({"text": ", ".join(syns[:5]), "src": "பொருள் விளக்கம் (Synonyms)"})
    except: pass

    return meanings[:5], root

# ---------------- OCR ENGINE ----------------

def process_ocr(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Tesseract configuration for Tamil + English
    config = r"--oem 3 --psm 6 -l tam+eng"
    return pytesseract.image_to_string(gray, config=config)

# ---------------- UI LAYOUT ----------------

st.markdown("<h1 class='title'>நிகண்டு</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Expert Tamil Digital Lexicon</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

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
        st.text_area("Extracted Text:", text, height=300)

with col2:
    st.subheader("🔍 Smart Dictionary")
    query = st.text_input("Enter Tamil word:", key="tamil_input")

    if query:
        with st.spinner("Searching dictionaries..."):
            results, root = search_tamil_dict(query)
        
        if results:
            st.write(f"**தேடப்பட்ட சொல்:** {query} | **வேர்ச்சொல்:** {root}")
            for r in results:
                st.markdown(f"""
                <div class="card">
                    <span class="source-label">ஆதாரம்: {r['src']}</span>
                    <p style="font-size:1.1rem; color:#3E2723; margin-top:5px;">{r['text']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Text-to-Speech
            tts = gTTS(text=query, lang='ta')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            st.audio(audio_io, format='audio/mp3')
        else:
            st.warning("மன்னிக்கவும்! இதற்கான தமிழ் பொருள் கிடைக்கவில்லை.")

st.markdown("---")
st.markdown("<p style='text-align:center; color:#800000; font-weight:bold;'>தமிழ் இனிது | 2026</p>", unsafe_allow_html=True)
