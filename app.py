import streamlit as st
import requests
import json

# --- Dictionary Function ---
@st.cache_data
def load_dictionary(url):
    try:
        response = requests.get(url)
        return response.json()
    except:
        return {}

def lookup_word(word, dictionary_data):
    # This assumes your JSON is a list of dicts like: [{"word": "...", "meaning": "..."}]
    # Adjust the keys ('word', 'meaning') based on your actual JSON structure
    for entry in dictionary_data:
        if entry.get('word') == word:
            return entry.get('meaning')
    return None

# --- Load the Data ---
DICT_URL = "https://raw.githubusercontent.com/oozh15/app/main/tamil.json"
dictionary = load_dictionary(DICT_URL)

# --- UI for Lookup (Add this after the OCR result) ---
st.divider()
st.subheader("🔍 Tough Word Lookup")
st.info("Copy a tough word from the text above and paste it here to see the meaning.")

col1, col2 = st.columns([1, 2])

with col1:
    search_query = st.text_input("Enter Tamil Word:")

with col2:
    if search_query:
        meaning = lookup_word(search_query, dictionary)
        if meaning:
            st.success(f"**Meaning:** {meaning}")
        else:
            st.warning("Word not found in the custom dictionary.")

# Optional: Show all available words in a dropdown for easy selection
if dictionary:
    with st.expander("📚 View all words in Dictionary"):
        all_words = [item.get('word') for item in dictionary if item.get('word')]
        selected = st.selectbox("Select a word to see meaning:", [""] + all_words)
        if selected:
            st.write(f"**{selected}:** {lookup_word(selected, dictionary)}")
