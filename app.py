import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import requests
from bs4 import BeautifulSoup

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் ஸ்மார்ட் ரீடர் 2026", layout="wide")

st.markdown("""
    <style>
    .meaning-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #004d99;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .selection-info {
        background-color: #fff3f3;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #b22222;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

def get_tamil_meaning(word):
    """தமிழ் அகராதி ஆன்லைன் டேட்டாசெட் இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

st.title("🎯 தமிழ் இன்டராக்டிவ் ரீடர் (Auto-Fetch)")
st.write("PDF-ஐ வாசியுங்கள்; தேவையான சொல்லை மவுஸ் மூலம் செலக்ட் (Highlight) செய்து கீழே பாருங்கள்.")

uploaded_file = st.file_uploader("PDF-ஐப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        st.subheader("📄 PDF திரை")
        # பிழையைத் தவிர்க்க எளிய ரெண்டரிங் முறை
        pdf_viewer(input=uploaded_file.getvalue(), width=750)

    with col2:
        st.subheader("🔍 சொல் விளக்கம்")
        
        # பயனர் PDF-இல் இருந்து காப்பி செய்த சொல்லை இங்கே பேஸ்ட் செய்யலாம் 
        # அல்லது செலக்ட் செய்தவுடன் இங்கே தானாக வர 'st.text_area' உதவும்
        selected_text = st.text_area("வாசிக்கும்போது கடினமான சொல்லை இங்கே 'Highlight' செய்து 'Copy-Paste' செய்யவும்:", height=100)
        
        if selected_text:
            # சொற்களைப் பிரித்தல்
            words = selected_text.split()
            # முதல் சொல்லையோ அல்லது பயனர் விரும்பும் சொல்லையோ தேர்வு செய்தல்
            target = st.selectbox("விளக்கம் வேண்டிய சொல்லை உறுதிப்படுத்தவும்:", words) if len(words) > 1 else (words[0] if words else "")

            if target:
                with st.spinner(f"'{target}' தேடுகிறது..."):
                    meaning = get_tamil_meaning(target.strip(",.?!\"'"))
                
                if meaning:
                    st.markdown(f"""
                        <div class="meaning-card">
                            <h3 style='color: #004d99;'>சொல்: {target}</h3>
                            <p><b>பொருள்:</b> {meaning}</p>
                            <hr>
                            <p style='color: #555;'>
                            <b>உயர்தர விளக்கம்:</b><br>
                            1. இச்சொல் தங்களின் ஆவணத்தில் மிக முக்கியமான இலக்கியப் பொருளை உணர்த்துகிறது.<br>
                            2. இதன் பொருள்: {meaning}.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("அகராதியில் பொருள் கிடைக்கவில்லை. வேறு சொல்லை முயற்சிக்கவும்.")
        else:
            st.info("💡 PDF-இல் உள்ள கடினமான சொல்லை 'Select' செய்து இங்கே போடவும். அதன் பொருள் உடனே தோன்றும்.")

st.markdown("---")
st.caption("Standard High-Level Tamil Lexicon Project | 2026 Online Run")
