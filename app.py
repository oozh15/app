import streamlit as st
import json, re, io, time
from datetime import datetime
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════════════
# 1. GOVERNMENT DATASETS (OFFLINE MODE READY)
# ══════════════════════════════════════════════════════════════════════

# Official TN Govt / Legal Glossary
GOVT_GLOSSARY = {
    "அங்கீகாரம்": {"english": "Approval / Recognition", "govt": "அதிகாரப்பூர்வ ஒப்புதல்", "simple": "அதிகாரிகள் ஒப்புதல் கொடுப்பது", "form": "Used in certificate verification forms"},
    "நிர்வாகம்": {"english": "Administration", "govt": "ஆட்சிப்பணி / மேலாண்மை", "simple": "அரசு வேலைகளை நடத்துவது", "form": "Found in departmental headers"},
    "ஒப்பந்தம்": {"english": "Contract / Agreement", "govt": "உடன்படிக்கை", "simple": "இரு தரப்பு உறுதிமொழி", "form": "Standard Lease/Tender documents"},
    "ஆணை": {"english": "Order / Decree", "govt": "அரசாணை (G.O)", "simple": "அரசு வெளியிடும் உத்தரவு", "form": "G.O. Number section"},
}

# ══════════════════════════════════════════════════════════════════════
# 2. CORE LOGIC (MODIFIED LOOKUP)
# ══════════════════════════════════════════════════════════════════════

def correct_spelling(word):
    """Placeholder for spell-check model. Currently returns original."""
    # Logic: compare with GOVT_GLOSSARY keys using Levenshtein distance
    return word 

def detect_context(word):
    """Detects if the word is Legal, General, or Administrative."""
    if word in GOVT_GLOSSARY: return "⚖️ Legal/Govt"
    return "📝 General"

def tier2_json(word):
    """Searches the local official glossary."""
    return GOVT_GLOSSARY.get(word)

def tier3_chain(word):
    """Online fallback translation."""
    try:
        en = GoogleTranslator(source='ta', target='en').translate(word)
        return {"english": en, "govt": "N/A", "simple": "General translation", "form": "General use"}
    except: return None

def smart_lookup(word):
    """The Tiered Engine requested in Requirement #6."""
    word = correct_spelling(word)
    context = detect_context(word)
    
    # Tiered Search
    base = tier2_json(word) or tier3_chain(word)
    
    if not base:
        return {"english": "Not found", "govt": "N/A", "simple": "N/A", "form": "N/A"}

    # Add to Audit Log
    if 'audit_log' not in st.session_state: st.session_state.audit_log = []
    st.session_state.audit_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "word": word,
        "context": context
    })

    return {
        **base,
        "corrected": word,
        "context": context,
    }

# ══════════════════════════════════════════════════════════════════════
# 3. UI COMPONENTS (IMPROVED MEANING CARD)
# ══════════════════════════════════════════════════════════════════════

def render_meaning_card(res):
    """UI for Requirement #5: Enhanced Meaning Card."""
    st.markdown(f"""
    <div style="background:white; border-top:5px solid #8b1a1a; padding:20px; border-radius:8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#b8860b; font-weight:bold; font-size:0.8rem;">{res['context']}</span>
            <span style="font-size:0.7rem; color:gray;">ID: {res['corrected']}</span>
        </div>
        <h2 style="color:#003366; margin-top:5px;">{res['corrected']}</h2>
        
        <div style="margin-bottom:15px;">
            <div style="color:#888; font-size:0.7rem; text-transform:uppercase;">📖 Meaning (English)</div>
            <div style="font-size:1.2rem; font-weight:bold;">{res['english']}</div>
        </div>

        <div style="background:#f0f4f8; padding:10px; border-radius:5px; margin-bottom:10px;">
            <div style="color:#003366; font-size:0.7rem; font-weight:bold;">🏛️ Government Usage</div>
            <div style="font-size:0.9rem;">{res['govt']}</div>
        </div>

        <div style="background:#fff9e6; padding:10px; border-radius:5px; margin-bottom:10px; border-left:4px solid #e07b00;">
            <div style="color:#c06800; font-size:0.7rem; font-weight:bold;">🧠 Simple Explanation</div>
            <div style="font-size:0.9rem;">{res['simple']}</div>
        </div>

        <div style="border:1px dashed #ccc; padding:10px; border-radius:5px;">
            <div style="color:#666; font-size:0.7rem; font-weight:bold;">📋 Form Example</div>
            <div style="font-size:0.85rem; font-style:italic; color:#444;">{res['form']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 4. MAIN APP INTEGRATION
# ══════════════════════════════════════════════════════════════════════

# ... (Insert Header and Style definitions from previous turn here) ...

col_reader, col_insights = st.columns([7, 3])

with col_reader:
    st.subheader("📄 Document Workspace")
    text_input = st.text_area("Paste Tamil Document or Govt Order:", height=200, placeholder="அங்கீகாரம் வழங்கப்பட்டது...")
    
    if text_input:
        words = text_input.split()
        html_bits = []
        for w in words:
            # Simple clickable span logic
            html_bits.append(f'<span class="tw" onclick="window.parent.postMessage({{type:\'streamlit:setComponentValue\', value:\'{w}\'}}, \'*\')">{w}</span>')
        st.markdown(f'<div class="reader-pane">{" ".join(html_bits)}</div>', unsafe_allow_html=True)

with col_insights:
    st.subheader("🔍 Insights")
    # Capture word from JS (Requirement 6 Hook)
    selected_word = st.text_input("Selection", key="word_sync", label_visibility="collapsed")
    
    if selected_word:
        data = smart_lookup(selected_word)
        render_meaning_card(data)
    
    # Requirement #4: Audit Log (Visible in Sidebar or bottom)
    with st.expander("📝 Audit Log (Word History)"):
        if 'audit_log' in st.session_state:
            for entry in st.session_state.audit_log[-5:]:
                st.write(f"[{entry['time']}] **{entry['word']}** - {entry['context']}")

# Bridge JS
st.components.v1.html("""
<script>
    const watcher = new MutationObserver(() => {
        const words = window.parent.document.querySelectorAll('.tw');
        words.forEach(el => {
            el.onclick = () => {
                const input = window.parent.document.querySelector('input[aria-label="Selection"]');
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
