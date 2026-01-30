import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import requests
from bs4 import BeautifulSoup
import re
import base64
import io
import cv2
import numpy as np
import unicodedata
from docx import Document

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Tamil Professional Lexicon", layout="wide")

st.markdown("""
<style>
.result-card {
    background:#ffffff;
    padding:20px;
    border-radius:12px;
    border-left:8px solid #0d47a1;
    box-shadow:0 4px 12px rgba(0,0,0,0.1);
}
.dataset-tag {
    background:#e3f2fd;
    color:#0d47a1;
    padding:4px 8px;
    border-radius:6px;
    font-size:12px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- OCR PREPROCESSING ----------------
def preprocess_image(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )
    return thresh

# ---------------- TAMIL NORMALIZATION ----------------
def normalize_tamil(word):
    word = unicodedata.normalize("NFC", word)
    word = re.sub(r'[^\u0b80-\u0bff]', '', word)
    return word

def get_root_word(word):
    word = normalize_tamil(word)
    suffixes = [
        'இருந்து','உடைய','உக்காக','க்காக','த்தால்',
        'ோடு','இடம்','உக்கு','ுக்கு','ின்','இல்','ஆல்','ை'
    ]
    for s in suffixes:
        if word.endswith(s) and len(word) > 4:
            return word[:-len(s)]
    return word

# ---------------- ONLINE DATASET FETCH ----------------
def fetch_meaning(word):
    result = {
        "meaning": "Meaning not found",
        "antonym": "Not found",
        "source": "Tamilcube Online Dictionary"
    }

    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")

        meaning_block = soup.find("div", id="ContentPlaceHolder1_lblMeaning")
        if meaning_block:
            result["meaning"] = meaning_block.get_text(strip=True)

        text = soup.get_text(separator="\n")
        for line in text.splitlines():
            if "Antonym" in line or "எதிர்ச்சொல்" in line:
                result["antonym"] = line.strip()
                break

    except:
        pass

    return result

# ---------------- DOCX EXPORT ----------------
def create_docx(data):
    doc = Document()
    doc.add_heading("Tamil Lexicon Report", 0)

    for d in data:
        doc.add_paragraph(f"Word: {d['word']}").bold = True
        doc.add_paragraph(f"Meaning: {d['meaning']}")
        doc.add_paragraph(f"Antonym: {d['antonym']}")
        doc.add_paragraph(f"Source: {d['source']}")
        doc.add_paragraph("-" * 30)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

# ---------------- UI ----------------
st.title("📘 Tamil Professional Lexicon Reader")
st.info("PDF / Image → Select Tamil word → Live meaning (No AI, No API)")

if "history" not in st.session_state:
    st.session_state.history = []

uploaded = st.file_uploader("Upload PDF or Image", type=["pdf","png","jpg","jpeg"])

if uploaded:
    file_bytes = uploaded.read()

    col1, col2 = st.columns([1,1])

    # ---------- DOCUMENT VIEW ----------
    with col1:
        st.subheader("📄 Document")
        if uploaded.type == "application/pdf":
            pdf64 = base64.b64encode(file_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{pdf64}" width="100%" height="600"></iframe>',
                unsafe_allow_html=True
            )
        else:
            st.image(uploaded)

    # ---------- OCR + ANALYSIS ----------
    with col2:
        st.subheader("🔍 Extract & Analyze")

        with st.spinner("Extracting Tamil text..."):
            images = convert_from_bytes(file_bytes) if uploaded.type == "application/pdf" else [Image.open(uploaded)]
            text = ""

            for img in images:
                processed = preprocess_image(img)
                text += pytesseract.image_to_string(processed, lang="tam", config="--psm 6")

        tamil_lines = [l for l in text.split("\n") if len(l.strip()) > 5]

        if tamil_lines:
            line = st.selectbox("Select a line:", tamil_lines)

            words = re.findall(r'[\u0b80-\u0bff]{3,}', line)

            if words:
                word = st.radio("Select a word:", words)

                root = get_root_word(word)
                data = fetch_meaning(root)

                st.markdown(f"""
                <div class="result-card">
                    <span class="dataset-tag">{data['source']}</span>
                    <h3>{word}</h3>
                    <p><b>Root Word:</b> {root}</p>
                    <p><b>Meaning:</b> {data['meaning']}</p>
                    <p><b>Antonym:</b> {data['antonym']}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("➕ Add to Report"):
                    st.session_state.history.append({
                        "word": word,
                        "meaning": data["meaning"],
                        "antonym": data["antonym"],
                        "source": data["source"]
                    })
                    st.success("Added to report")

# ---------------- DOWNLOAD REPORT ----------------
if st.session_state.history:
    st.divider()
    st.subheader("📑 Research Report")
    docx = create_docx(st.session_state.history)
    st.download_button("⬇ Download DOCX", docx, "Tamil_Lexicon_Report.docx")
