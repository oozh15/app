import streamlit as st
import requests
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Lexicon Pro Decoder", page_icon="📘", layout="wide")

def get_word_data(word):
    """Fetch data from the Free Dictionary API dataset."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()[0]
            definition = data['meanings'][0]['definitions'][0]['definition']
            synonyms = data['meanings'][0].get('synonyms', [])
            antonyms = data['meanings'][0].get('antonyms', [])
            return {"def": definition, "syn": synonyms, "ant": antonyms}
    except:
        return None

# --- UI DESIGN ---
st.title("📘 Standard Lexicon Decoder")
st.markdown("### Upload a PDF or Image to decode complex terminology instantly.")

uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("Extracting text..."):
        text = ""
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                text += pytesseract.image_to_string(img)
        else:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)

    # UI Layout: Left for Text, Right for Definitions
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Extracted Text")
        st.text_area("Content", text, height=400)
    
    with col2:
        st.subheader("Word Decoder")
        word_to_search = st.text_input("Type a difficult word from the text:")
        
        if word_to_search:
            res = get_word_data(word_to_search.strip().lower())
            if res:
                st.markdown(f"**Meaning:**\n> {res['def']}")
                st.success(f"**Synonyms:** {', '.join(res['syn'][:5]) if res['syn'] else 'N/A'}")
                st.error(f"**Antonyms:** {', '.join(res['ant'][:5]) if res['ant'] else 'N/A'}")
                st.info(f"**Standard Explanation:**\nThis term is used to describe {res['def'].lower()}")
            else:
                st.warning("Word not found in the dataset.")
