import streamlit as st
import json
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import os

# --- CLASSY DESIGN SETTINGS ---
st.set_page_config(page_title="Tamil Lexicon Pro", page_icon="📜", layout="centered")

# Custom CSS for the "Old Classy" look
st.markdown("""
    <style>
    .main { background-color: #fdf6e3; color: #5d4037; font-family: 'Georgia', serif; }
    .stButton>button { 
        background-color: #8b5e3c; color: white; border-radius: 0px; 
        border: 2px solid #5d4037; padding: 10px 20px; font-weight: bold;
    }
    .meaning-card {
        background-color: #ffffff;
        padding: 15px;
        border-left: 8px solid #8b5e3c;
        border-top: 1px solid #d3c6b0;
        border-bottom: 1px solid #d3c6b0;
        border-right: 1px solid #d3c6b0;
        margin-bottom: 20px;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.05);
    }
    .word-title { color: #3e2723; font-size: 26px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- TRANSLATION LOGIC ---
def get_ai_meaning(word):
    """
    Steps 3 & 4: Tamil -> English -> Meaning in English -> Tamil
    """
    try:
        # Translate Tamil to English
        en_word = GoogleTranslator(source='ta', target='en').translate(word)
        
        # Get English definition context and translate back to Tamil
        context_query = f"Definition of the word {en_word}"
        ta_meaning = GoogleTranslator(source='en', target='ta').translate(context_query)
        
        return {"en": en_word, "ta": ta_meaning}
    except:
        return None

def main():
    st.title("📜 தமிழ் சொல் அகராதி")
    st.subheader("Tamil Word Extractor & Advanced Lexicon")
    st.write("---")

    # Load local JSON dictionary
    if os.path.exists('tamil.json'):
        with open('tamil.json', 'r', encoding='utf-8') as f:
            local_data = json.load(f)
    else:
        local_data = {}

    # Step 1: Document Upload
    uploaded_file = st.file_uploader("Upload Document Image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Document", use_container_width=True)

        if st.button("EXTRACT TAMIL WORDS"):
            with st.spinner("Analyzing text..."):
                # Extract Tamil Text
                extracted_text = pytesseract.image_to_string(img, lang='tam')
                # Clean up word list
                raw_words = list(set(extracted_text.split()))
                unique_words = [w.strip('.,!?;:()') for w in raw_words if len(w.strip()) > 1]

            if not unique_words:
                st.warning("No Tamil words detected. Try a clearer image.")
            else:
                st.success(f"Extracted {len(unique_words)} words.")
                
                for word in unique_words:
                    st.markdown(f"<div class='word-title'>சொல்: {word}</div>", unsafe_allow_html=True)
                    
                    # STEP 2: Local JSON check
                    if word in local_data:
                        st.success(f"**Found in Dictionary:** {local_data[word]}")
                    
                    # STEP 3 & 4: Translation Failover
                    else:
                        st.info("Searching Cloud Meaning...")
                        result = get_ai_meaning(word)
                        if result:
                            st.markdown(f"""
                            <div class='meaning-card'>
                                <b>English:</b> {result['en']}<br>
                                <b>விளக்கம் (Context):</b> {result['ta']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("Meaning could not be fetched.")
                    st.write("---")

if __name__ == "__main__":
    main()
