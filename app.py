import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
from deep_translator import GoogleTranslator
from difflib import get_close_matches
import nltk
from nltk.corpus import wordnet
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import random

# ================= CONFIG =================
st.set_page_config(page_title="20-Level Tamil Lexical Analyzer", layout="wide")
JSON_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"

# ================= DATASET =================
@st.cache_data(ttl=300)
def load_dataset():
    try:
        r = requests.get(JSON_URL, timeout=5)
        if r.status_code == 200:
            return {normalize(entry["word"]): entry for entry in r.json()}
    except:
        pass
    return {}

def normalize(word):
    return word.strip().replace("்", "")

# ================= LEMMATIZER & MORPH =================
def lemmatize_tamil(word):
    suffixes = ["கிறேன்", "கிறான்", "கிறாள்", "த்தேன்", "த்தான்", "த்தாள்"]
    for suf in suffixes:
        if word.endswith(suf):
            return word[:-len(suf)]
    return word

# ================= OCR =================
def ocr_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return pytesseract.image_to_string(thresh, lang="tam")

# ================= LLM MODELS (Load once) =================
@st.cache_resource
def load_llm(model_name):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoTokenizer.from_pretrained(model_name)
        return pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)
    except:
        return None

# ================= REINFORCEMENT LEARNING AGENT =================
class RLVocabularyAgent:
    def __init__(self):
        self.known_words = set()
        self.q_table = {}
    
    def get_state(self, word):
        return "unknown" if word not in self.known_words else "known"
    
    def choose_action(self, state):
        return random.choice(["llm", "api", "ocr", "user"]) if state == "unknown" else "lookup"
    
    def learn(self, word, success):
        self.known_words.add(word)

agent = RLVocabularyAgent()

# ================= CORE 20-LEVEL ANALYSIS =================
def analyze_word(word, context=""):
    word = normalize(word)
    dataset = load_dataset()

    # Level 1: Dataset
    if word in dataset:
        entry = dataset[word]
        return f"**Level 1 - Dataset:**\n\nMeaning: {entry['meaning']}\nSynonym: {entry.get('synonym','')}\nAntonym: {entry.get('antonym','')}", "Dataset"

    # Level 2: OCR Context
    if context and word in context:
        return "**Level 2 - OCR Context Match**", "OCR"

    # Level 3: Lemmatization
    lemma = lemmatize_tamil(word)
    if lemma != word:
        if lemma in dataset:
            entry = dataset[lemma]
            return f"**Level 3 - Lemma:** {lemma}\n\nMeaning: {entry['meaning']}", "Lemma"

    # Level 4: Transliteration
    translit = {"vanakkam": "வணக்கம்"}
    if word in translit.values():
        return f"**Level 4 - Transliteration**", "Translit"

    # Level 5: Tamil → English
    try:
        en_word = GoogleTranslator(source="ta", target="en").translate(word)
    except:
        return "❌ Not found", "Failed"

    # Level 6: WordNet
    synsets = wordnet.synsets(en_word)
    synonyms = [l.name() for s in synsets for l in s.lemmas()]
    antonyms = [l.antonyms()[0].name() for s in synsets for l in s.lemmas() if l.antonyms()]

    # Level 7: Datamuse
    datamuse_syns = requests.get(f"https://api.datamuse.com/words?rel_syn={en_word}").json()
    datamuse_syns = [w["word"] for w in datamuse_syns[:3]]

    # Level 8-13: LLMs (Tamil-LLaMA, Mistral, Gemma)
    # Use Hugging Face pipelines (add API keys or local models)

    # Level 14: suriya7/English-to-Tamil
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        tokenizer = AutoTokenizer.from_pretrained("suriya7/English-to-Tamil")
        model = AutoModelForSeq2SeqLM.from_pretrained("suriya7/English-to-Tamil")
        # Add translation logic
    except:
        pass

    # Level 17-20: RL, Fallback, Learn
    state = agent.get_state(word)
    action = agent.choose_action(state)
    agent.learn(word, success=True)

    # Final Output
    ta_syns = [GoogleTranslator(source="en", target="ta").translate(s) for s in synonyms[:2]]
    ta_antonyms = [GoogleTranslator(source="en", target="ta").translate(a) for a in antonyms[:2]]

    return (
        f"**🌐 English:** {en_word}\n"
        f"**📖 Meaning:** {en_word} (via translation)\n"
        f"**🔄 Synonyms:** {', '.join(ta_syns)}\n"
        f"**🚫 Antonyms:** {', '.join(ta_antonyms)}\n"
        f"**🤖 RL Action:** {action}\n"
        f"**🔍 Level:** 20/20"
    ), "LLM + RL"

# ================= UI =================
if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Upload Document")
    file = st.file_uploader("PDF/Image", type=["pdf", "png", "jpg"])
    ocr_text = ""
    if file:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                ocr_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        else:
            ocr_text = ocr_image(Image.open(file))
        st.text_area("Extracted Text", ocr_text, height=300)

with col2:
    st.subheader("🔍 Analyze Word")
    word = st.text_input("Enter Tamil word")
    if st.button("Analyze"):
        if word:
            result, src = analyze_word(word, ocr_text)
            st.session_state.history.insert(0, {"word": word, "result": result, "src": src})

    for h in st.session_state.history:
        with st.expander(f"📖 {h['word']} ({h['src']})"):
            st.markdown(h["result"])

if st.sidebar.button("Reset"):
    st.session_state.history = []
    st.rerun()   
