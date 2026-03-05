import streamlit as st
from tamil_lemmatizer import TamilLemmatizer
import tamil.utf8 as utf8
import requests

# 1. Initialize Lemmatizer for Suffix Removal
lemmatizer = TamilLemmatizer()

def smart_tamil_pipeline(word):
    # --- STEP 1: Suffix Removal & Lemmatization ---
    # This turns "சென்றார்கள்" into "செல்"
    root_word = lemmatizer.lemmatize(word)
    
    # --- STEP 2: Compound Splitting (Open-Tamil) ---
    # Attempt to split if it's a long word
    letters = utf8.get_letters(root_word)
    if len(letters) > 5:
        # Note: Open-Tamil provides basic utilities; 
        # for deep splitting, we treat the root as the primary search term
        pass

    # --- STEP 3: Search Hierarchy ---
    # Start with the cleaned root_word
    st.write(f"🔍 Analyzing Root: **{root_word}**")
    
    # Check Wiktionary
    meaning, src = search_wiktionary(root_word)
    if not meaning:
        # Check Glosbe (Free API)
        meaning, src = search_glosbe(root_word)
    
    if not meaning:
        # STEP 4: Literature Context (Wikipedia)
        meaning, src = search_wikipedia(root_word)
        
    if not meaning:
        # STEP 5: AI Explanation (Final Fallback)
        meaning, src = get_ai_explanation(root_word)
        
    return root_word, meaning, src

# Add this to your Streamlit UI
user_input = st.text_input("Enter Tamil word:")
if user_input:
    root, mean, source = smart_tamil_pipeline(user_input)
    st.success(f"**Root Word:** {root}")
    st.info(f"**Meaning:** {mean}")
    st.caption(f"Source: {source}")
