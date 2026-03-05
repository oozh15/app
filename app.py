import streamlit as st
import pytesseract
from PIL import Image
import requests
import wikipediaapi
from gtts import gTTS
import io
from tamil_lemmatizer import TamilLemmatizer

# Initialize Tools
lemmatizer = TamilLemmatizer()
wiki = wikipediaapi.Wikipedia(
    user_agent="TamilLexiconApp/1.0 (contact: your-email@example.com)",
    language='ta'
)

## --- 1. SEARCH ENGINES ---

def search_wiktionary(word):
    url = f"https://ta.wiktionary.org/api/rest_v1/page/definition/{word}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            # Extracting the first available definition
            definition = data['ta'][0]['definitions'][0]['definition']
            return definition, "Wiktionary"
    except:
        pass
    return None, None

def search_glosbe(word):
    # Note: Glosbe API format can vary, using their translate endpoint
    url = f"https://glosbe.com/gapi/translate?from=ta&dest=en&format=json&phrase={word}&pretty=true"
    try:
        res = requests.get(url, timeout=5).json()
        if "tuc" in res:
            meanings = []
            for item in res["tuc"]:
                if "phrase" in item:
                    meanings.append(item["phrase"]["text"])
            if meanings:
                return ", ".join(meanings[:5]), "Glosbe Dictionary"
    except:
        pass
    return None, None

def search_wikipedia(word):
    page = wiki.page(word)
    if page.exists():
        return page.summary[:600] + "...", "Tamil Wikipedia"
    return None, None

def get_meaning(word):
    # Step 1: Wiktionary
    m, s = search_wiktionary(word)
    if m: return m, s
    
    # Step 2: Glosbe
    m, s = search_glosbe(word)
    if m: return m, s
    
    # Step 3: Wikipedia
    m, s = search_wikipedia(word)
    if m: return m, s
    
    return "Meaning not found in live sources.", None

## --- 2. VOICE FEATURE ---

def play_voice(word):
    tts = gTTS(text=word, lang='ta')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

## --- 3. STREAMLIT UI ---

st.title("🚀 Tamil AI Lexicon & OCR")

uploaded_file = st.file_uploader("Upload Tamil Document (Image)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    # OCR Extraction
    with st.spinner("Extracting Tamil Text..."):
        text = pytesseract.image_to_string(img, lang='tam')
    
    st.subheader("Extracted Text:")
    # Split text into clickable words
    words = text.split()
    
    # Display words as buttons for "Clickable Search"
    cols = st.columns(5) 
    for i, word in enumerate(words[:20]): # Limiting to 20 words for UI clarity
        if cols[i % 5].button(word):
            st.session_state['search_word'] = word

# Manual Search & Results
search_query = st.text_input("Or type a Tamil word:", key="manual_search")
final_word = st.session_state.get('search_word', search_query)

if final_word:
    st.divider()
    st.header(f"Results for: {final_word}")
    
    # Voice Button
    audio_data = play_voice(final_word)
    st.audio(audio_data, format='audio/mp3')
    
    # Meaning
    meaning, source = get_meaning(final_word)
    st.success(f"**Source:** {source}")
    st.write(f"**Meaning:** {meaning}")
    
    # Lemmatization (Root Word)
    root = lemmatizer.lemmatize(final_word)
    st.info(f"**Root Word Analysis:** {root}")
