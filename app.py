import streamlit as st
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
from deep_translator import GoogleTranslator
import requests

# --- Page Config ---
st.set_page_config(
    page_title="Tamil OCR + Meaning & Antonyms", 
    page_icon="📘",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stTextArea textarea {
        font-size: 18px !important;
        font-family: 'Latha', 'Arial Unicode MS', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- OCR Functions ---
def preprocess_for_tamil(img):
    """Enhance image quality for better Tesseract OCR accuracy."""
    img_array = np.array(img)
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Upscale image to help with small fonts
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Denoising
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    # Binarization using Otsu's thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_tamil_text(image):
    """Perform OCR on the image using Tamil language pack."""
    processed = preprocess_for_tamil(image)
    # psm 4: Assume a single column of text of variable sizes
    custom_config = r'--oem 3 --psm 4 -l tam'
    raw_text = pytesseract.image_to_string(processed, config=custom_config)
    # Clean common OCR artifacts
    clean_text = raw_text.replace('|','').replace('I','')
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    return clean_text.strip()

# --- Meaning & Antonyms Functions ---
def fetch_english_antonyms(word_en):
    """Fetch antonyms in English using Datamuse API."""
    if not word_en:
        return []
    url = f"https://api.datamuse.com/words?rel_ant={word_en.split()[0]}" # Use first word only
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [item['word'] for item in data[:5]] # Limit to top 5
    except:
        return []

def get_tamil_meaning(word_tam):
    """Translate Tamil word to English and back to get a clarified Tamil meaning."""
    try:
        # Step 1: Tamil to English
        meaning_en = GoogleTranslator(source='ta', target='en').translate(word_tam)
        # Step 2: English back to Tamil (to get synonyms/meanings)
        meaning_ta = GoogleTranslator(source='en', target='ta').translate(meaning_en)
        return meaning_en, meaning_ta
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def get_antonyms_tamil(meaning_en):
    """Get English antonyms and translate them back to Tamil."""
    if not meaning_en:
        return ["தகவல் இல்லை (No data found)"]
    
    antonyms_en = fetch_english_antonyms(meaning_en)
    if not antonyms_en:
        return ["எதிர்ச்சொல் கிடைக்கவில்லை (Antonyms not found)"]
    
    antonyms_ta = []
    translator = GoogleTranslator(source='en', target='ta')
    for ant in antonyms_en:
        try:
            ant_ta = translator.translate(ant)
            antonyms_ta.append(ant_ta)
        except:
            continue
    return list(set(antonyms_ta)) # Remove duplicates

# --- Sidebar Info ---
with st.sidebar:
    st.header("Settings & Help")
    st.info("""
    **Instructions:**
    1. Upload a clear image or PDF.
    2. Wait for OCR to finish.
    3. Copy any word from the output.
    4. Paste it into the search box below to find meanings.
    """)
    st.divider()
    st.caption("Powered by Tesseract OCR & Google Translate")

# --- UI Layout ---
st.title("📘 Tamil OCR & Word Explorer")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF or Image file", type=["pdf", "png", "jpg", "jpeg"])
    
    extracted_text = ""
    if uploaded_file:
        with st.spinner("🔍 Reading Tamil Text..."):
            try:
                if uploaded_file.type == "application/pdf":
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            img = page.to_image(resolution=300).original
                            extracted_text += extract_tamil_text(img) + "\n\n"
                else:
                    img = Image.open(uploaded_file)
                    extracted_text = extract_tamil_text(img)
                
                st.success("OCR Processing Complete!")
            except Exception as e:
                st.error(f"OCR Error: {e}")

    st.subheader("📄 Extracted Tamil Text")
    output_text = st.text_area("You can copy words from here:", extracted_text, height=450)

with col2:
    st.subheader("🔍 Word Explorer")
    st.write("Enter a word to find its definition and opposite.")
    
    word_input = st.text_input("Enter Tamil word (அறியாத சொல்):", placeholder="எ.கா. மகிழ்ச்சி")
    
    if word_input:
        with st.spinner("🔄 Searching..."):
            eng_equiv, tam_meaning = get_tamil_meaning(word_input)
            
            if eng_equiv:
                tam_antonyms = get_antonyms_tamil(eng_equiv)
                
                # Result Card
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    <h3 style="color: #2e7d32; margin-top: 0;">{word_input}</h3>
                    <p><b>பொருள் (Meaning):</b> {tam_meaning}</p>
                    <p><b>ஆங்கில நிகர் (English):</b> {eng_equiv.capitalize()}</p>
                    <hr>
                    <p><b>எதிர்ச்சொற்கள் (Antonyms):</b></p>
                    <p>{', '.join(tam_antonyms)}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Could not find data for this word.")

# --- Footer ---
st.markdown("---")
st.markdown("<center>Tamil OCR Tool v2.0</center>", unsafe_allow_html=True)
