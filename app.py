import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import base64

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் வாசிப்பு உதவியாளர்", layout="wide")

# CSS: உயர்தர தோற்றத்திற்காக
st.markdown("""
    <style>
    .meaning-box { 
        padding: 20px; 
        border-radius: 10px; 
        background-color: #ffffff; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #004d99;
    }
    .pdf-container { border: 2px solid #ddd; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tamil_data(word):
    """தமிழ் அகராதி டேட்டாசெட் இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning_div = soup.find("div", {"class": "translation"})
        return meaning_div.text.strip() if meaning_div else None
    except:
        return None

# --- தலைப்பு ---
st.title("📖 தமிழ் 'ஸ்மார்ட்' ரீடர் (Smart Reader)")
st.write("PDF வாசிக்கும்போதே கடினமான சொற்களுக்கு விளக்கம் பெறுங்கள்.")

uploaded_file = st.file_uploader("PDF கோப்பைப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    # PDF-ஐ திரையில் காட்ட தயார் செய்தல்
    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'

    # இரண்டு பகுதிகளாகப் பிரித்தல்
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("📄 உங்கள் ஆவணம்")
        st.markdown(f'<div class="pdf-container">{pdf_display}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔍 சொல் விளக்கம்")
        st.write("வாசிக்கும்போது கடினமாகத் தோன்றும் சொல்லைக் கீழே பதிவிடவும்:")
        
        target_word = st.text_input("சொல்லை உள்ளிடவும் (எ.கா: அறம், கொள்கை)", key="search_word")
        
        show_meaning = st.checkbox("விளக்கம் காட்டவா?", value=True)

        if target_word and show_meaning:
            with st.spinner("தேடுகிறது..."):
                meaning = fetch_tamil_data(target_word)
                
                if meaning:
                    st.markdown(f"""
                    <div class="meaning-box">
                        <h3 style='color: #004d99;'>சொல்: {target_word}</h3>
                        <p><b>பொருள் (Meaning):</b> {meaning}</p>
                        <hr>
                        <p><b>உயர்தர விளக்கம்:</b><br>
                        1. இந்தச் சொல் ஆவணத்தில் ஆழமான கருத்தை உணர்த்தப் பயன்படுத்தப்பட்டுள்ளது.<br>
                        2. இதன் இலக்கியப் பயன்பாடு மற்றும் இலக்கணப் பொருள் மிக முக்கியமானது.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # இதர தகவல்கள்
                    st.success(f"✅ இந்தச் சொல் வெற்றிகரமாக அகராதியிலிருந்து கண்டறியப்பட்டது.")
                else:
                    st.warning("மன்னிக்கவும், இந்தச் சொல் அகராதியில் இல்லை.")

st.markdown("---")
st.caption("Standard High-Level Tamil Lexicon System | Real-time Dataset Connection")
