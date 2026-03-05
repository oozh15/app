import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import requests
import wikipediaapi
from gtts import gTTS
import io
import google.generativeai as genai
from tamil_lemmatizer import TamilLemmatizer

# --- INITIALIZATION ---
lemmatizer = TamilLemmatizer()
wiki_ta = wikipediaapi.Wikipedia(
    user_agent="TamilLexiconApp/1.0",
    language='ta'
)

# Configure Gemini AI (Ensure GEMINI_API_KEY is in Streamlit Secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Please set GEMINI_API_KEY in Streamlit Secrets.")

# --- 1. SEARCH FUNCTIONS (THE PIPELINE) ---

def search_wiktionary(word):
    url = f"https://ta.wiktionary.org/api/rest_v1/page/definition/{word}"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return data['ta'][0]['definitions'][0]['definition'], "Wiktionary"
    except:
        return None, None

def search_glosbe(word):
    url = f"https://glosbe.com/gapi/translate?from=ta&dest=en&format=json&phrase={word}&pretty=true"
    try:
        res = requests.get(url, timeout=3).json()
        if "tuc" in res and "phrase" in res["tuc"][0]:
            return res["tuc"][0]["phrase"]["text"], "Glosbe Dictionary"
    except:
        return None, None

def get_ai_data(word):
    """Fallback for Definition, Context, and Synonyms"""
    prompt = (f"Provide details for the Tamil word '{word}': "
              "1. Simple Meaning, 2. A usage sentence, 3. Two synonyms. "
              "Format: Meaning|Sentence|Synonyms")
    try:
        response = ai_model.generate_content(prompt).text
        parts = response.split('|')
        return {
            "def": parts[0].strip() if len(parts) > 0 else "Not found",
            "sentence": parts[1].strip() if len(parts) > 1 else "No example available",
            "synonyms": parts[2].strip() if len(parts) > 2 else "None"
        }
    except:
        return {"def": "Error fetching AI data", "sentence": "", "synonyms": ""}

# --- 2. THE ORCHESTRATOR ---

def master_search(raw_word):
    # Step 1: Suffix Removal (Root word extraction)
    root = lemmatizer.lemmatize(raw_word)
    
    # Step 2 & 3: Wiktionary & Wikipedia
    meaning, source = search_wiktionary(root)
    
    if not meaning:
        page = wiki_ta.page(root)
        if page.exists():
            meaning, source = page.summary[:400] + "...", "Tamil Wikipedia"
            
    if not meaning:
        meaning, source = search_glosbe(root)

    # Step 4 & 5: Context & Synonyms (Always via AI for best quality)
    ai_extra = get_ai_data(root)
    
    if not meaning:
        meaning, source = ai_extra['def'], "AI Smart Search"
        
    return {
        "root": root,
        "meaning": meaning,
        "source": source,
        "sentence": ai_extra['sentence'],
        "synonyms": ai_extra['synonyms']
    }

# --- 3. STREAMLIT UI ---

st.set_page_config(page_title="Tamil AI Lexicon", layout="wide")
st.title("🏹 Smart Tamil AI Lexicon")
st.markdown("---")

# Layout Columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📸 OCR Scanner")
    uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Input Image", use_container_width=True)
        
        if st.button("Extract Text"):
            with st.spinner("Processing OCR..."):
                # Basic Preprocessing for Tesseract
                open_cv_image = np.array(img)
                gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray, lang='tam')
                st.session_state['extracted_text'] = text

    if 'extracted_text' in st.session_state:
        st.text_area("Extracted Text:", st.session_state['extracted_text'], height=150)
        st.info("Click a word above to search or type below.")

with col2:
    st.header("📖 Smart Dictionary")
    search_query = st.text_input("Enter Tamil word to search:")
    
    if search_query:
        with st.spinner(f"Analyzing {search_query}..."):
            result = master_search(search_query)
            
            # 1. Voice Output
            tts = gTTS(text=search_query, lang='ta')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')
            
            # 2. Results Cards
            st.success(f"**Root Word:** {result['root']}")
            
            with st.expander("📝 Definition & Source", expanded=True):
                st.write(result['meaning'])
                st.caption(f"Source: {result['source']}")
                
            with st.expander("💡 Usage Context"):
                st.write(f"*{result['sentence']}*")
                
            with st.expander("🔗 Synonyms"):
                st.code(result['synonyms'])

st.markdown("---")
st.caption("B.Tech IT Final Year Project - Built with Python & Gemini AI")
