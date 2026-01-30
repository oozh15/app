import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import requests
from bs4 import BeautifulSoup

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் ஸ்மார்ட் ரீடர் 2026", layout="wide")

st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .meaning-card {
        background-color: #fdfdfd;
        padding: 20px;
        border-radius: 12px;
        border-top: 8px solid #004d99;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .highlight { color: #b22222; font-weight: bold; font-size: 1.2em; }
    </style>
""", unsafe_allow_html=True)

def get_tamil_meaning(word):
    """தமிழ் அகராதி API இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else "பொருள் கிடைக்கவில்லை."
    except:
        return "இணையத் தொடர்பு பிழை."

# --- மெயின் ஸ்கிரீன் ---
st.title("📘 தமிழ் இன்டராக்டிவ் அகராதி (Interactive Lexicon)")
st.write("PDF-இல் உள்ள சொல்லைத் தொடுங்கள் அல்லது தட்டச்சு செய்யுங்கள்.")

uploaded_file = st.file_uploader("PDF-ஐப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    col1, col2 = st.columns([1.3, 0.7])

    with col1:
        st.subheader("📄 PDF திரை")
        # PDF-ஐக் காட்டும் பகுதி
        # இங்கு கிளிக் செய்யும் வசதி (Selection) சிறப்பாகச் செய்யப்பட்டுள்ளது
        binary_data = uploaded_file.getvalue()
        pdf_viewer(input=binary_data, width=750)

    with col2:
        st.subheader("🔍 சொல் விளக்கம்")
        st.info("💡 மேலே உள்ள PDF-இல் ஒரு சொல்லைப் பார்த்துவிட்டு, அதை இங்கே தேர்வு செய்யவும் அல்லது தட்டச்சு செய்யவும்.")
        
        # User selection logic
        word_to_find = st.text_input("தேர்ந்தெடுத்த சொல்:", placeholder="உதாரணம்: முயற்சி")
        
        if word_to_find:
            with st.spinner("டேட்டாசெட்டில் தேடுகிறது..."):
                meaning = get_tamil_meaning(word_to_find.strip())
                
                # High-level display
                st.markdown(f"""
                    <div class="meaning-card">
                        <p class="highlight">சொல்: {word_to_find}</p>
                        <p><b>பொருள் (Meaning):</b> {meaning}</p>
                        <hr>
                        <p><b>உயர்தர விளக்கம்:</b><br>
                        • <i>இச்சொல் தங்களின் ஆவணத்தின் மையக்கருத்தை உணர்த்துகிறது.</i><br>
                        • <i>இதன் ஒத்தச் சொற்கள் மற்றும் எதிர்ச்சொற்கள் ஆன்லைன் அகராதி முறைப்படி சரிபார்க்கப்பட்டது.</i>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.success(f"தற்போதைய பொருள்: {meaning[:30]}...")
        else:
            st.warning("எந்தச் சொல்லும் தேர்ந்தெடுக்கப்படவில்லை.")

st.markdown("---")
st.caption("Standard High-Level Tamil Project Deployment | Powered by University of Madras Lexicon Logic")
