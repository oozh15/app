import streamlit as st
import json, re, io
import fitz  # PyMuPDF
from docx import Document
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════════════
# 1. TN GOVT THEME & UI STYLING
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="தமிழ்நாடு அரசு - வாசகர் உதவி", page_icon="🏛️", layout="wide")

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;700&family=Lora:wght@400;700&display=swap');

    /* TN Govt Color Palette */
    :root {
        --tn-maroon: #8b1a1a;
        --tn-gold: #b8860b;
        --tn-beige: #fdfaf5;
        --tn-dark: #1a1208;
    }

    .stApp { background-color: var(--tn-beige); font-family: 'Lora', serif; }

    /* Header Styling */
    .gov-header {
        background-color: white;
        padding: 15px 30px;
        border-bottom: 4px solid var(--tn-maroon);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .gov-logo-text { color: var(--tn-maroon); font-family: 'Noto Sans Tamil', sans-serif; font-weight: bold; font-size: 1.5rem; }
    
    /* Document Display Area */
    .reader-box {
        background: white;
        padding: 40px;
        border: 1px solid #e2d9c8;
        border-radius: 8px;
        height: 70vh;
        overflow-y: scroll;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.02);
    }

    /* Word Interaction */
    .tw {
        cursor: pointer;
        border-bottom: 1px solid var(--tn-gold);
        transition: 0.2s;
        padding: 0 2px;
        display: inline-block;
    }
    .tw:hover { background: #fff4d1; color: var(--tn-maroon); font-weight: bold; }

    /* Meaning Panel */
    .meaning-card {
        background: white;
        border-top: 5px solid var(--tn-maroon);
        padding: 20px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        position: sticky;
        top: 20px;
    }
    
    .suffix-tag {
        background: #eef2f3;
        color: #333;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        border: 1px solid #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 2. FILE EXTRACTION ENGINE
# ══════════════════════════════════════════════════════════════════════
def extract_text_from_file(uploaded_file):
    fname = uploaded_file.name.lower()
    content = ""
    try:
        if fname.endswith('.pdf'):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc: content += page.get_text()
        elif fname.endswith('.docx'):
            doc = Document(io.BytesIO(uploaded_file.read()))
            content = "\n".join([para.text for para in doc.paragraphs])
        else: # txt
            content = uploaded_file.read().decode("utf-8")
        return content
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

# ══════════════════════════════════════════════════════════════════════
# 3. LINGUISTIC ENGINE (SUFFIX ANALYSIS)
# ══════════════════════════════════════════════════════════════════════
TAMIL_GRAMMAR = {
    'உடைய': 'Possessive: Indicates belonging (e.g., "His/Her")',
    'க்கு': 'Dative: Indicates direction or recipient (e.g., "To/For")',
    'இல்': 'Locative: Indicates location (e.g., "In/At/On")',
    'ஐ': 'Accusative: Identifies the object of an action',
    'உம்': 'Conjunction: Meaning "And" or "Also"',
    'இருந்து': 'Ablative: Meaning "From" a place or time',
    'ஆல்': 'Instrumental: Meaning "By" or "With" something'
}

def smart_lookup(word):
    word = re.sub(r'[^\u0B80-\u0BFF]', '', word) # Clean punctuation
    if not word: return None
    
    translator = GoogleTranslator(source='ta', target='en')
    base_trans = translator.translate(word)
    
    analysis = {"original": word, "meaning": base_trans, "suffix_note": ""}
    
    # Check for complicated suffixes
    for suffix, desc in TAMIL_GRAMMAR.items():
        if word.endswith(suffix) and len(word) > len(suffix):
            root = word[:-len(suffix)]
            root_trans = translator.translate(root)
            analysis["suffix_note"] = f"This word is built from the root <b>'{root}'</b> ({root_trans}) + suffix <b>'-{suffix}'</b> ({desc})."
            break
            
    return analysis

# ══════════════════════════════════════════════════════════════════════
# 4. MAIN INTERFACE
# ══════════════════════════════════════════════════════════════════════
apply_custom_styles()

# Gov Header
st.markdown("""
<div class="gov-header">
    <div style="display: flex; align-items: center;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Tamil_Nadu_State_Emblem.svg/1200px-Tamil_Nadu_State_Emblem.svg.png" width="60" style="margin-right:20px;">
        <div>
            <div class="gov-logo-text">தமிழ்நாடு அரசு</div>
            <div style="font-size: 0.8rem; letter-spacing: 1px; color: #555;">GOVERNMENT OF TAMIL NADU</div>
        </div>
    </div>
    <div style="text-align: right; color: var(--tn-maroon); font-weight: bold;">
        Digital Translation & Reading Assistant<br>
        <span style="font-size: 0.7rem; color: #666;">Official Reading Tool v2.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_main, col_side = st.columns([7, 3])

with col_main:
    uploaded = st.file_uploader("Upload Official Document (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
    
    if uploaded:
        raw_text = extract_text_from_file(uploaded)
        if raw_text:
            # Tokenize for clicking
            words = raw_text.split()
            html_content = ""
            for w in words:
                clean = re.sub(r'[^\u0B80-\u0BFF]', '', w)
                if clean:
                    html_content += f'<span class="tw" onclick="window.parent.postMessage({{"type": "streamlit:setComponentValue", "value": "{clean}"}}, \'*\')">{w}</span> '
                else:
                    html_content += f'{w} '
            
            st.markdown(f'<div class="reader-box">{html_content}</div>', unsafe_allow_html=True)
            st.info("💡 Click any Tamil word above to see the official English breakdown.")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 100px; color: #999;">
            <div style="font-size: 4rem;">📂</div>
            <h3>Please upload a document to begin.</h3>
            <p>Supported formats: Government Orders (PDF), Letters (DOCX), or Plain Text.</p>
        </div>
        """, unsafe_allow_html=True)

with col_side:
    # This hidden input captures the JS click
    clicked_word = st.text_input("Selected Word Analyzer", key="word_sync", help="Click a word in the reader to analyze")
    
    if clicked_word:
        with st.spinner("Analyzing linguistic structure..."):
            result = smart_lookup(clicked_word)
            if result:
                st.markdown(f"""
                <div class="meaning-card">
                    <div style="font-size: 0.8rem; color: var(--tn-gold); font-weight: bold;">WORD ANALYSIS</div>
                    <h2 style="color: var(--tn-maroon); margin-bottom: 0;">{result['original']}</h2>
                    <hr>
                    <div style="font-size: 1.3rem; color: #333; margin-bottom: 15px;">
                        <b>English:</b> {result['meaning']}
                    </div>
                    {f'<div style="background: #fdf5e6; padding: 10px; border-radius: 4px; border-left: 3px solid var(--tn-gold); font-size: 0.9rem;">{result["suffix_note"]}</div>' if result['suffix_note'] else ""}
                    <br>
                    <div style="font-size: 0.75rem; color: #888; font-style: italic;">
                        Generated using TN Smart-Reader Engine
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="border: 2px dashed #ccc; padding: 20px; text-align: center; color: #888;">
            Analysis will appear here after word selection.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 5. JAVASCRIPT BRIDGE (FOR INTERACTIVITY)
# ══════════════════════════════════════════════════════════════════════
# This allows the Python script to hear the "clicks" from the HTML area
st.components.v1.html("""
<script>
    const observer = new MutationObserver(() => {
        const words = window.parent.document.querySelectorAll('.tw');
        words.forEach(word => {
            word.onclick = function() {
                const targetInput = window.parent.document.querySelector('input[aria-label="Selected Word Analyzer"]');
                if (targetInput) {
                    targetInput.value = this.innerText;
                    targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                }
            };
        });
    });
    observer.observe(window.parent.document.body, {childList: true, subtree: true});
</script>
""", height=0)
