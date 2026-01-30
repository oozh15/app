import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import requests
from bs4 import BeautifulSoup

# --- பக்க வடிவமைப்பு ---
st.set_page_config(page_title="தமிழ் ஸ்மார்ட் ரீடர்", layout="wide")

st.markdown("""
    <style>
    .meaning-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #004d99;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        position: sticky;
        top: 20px;
    }
    .selection-text {
        color: #b22222;
        font-weight: bold;
        background-color: #fff3f3;
        padding: 5px;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

def get_tamil_meaning(word):
    """தமிழ் அகராதி ஆன்லைன் இணைப்பு"""
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning = soup.find("div", {"class": "translation"})
        return meaning.text.strip() if meaning else None
    except:
        return None

st.title("🎯 இன்டராக்டிவ் தமிழ் அகராதி (Automatic Capture)")
st.write("PDF-இல் உள்ள கடினமான வரியை அல்லது சொல்லைக் கிளிக் செய்யவும்.")

uploaded_file = st.file_uploader("PDF-ஐப் பதிவேற்றவும்", type=['pdf'])

if uploaded_file:
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        st.subheader("📄 PDF திரை")
        # render_text=True என்பது பயனரின் கிளிக்குகளைப் பிடிக்க உதவும்
        # annotations_on_text_click=True கிளிக்கைத் தூண்டும்
        selected_data = pdf_viewer(
            input=uploaded_file.getvalue(),
            width=750,
            render_text=True,
            annotations_on_text_click=True
        )

    with col2:
        st.subheader("🔍 தானியங்கி விளக்கம்")
        
        # பயனர் எதையாவது கிளிக் செய்திருந்தால் மட்டும் இது வேலை செய்யும்
        if selected_data and 'text' in selected_data:
            selected_text = selected_data['text'].strip()
            
            if selected_text:
                st.markdown(f"**தேர்ந்தெடுக்கப்பட்ட உரை:** <span class='selection-text'>{selected_text}</span>", unsafe_allow_html=True)
                
                # ஒரு வரியாக இருந்தால் முதல் சொல்லை மட்டும் எடுத்துத் தேடும் அல்லது பயனர் தேர்வு செய்யலாம்
                words = selected_text.split()
                target = st.selectbox("விளக்கம் வேண்டிய சொல்லைத் தேர்வு செய்க:", words) if len(words) > 1 else words[0]

                with st.spinner("ஆன்லைன் தரவைச் சேகரிக்கிறது..."):
                    meaning = get_tamil_meaning(target.strip(",.?!"))
                
                if meaning:
                    st.markdown(f"""
                        <div class="meaning-card">
                            <h3 style='color: #004d99;'>சொல்: {target}</h3>
                            <p><b>பொருள்:</b> {meaning}</p>
                            <hr>
                            <p style='color: #555;'>
                            <b>2-வரி விளக்கம்:</b><br>
                            1. '{target}' என்பது ஆவணத்தின் சூழலில் மிக முக்கியமான உயர்நிலைச் சொல்லாகும்.<br>
                            2. இதன் பொதுவான அகராதி விளக்கம்: {meaning}.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("இந்தச் சொல்லிற்கு நேரடிப் பொருள் கிடைக்கவில்லை. வேறு சொல்லைத் தேர்வு செய்யவும்.")
        else:
            st.info("💡 PDF-இல் உள்ள ஏதேனும் ஒரு சொல்லை அல்லது வரியை மவுஸ் மூலம் கிளிக் செய்யவும். அதன் பொருள் இங்கே தானாகத் தோன்றும்.")

st.markdown("---")
st.caption("Standard High-Level Real-time Deployment 2026")
