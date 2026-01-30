import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import requests
from bs4 import BeautifulSoup

# --- பக்க அமைப்பு ---
st.set_page_config(page_title="தமிழ் ஸ்மார்ட் ரீடர்", layout="wide")

st.markdown("""
    <style>
    .selected-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #004d99;
        margin-bottom: 20px;
    }
    .meaning-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #b22222;
        box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

def get_tamil_meaning(word):
    """அகராதி தரவுத்தள இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else "பொருள் கிடைக்கவில்லை."
    except:
        return "இணைப்பு பிழை."

# --- UI ---
st.title("🎯 இன்டராக்டிவ் தமிழ் ரீடர் (Touch to Meanings)")
st.write("PDF-இல் உள்ள வரிகளைத் தொட்டு (Click) உடனே பொருள் அறியுங்கள்.")

uploaded_file = st.file_uploader("PDF பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        st.subheader("📄 PDF திரை")
        # annotations_on_text_click=True என்பதுதான் சொல்லைத் தொட அனுமதிக்கும்
        v = pdf_viewer(
            input=uploaded_file.getvalue(),
            width=700,
            annotations_on_text_click=True
        )

    with col2:
        st.subheader("🔍 விளக்கப் பகுதி")
        
        # பயனர் தொட்ட சொல் அல்லது வரி இங்கே பிடிபடும்
        if v and 'text' in v:
            selected_text = v['text']
            st.markdown(f'<div class="selected-box"><b>நீங்கள் தேர்ந்தெடுத்தது:</b><br>{selected_text}</div>', unsafe_allow_html=True)
            
            # வரியிலிருந்து சொற்களைத் தேர்ந்தெடுக்க ஒரு ஆப்ஷன்
            words = selected_text.split()
            target_word = st.selectbox("விளக்கம் வேண்டிய சொல்லைத் தேர்வு செய்யவும்:", words)

            if target_word:
                res = get_tamil_meaning(target_word.strip(",.?!"))
                
                st.markdown(f"""
                    <div class="meaning-card">
                        <h3 style='color: #b22222;'>சொல் விளக்கம்</h3>
                        <p><b>தேர்வு:</b> {target_word}</p>
                        <p><b>பொருள்:</b> {res}</p>
                        <hr>
                        <p style='color: #555;'>
                        <b>நிலைத்த விளக்கம்:</b><br>
                        1. '{target_word}' என்பது உயர்தர தமிழ் ஆவணங்களில் பயன்படுத்தப்படும் ஒரு சொல்லாகும்.<br>
                        2. இதன் விரிவான விளக்கம்: {res}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("PDF-இல் உள்ள ஒரு வரியை மவுஸ் மூலம் கிளிக் செய்யவும்.")

st.markdown("---")
st.caption("Advanced OCR-less Interaction | Tamil Lexicon Online Run 2026")
