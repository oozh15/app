import streamlit as st
import json
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Tamil Lexicon Pro", page_icon="📚", layout="centered")

# --- CLASSY OLD STYLE DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #f4ece1; color: #4a3728; font-family: 'Georgia', serif; }
    .stButton>button { 
        background-color: #5d4037; 
        color: white; 
        border-radius: 2px; 
        border: 1px solid #3e2723;
        padding: 10px 24px;
    }
    .meaning-card {
        background-color: #ffffff;
        padding: 20px;
        border: 1px solid #d7ccc8;
        border-left: 10px solid #5d4037;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #3e2723; }
    </style>
    """, unsafe_allow_html=True)

# --- TRANSLATION LOGIC ---
def get_advanced_meaning(word):
    """
    Step 3 & 4: Tamil -> English -> Meaning -> Tamil 
    Using deep-translator for stability.
    """
    try:
        translator_to_en = GoogleTranslator(source='ta', target='en')
        translator_to_ta = GoogleTranslator(source='en', target='ta')
        
        # Tamil to English
        english_word = translator_to_en.translate(word)
        
        # English Meaning (Simulated via translation context)
        meaning_query = f"The meaning of the word {english_word} is"
        tamil_meaning = translator_to_ta.translate(meaning_query)
        
        return {
            "english": english_word,
            "tamil_desc": tamil_meaning
        }
    except Exception as e:
        return None

def main():
    st.title("📜 Tamil Word Meaning Finder")
    st.write("---")

    # Load Local JSON (Step 2)
    if os.path.exists('tamil.json'):
        with open('tamil.json', 'r', encoding='utf-8') as f:
            local_data = json.load(f)
    else:
        local_data = {}

    # File Upload (Step 1)
    uploaded_file = st.file_uploader("Upload Document (Image)", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Document Preview", width=400)

        if st.button("EXTRACT & FIND MEANINGS"):
            with st.spinner("Processing..."):
                # OCR Extraction
                extracted_text = pytesseract.image_to_string(img, lang='tam')
                # Clean and split words
                words = list(set([w.strip() for w in extracted_text.split() if len(w.strip()) > 1]))

            if not words:
                st.error("No Tamil words found. Please ensure the image is clear.")
            else:
                st.subheader(f"Found {len(words)} unique words:")
                
                for word in words:
                    st.markdown(f"### சொல் (Word): {word}")
                    
                    # 1. Check Local JSON
                    if word in local_data:
                        st.success(f"**Found in Dictionary:** {local_data[word]}")
                    
                    # 2. Advanced AI Translation Logic
                    else:
                        st.info("Searching AI Cloud...")
                        result = get_advanced_meaning(word)
                        if result:
                            st.markdown(f"""
                            <div class="meaning-card">
                                <b>English:</b> {result['english']}<br>
                                <b>விளக்கம் (Meaning):</b> {result['tamil_desc']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("Meaning not found in cloud.")
                    st.write("---")

if __name__ == "__main__":
    main()
