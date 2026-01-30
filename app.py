import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup
from docx import Document
import io

st.set_page_config(page_title="Tamil PDF/Image Reader", page_icon="📄")

st.title("📄 Tamil PDF / Image Reader (Non-AI)")
st.write("Upload a PDF or Image → select Tamil words → get meaning → export DOCX")

# -----------------------------
# Dictionary fetch (Tamilcube)
# -----------------------------
def fetch_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)

    if res.status_code != 200:
        return "Meaning not found"

    soup = BeautifulSoup(res.text, "html.parser")
    div = soup.find("div", class_="meaning")
    return div.text.strip() if div else "Meaning not found"

# -----------------------------
# File Upload
# -----------------------------
uploaded = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

extracted_text = ""

if uploaded:
    if uploaded.type == "application/pdf":
        with pdfplumber.open(uploaded) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"

    else:
        image = Image.open(uploaded)
        extracted_text = pytesseract.image_to_string(image, lang="tam")

# -----------------------------
# Show extracted text
# -----------------------------
if extracted_text:
    st.subheader("📃 Extracted Tamil Text")
    st.text_area("Text", extracted_text, height=200)

    words = list(set(extracted_text.split()))
    selected_word = st.selectbox("🔍 Select a word", words)

    if selected_word:
        meaning = fetch_meaning(selected_word)

        st.subheader("📘 Meaning")
        st.write(meaning)

        # DOCX Export
        if st.button("⬇️ Add to DOCX"):
            doc = Document()
            doc.add_heading("Tamil Word Meanings", level=1)
            doc.add_paragraph(f"Word: {selected_word}")
            doc.add_paragraph(f"Meaning: {meaning}")
            doc.add_paragraph("Source: Tamilcube Dictionary")

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            st.download_button(
                "Download DOCX",
                buffer,
                file_name="tamil_meaning.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
