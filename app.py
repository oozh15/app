import streamlit as st
import pytesseract
from PIL import Image
import pdfplumber
import requests
from bs4 import BeautifulSoup
import re
import io
from gtts import gTTS
from deep_translator import GoogleTranslator

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Tamil Doc Insights", page_icon="📜", layout="wide")

# ── ADAPTIVE CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;700&family=Inter:wght@400;600&display=swap');
    
    :root {
        --primary: #1e293b;
        --accent: #d97706;
        --bg: #f8fafc;
    }

    .stApp { background-color: var(--bg); font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: var(--primary);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        border-bottom: 4px solid var(--accent);
    }

    .doc-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        font-family: 'Noto Sans Tamil', sans-serif;
        font-size: 1.1rem;
        line-height: 1.8;
        max-height: 500px;
        overflow-y: auto;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    .meaning-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }

    .source-tag {
        font-size: 0.7rem;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 10px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ── LOGIC: SUFFIX & ROOT ENGINE ──────────────────────────────────────────────
SUFFIXES = ["படுத்தப்படும்", "செய்யப்பட்டது", "வைக்கப்படும்", "இல்லாமல்", "இருந்தால்", "பட்டிருக்கும்", "படுத்தல்", "இருக்கும்", "யிருந்து", "வைத்தல்", "கொண்டு", "விட்டது", "என்பது", "உடன்", "இல்", "இருந்து", "ஆகும்", "ஆனது", "என்று", "யுடன்", "படும்", "ஆல்", "ஆக", "ஆன", "கள்", "இல்", "கு", "ஐ"]

def get_clean_roots(word):
    forms = [word]
    temp = word
    for _ in range(3):
        for s in SUFFIXES:
            if temp.endswith(s) and len(temp) > len(s) + 1:
                temp = temp[:-len(s)]
                if temp not in forms: forms.append(temp)
                break
    return forms

# ── DATA FETCHING (THE FIXES) ────────────────────────────────────────────────
def fetch_meaning(word):
    results = []
    roots = get_clean_roots(word)
    
    # 1. Wiktionary Check
    for r_word in roots:
        try:
            api_url = f"https://ta.wiktionary.org/api/rest_v1/page/definition/{requests.utils.quote(r_word)}"
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for lang in data:
                    defs = data[lang][0].get("definitions", [])
                    if defs:
                        clean_def = re.sub('<[^<]+?>', '', defs[0]['definition'])
                        results.append({"text": clean_def, "src": "Wiktionary", "color": "#dbeafe", "txt_color": "#1e40af"})
                        break
                if results: break
        except: pass

    # 2. Agarathi Scrape (Updated Selectors)
    if not results:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            scrape_url = f"https://agarathi.com/word/{requests.utils.quote(word)}"
            page = requests.get(scrape_url, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "html.parser")
            # New potential tags for agarathi
            content = soup.find("div", class_="meaning") or soup.find("div", class_="description")
            if content:
                results.append({"text": content.get_text().strip(), "src": "Agarathi.com", "color": "#dcfce7", "txt_color": "#166534"})
        except: pass

    # 3. Translation Fallback (Guaranteed Result)
    try:
        translated = GoogleTranslator(source='ta', target='en').translate(word)
        results.append({"text": f"English Translation: {translated}", "src": "AI Translate", "color": "#fef3c7", "txt_color": "#92400e"})
    except: pass

    return results

# ── UI COMPONENTS ────────────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-header"><h1>📜 Tamil Doc Insights</h1><p>Professional Government Document Analysis & Translation</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.subheader("📂 Upload Document")
        file = st.file_uploader("Upload PDF or Image", type=['pdf', 'png', 'jpg', 'jpeg'], label_visibility="collapsed")
        
        extracted_text = ""
        if file:
            with st.spinner("Processing document..."):
                if file.type == "application/pdf":
                    with pdfplumber.open(file) as pdf:
                        extracted_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                else:
                    extracted_text = pytesseract.image_to_string(Image.open(file), lang='tam+eng')
            
            st.session_state['doc_text'] = extracted_text
        
        if 'doc_text' in st.session_state:
            st.markdown(f'<div class="doc-box">{st.session_state["doc_text"]}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔍 Intelligent Lookup")
        input_word = st.text_input("Type or paste a Tamil word:", placeholder="எ.கா. நிர்வாகம்")
        
        if not input_word and 'doc_text' in st.session_state:
            # Quick pick from text
            words = list(set(re.findall(r"[\u0B80-\u0BFF]+", st.session_state['doc_text'])))
            if words:
                input_word = st.selectbox("Or select from document:", ["Select a word..."] + sorted(words))

        if input_word and input_word != "Select a word...":
            meanings = fetch_meaning(input_word)
            
            st.markdown(f'<div class="meaning-card"><h3>{input_word}</h3>', unsafe_allow_html=True)
            for m in meanings:
                st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <span class="source-tag" style="background:{m['color']}; color:{m['txt_color']};">{m['src']}</span>
                        <p style="font-size: 0.95rem; color: #334155; border-left: 3px solid {m['txt_color']}; padding-left: 10px;">{m['text']}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Audio
            try:
                tts = gTTS(text=input_word, lang='ta')
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                st.audio(audio_data)
            except: st.error("Audio unavailable")
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
