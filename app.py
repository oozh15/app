import streamlit as st
import json, re, io, time
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
from docx import Document
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & THEME
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="தமிழ்நாடு அரசு | Tamil Language Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Shared Styles for TN Govt Aesthetic
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@300;400;700&family=Noto+Serif+Tamil:wght@400;700&family=Source+Serif+4:wght@400;600&display=swap');

:root {
  --tn-navy: #003366; --tn-saffron: #e07b00; --tn-red: #8b1a1a;
  --tn-offwhite: #f5f7fa; --tn-border: #c5cdd8;
}

.stApp { background: var(--tn-offwhite); font-family: 'Source Serif 4', serif; }

/* Header & Banner */
.gov-header {
  background: var(--tn-navy); border-bottom: 4px solid var(--tn-saffron);
  padding: 15px 30px; display: flex; align-items: center; justify-content: space-between;
}
.gov-title { color: white; font-family: 'Noto Serif Tamil'; font-size: 1.5rem; font-weight: 700; }

/* Reader Styles */
.reader-box {
  background: white; border: 1px solid var(--tn-border); padding: 25px;
  height: 60vh; overflow-y: auto; border-radius: 4px; line-height: 2.2;
}
.tw {
  cursor: pointer; border-bottom: 2px solid var(--tn-saffron); padding: 0 2px;
}
.tw:hover { background: #fff3cc; color: var(--tn-navy); }

/* Meaning Card */
.mcard {
  background: white; border: 1px solid var(--tn-border); border-top: 5px solid var(--tn-red);
  padding: 20px; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.mcard-ta { background: #eaf5ee; border: 1px solid #b8ddc4; padding: 10px; margin: 10px 0; border-radius: 4px; }

/* Ticker */
.tn-ticker {
  background: var(--tn-saffron); color: white; padding: 5px 20px; font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 2. DATASETS & LINGUISTICS
# ══════════════════════════════════════════════════════════════════════

# Tier 2: Official Local Glossary
OFFICIAL_GLOSSARY = {
    "அங்கீகாரம்": {"en": "Approval / Recognition", "govt": "அதிகாரப்பூர்வ ஒப்புதல்", "simple": "அதிகாரிகள் ஒப்புதல் கொடுப்பது", "form": "Used in certificate verification"},
    "நிர்வாகம்": {"en": "Administration", "govt": "ஆட்சிப்பணி / மேலாண்மை", "simple": "அரசு வேலைகளை நடத்துவது", "form": "Found in dept headers"},
    "ஒப்பந்தம்": {"en": "Contract / Agreement", "govt": "உடன்படிக்கை", "simple": "இரு தரப்பு உறுதிமொழி", "form": "Standard Lease/Tender docs"},
    "ஆணை": {"en": "Order", "govt": "அரசாணை (G.O)", "simple": "அரசு வெளியிடும் உத்தரவு", "form": "G.O. Number section"},
    "விண்ணப்பம்": {"en": "Application", "govt": "முறையீடு / மனு", "simple": "உதவி கோரி எழுதும் கடிதம்", "form": "Front page of any form"},
}

def correct_spelling(word):
    # Simple cleaner
    return re.sub(r'[^\u0B80-\u0BFF]', '', word).strip()

def smart_lookup(word):
    word = correct_spelling(word)
    if not word: return None

    # Tier 2: Internal Glossary
    if word in OFFICIAL_GLOSSARY:
        base = OFFICIAL_GLOSSARY[word]
        base['tier'] = "Tier 2: Official Glossary"
    else:
        # Tier 3: Online Translation Fallback
        try:
            en = GoogleTranslator(source='ta', target='en').translate(word)
            base = {"en": en, "govt": "N/A", "simple": "General translation", "form": "N/A", "tier": "Tier 3: Online AI"}
        except:
            return None

    # Update Audit Log
    if 'audit_log' not in st.session_state: st.session_state.audit_log = []
    st.session_state.audit_log.append({"time": datetime.now().strftime("%H:%M"), "word": word})
    
    return base

# ══════════════════════════════════════════════════════════════════════
# 3. FILE EXTRACTION ENGINE
# ══════════════════════════════════════════════════════════════════════

def extract_text(file):
    name = file.name.lower()
    if name.endswith('.pdf'):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([p.get_text() for p in doc])
    elif name.endswith('.docx'):
        doc = Document(io.BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])
    return file.read().decode("utf-8")

# ══════════════════════════════════════════════════════════════════════
# 4. MAIN INTERFACE
# ══════════════════════════════════════════════════════════════════════

# Official Header
st.markdown("""
<div class="gov-header">
    <div style="display: flex; align-items: center;">
        <div style="background:white; border-radius:50%; width:60px; height:60px; display:flex; align-items:center; justify-content:center; margin-right:15px;">🏛️</div>
        <div>
            <div class="gov-title">தமிழ்நாடு அரசு - தமிழ் உதவியாளர்</div>
            <div style="color: #aabbd4; font-size: 0.8rem;">GOVERNMENT OF TAMIL NADU • DIGITAL SERVICE</div>
        </div>
    </div>
    <div style="text-align: right; color: white; font-size: 0.8rem;">
        Official Release v3.0<br>Secure Reading Portal
    </div>
</div>
<div class="tn-ticker">📢 அறிவிப்பு: தமிழ் சொற்களை கிளிக் செய்து அரசு விளக்கங்களை அறியலாம். PDF மற்றும் DOCX கோப்புகளை இங்கே பதிவேற்றவும்.</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([7, 3])

with col_left:
    uploaded = st.file_uploader("Upload Government Order (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
    
    if uploaded:
        raw_text = extract_text(uploaded)
        words = raw_text.split()
        html_out = ""
        for w in words:
            clean = correct_spelling(w)
            if clean:
                html_out += f'<span class="tw" onclick="window.parent.postMessage({{type:\'streamlit:setComponentValue\', value:\'{clean}\'}}, \'*\')">{w}</span> '
            else:
                html_out += f'{w} '
        
        st.markdown(f'<div class="reader-box">{html_out}</div>', unsafe_allow_html=True)
    else:
        st.info("Please upload a file or use the search box on the right.")

with col_right:
    st.markdown("### 🔍 Word Analysis")
    # Captures the click from JS
    selected = st.text_input("Selected Word", key="word_sync", label_visibility="collapsed")
    
    if selected:
        res = smart_lookup(selected)
        if res:
            st.markdown(f"""
            <div class="mcard">
                <small style="color:var(--tn-saffron); font-weight:bold;">{res['tier']}</small>
                <h2 style="color:var(--tn-navy); margin-top:0;">{selected}</h2>
                <hr>
                <div style="font-size:1.1rem; font-weight:bold;">English: {res['en']}</div>
                
                <div class="mcard-ta">
                    <small style="color:green; font-weight:bold;">🏛️ GOVERNMENT MEANING</small><br>
                    {res['govt']}
                </div>
                
                <div style="padding:10px; border-left:4px solid var(--tn-saffron); background:#fff9e6; margin-bottom:10px;">
                    <small style="color:#e07b00; font-weight:bold;">🧠 SIMPLE TAMIL</small><br>
                    {res['simple']}
                </div>

                <div style="font-size:0.8rem; color:#666; font-style:italic; border-top:1px dashed #ccc; padding-top:10px;">
                    <b>Form Usage:</b> {res['form']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Audit Log Display
    with st.expander("📜 Word Audit Log (History)"):
        if 'audit_log' in st.session_state:
            for entry in reversed(st.session_state.audit_log[-10:]):
                st.write(f"[{entry['time']}] Viewed: **{entry['word']}**")

# JS BRIDGE
st.components.v1.html("""
<script>
    const watcher = new MutationObserver(() => {
        const words = window.parent.document.querySelectorAll('.tw');
        words.forEach(el => {
            el.onclick = () => {
                const input = window.parent.document.querySelector('input[aria-label="Selected Word"]');
                if(input) {
                    input.value = el.innerText.trim();
                    input.dispatchEvent(new Event('input', {bubbles:true}));
                }
            };
        });
    });
    watcher.observe(window.parent.document.body, {childList:true, subtree:true});
</script>
""", height=0)
