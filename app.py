import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import base64
import re

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் ஸ்மார்ட் ரீடர் 2026", layout="wide")

st.markdown("""
    <style>
    .pdf-container { border: 2px solid #ddd; border-radius: 10px; overflow: hidden; }
    .meaning-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 8px solid #004d99; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .line-selector { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

def get_tamil_meaning(word):
    """ஆன்லைன் அகராதி இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

st.title("🏛️ தமிழ் 'நிபுணர்' ஆவண வாசிப்பாளர்")

uploaded_file = st.file_uploader("PDF-ஐப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    # 1. PDF-ஐத் திரையில் காட்ட Base64 ஆக மாற்றுதல்
    base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("📄 உங்கள் ஆவணம்")
        st.markdown(f'<div class="pdf-container">{pdf_display}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔍 லெக்சிகன் விளக்கம்")
        
        # 2. OCR மூலம் வரிகளைப் பிரித்தல் (பின்னணியில்)
        with st.spinner("OCR மூலம் வரிகளை வாசிக்கிறது..."):
            uploaded_file.seek(0) # ஃபைல் பாயிண்டரை மீண்டும் தொடக்கத்திற்கு கொண்டு வருதல்
            images = convert_from_bytes(uploaded_file.read())
            all_lines = []
            for img in images:
                text = pytesseract.image_to_string(img, lang='tam')
                all_lines.extend([l.strip() for l in text.split('\n') if len(l.strip()) > 5])

        if all_lines:
            st.markdown('<div class="line-selector">', unsafe_allow_html=True)
            current_line = st.selectbox("விளக்கம் வேண்டிய வரியைத் தேர்ந்தெடுக்கவும்:", all_lines)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # சொற்களைப் பிரித்தல்
            words = current_line.split()
            selected_word = st.radio("எந்த சொல்லின் பொருள் தேவை?", words, horizontal=True)

            if selected_word:
                # புள்ளி கமா நீக்கம்
                clean_word = re.sub(r'[^\u0b80-\u0bff]', '', selected_word)
                
                with st.status(f"'{clean_word}' தேடுகிறது..."):
                    meaning = get_tamil_meaning(clean_word)
                
                if meaning:
                    st.markdown(f"""
                        <div class="meaning-card">
                            <h2 style='color: #004d99;'>{clean_word}</h2>
                            <p><b>பொருள்:</b> {meaning}</p>
                            <hr>
                            <p style='color: #555;'><b>குறிப்பு:</b> இது அகராதி முறைப்படி 'உயர்தர' சொல்லாகும்.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("பொருள் கிடைக்கவில்லை.")
        else:
            st.error("இந்த PDF-இல் இருந்து உரையை வாசிக்க முடியவில்லை.")

st.markdown("---")
st.caption("Standard High-Level Tamil Project | 2026 Online Run")
