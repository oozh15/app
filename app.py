import streamlit as st
import pytesseract
from PIL import Image
import requests
import re
import tamil.utf8 as utf8
import tamil.wordutils as wordutils
from tamil_lemmatizer import TamilLemmatizer
from gtts import gTTS
import io

# Initialize the Suffix/Stemming Engine
lemmatizer = TamilLemmatizer()

## --- 1. LINGUISTIC ENGINE (THE BRAIN) ---

def normalize_tamil_spelling(word):
    """
    Handles Variation Engine (Idea #4): Normalizes common spelling 
    confusions (ர/ற, ல/ள) to attempt multiple searches.
    """
    variations = [word]
    # Simple substitution rules for common spelling errors
    rules = {'ரை': 'றை', 'றை': 'ரை', 'ல': 'ள', 'ள': 'ல', 'ன': 'ந'}
    for mistake, fix in rules.items():
        if mistake in word:
            variations.append(word.replace(mistake, fix))
    return list(set(variations))

def remove_common_suffixes(word):
    """
    Suffix Removal Engine (Idea #1 & #2): 
    Strips common Tamil post-positions/suffixes.
    """
    suffixes = [
        'உடன்', 'இல்லாமல்', 'கள்', 'இல்', 'யுடன்', 
        'ஆல்', 'ஐ', 'கு', 'இருந்து', 'உடைய'
    ]
    stem = word
    for s in suffixes:
        if word.endswith(s):
            stem = word.rsplit(s, 1)[0]
            break
    return stem

## --- 2. MULTI-SOURCE ORCHESTRATOR ---

def get_meaning_extreme(word):
    """
    Flow: Normalization -> Suffix Removal -> Multi-source Search
    """
    # Step A: Remove Suffixes
    base_word = remove_common_suffixes(word)
    # Step B: Get Root via Lemmatizer
    root_word = lemmatizer.lemmatize(base_word)
    
    # Step C: Try all spelling variations
    search_terms = normalize_tamil_spelling(root_word)
    
    for term in search_terms:
        # 1. Search Wiktionary
        meaning, src = search_live_source(term, "wiktionary")
        if meaning: return meaning, src, term
        
        # 2. Search Glosbe
        meaning, src = search_live_source(term, "glosbe")
        if meaning: return meaning, src, term

    return None, None, root_word

def search_live_source(word, source_type):
    if source_type == "wiktionary":
        url = f"https://ta.wiktionary.org/api/rest_v1/page/definition/{word}"
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                data = res.json()
                return data['ta'][0]['definitions'][0]['definition'], "Wiktionary"
        except: pass
    
    elif source_type == "glosbe":
        url = f"https://glosbe.com/gapi/translate?from=ta&dest=en&format=json&phrase={word}"
        try:
            res = requests.get(url, timeout=2).json()
            if "tuc" in res and "phrase" in res["tuc"][0]:
                return res["tuc"][0]["phrase"]["text"], "Glosbe"
        except: pass
    
    return None, None

## --- 3. UI INTERFACE ---

st.set_page_config(page_title="Extreme Tamil Lexicon", layout="centered")
st.title("🔥 Extreme Tamil Linguistic Engine")
st.write("Professional Stemming | Suffix Removal | Multi-Source Search")

word_input = st.text_input("Enter Tamil word (e.g., அக்கறையுடன்):")



if word_input:
    with st.spinner("Processing Linguistic Pipeline..."):
        # Run the Engine
        meaning, source, final_root = get_meaning_extreme(word_input)
        
        if meaning:
            st.success(f"**Found Meaning for Root: {final_root}**")
            
            # Layout for output
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Definition:** {meaning}")
                st.caption(f"Source: {source}")
            with col2:
                # Pronunciation
                tts = gTTS(text=final_root, lang='ta')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3')
            
            # Idea #9: Sandhi/Character Pattern Matching
            st.divider()
            st.subheader("Analysis")
            st.write(f"Original Word: `{word_input}`")
            st.write(f"Detected Suffixes removed. Stemmed to: `{final_root}`")
            
        else:
            st.error(f"Could not find exact meaning for '{word_input}' or its root '{final_root}'.")
            st.info("Try checking the spelling or searching for a simpler form of the word.")
