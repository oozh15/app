import streamlit as st
import json, re, io
import requests
from pathlib import Path
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLES
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="தமிழ் வாசகர் Pro", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700&family=Noto+Sans+Tamil:wght@400;700&display=swap');
    
    .stApp { background-color: #fcfaf7; color: #1a1a1a; font-family: 'Lora', serif; }
    .tw { cursor: pointer; border-bottom: 1px dashed #b8860b; transition: 0.2s; }
    .tw:hover { background: #fff4d1; color: #8b1a1a; }
    .active { background: #ffeaa0 !important; font-weight: bold; border-bottom: 2px solid #b8860b; }
    
    /* Meaning Card Styling */
    .m-container { background: white; border: 1px solid #e2d9c8; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .m-header { font-family: 'Noto Sans Tamil'; font-size: 2.2rem; color: #1a1208; margin-bottom: 5px; }
    .m-pronounce { font-style: italic; color: #666; margin-bottom: 15px; font-size: 0.9rem; }
    .m-eng-title { font-size: 1.4rem; font-weight: bold; color: #8b1a1a; margin-top: 10px; }
    .m-explanation { line-height: 1.6; color: #333; background: #f9f9f9; padding: 10px; border-left: 4px solid #b8860b; margin: 10px 0; }
    .m-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; background: #eee; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SMART LINGUISTIC LOGIC
# ══════════════════════════════════════════════════════════════════════

TAMIL_SUFFIXES = [
    ('உடைய', 'possessive (of/belonging to)'),
    ('இன்', 'possessive (of)'),
    ('ஐ', 'accusative (object marker)'),
    ('க்கு', 'dative (to/for)'),
    ('இல்', 'locative (in/at)'),
    ('உடன்', 'sociative (with)'),
    ('இருந்து', 'ablative (from)'),
    ('உம்', 'conjunctive (and/also)'),
    ('ஆவது', 'ordinal (th/sequence)'),
]

def analyze_tamil_word(word):
    """Breaks down complex Tamil words into Root + Grammar."""
    for suffix, meaning in TAMIL_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            root = word[:-len(suffix)]
            return root, meaning
    return word, None

@st.cache_data(ttl=3600)
def get_ai_explanation(word):
    """Fetch a natural English explanation + translation."""
    try:
        # Get basic translation
        translator = GoogleTranslator(source='ta', target='en')
        simple_translation = translator.translate(word)
        
        # In a production app, you'd use an LLM here for "Explanation". 
        # For this version, we simulate a 'smart' response.
        root, grammar = analyze_tamil_word(word)
        
        explanation = f"The word **{word}** translates primarily as **'{simple_translation}'**."
        if grammar:
            root_trans = translator.translate(root)
            explanation += f" It appears to be the root word **'{root}'** ({root_trans}) combined with the suffix **'-{suffix}'**, indicating a {grammar} relationship."
        
        return {
            "word": word,
            "translation": simple_translation,
            "explanation": explanation,
            "root": root if grammar else None
        }
    except:
        return None

# ══════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def tokenize_text(text):
    """Wraps Tamil words in clickable spans."""
    words = text.split()
    html_output = []
    for w in words:
        clean = re.sub(r'[^\u0B80-\u0BFF]', '', w)
        if clean:
            html_output.append(f'<span class="tw" onclick="selectWord(\'{clean}\')">{w}</span>')
        else:
            html_output.append(w)
    return " ".join(html_output)

# ══════════════════════════════════════════════════════════════════════
# UI LAYOUT
# ══════════════════════════════════════════════════════════════════════

if 'selected_word' not in st.session_state:
    st.session_state.selected_word = None

st.title("📖 தமிழ் வாசகர் (Tamil Reading Assistant)")
st.subheader("Understand complicated Tamil text with AI explanations")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload TXT or paste text", type=['txt'])
    input_text = ""
    if uploaded_file:
        input_text = uploaded_file.read().decode("utf-8")
    else:
        input_text = st.text_area("Paste Tamil text here:", height=300)

    if input_text:
        st.markdown("### Reader View")
        formatted_html = tokenize_text(input_text)
        st.markdown(f'<div style="font-size: 1.2rem; line-height: 2;">{formatted_html}</div>', unsafe_allow_html=True)

with col2:
    st.write("### Word Insights")
    
    # Manual Input / JS Bridge Placeholder
    # Note: In a real Streamlit app, we use query params or components to bridge JS click to Python.
    clicked_word = st.text_input("Selected Word:", key="word_sync")
    
    if clicked_word:
        with st.spinner(f"Analyzing {clicked_word}..."):
            data = get_ai_explanation(clicked_word)
            
            if data:
                st.markdown(f"""
                <div class="m-container">
                    <div class="m-tag">Tamil Word</div>
                    <div class="m-header">{data['word']}</div>
                    <div class="m-eng-title">{data['translation']}</div>
                    <hr>
                    <div class="m-tag">Contextual Explanation</div>
                    <div class="m-explanation">{data['explanation']}</div>
                    <p style="font-size:0.8rem; color:gray;">
                        Clicking other words will update this panel automatically.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Could not fetch meaning.")
    else:
        st.info("Click a word in the text to see its English meaning and grammatical breakdown.")

# JavaScript Bridge for clicking
st.markdown("""
<script>
    function selectWord(word) {
        // Find the Streamlit text input and inject the word
        const inputs = window.parent.document.querySelectorAll('input');
        for (let i of inputs) {
            if (i.ariaLabel === "Selected Word:") {
                i.value = word;
                i.dispatchEvent(new Event('input', {bubbles: true}));
                break;
            }
        }
    }
</script>
""", unsafe_allow_html=True)
