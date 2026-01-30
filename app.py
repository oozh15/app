import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup
from docx import Document
import unicodedata
import re
import io

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Tamil Professional Reader",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Tamil PDF / Image Professional Reader")
st.write(
    "Upload a PDF or Image → copy a Tamil word → get verified meaning (Non-AI)"
)

# -------------------------------
# Tamil Unicode Normalization
# -------------------------------
def normalize_tamil_word(word):
    # Normalize Unicode form
    word = unicodedata.normalize("NFC", word)

    # Remove zero-width characters
    word = re.sub(r"[\u200b\u200c\u200d]", "", word)

    # Remove unwanted spaces
    word = re.sub(r"\s+", "", word)

    return word.strip()

# -------------------------------
# Fetch Meaning (Tamilcube)
# -------------------------------
def fetch_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except:
        return "Dictionary server not reachable."

    if response.status_code != 200:
        return "Meaning not found."

    soup = BeautifulSoup(response.text, "html.parser")
    div = soup.find("div", class_="meaning")

    if div:
        return div.get_text(strip=True)
    else:
        return "Meaning not found."

# -------------------------------
# Upload PDF / Image
# -------------------------------
uploaded_file = st.file_uploader(
    "📂 Upload Tamil PDF or Image",
    type=["pdf", "png", "jpg", "jpeg"]
)

extracted_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

    else:
        image = Image.open(uploaded_file)
        extracted_text = pytesseract.image_to_string(image, lang="tam")

# -------------------------------
# Show extracted text
# -------------------------------
if extracted_text:
    st.subheader("📄 Extracted Text (Copy word manually)")
    st.text_area(
        "Select & copy a Tamil word from below",
        extracted_text,
        height=220
    )

# -------------------------------
# User copy & paste word
# -------------------------------
st.subheader("✂️ Paste Copied Tamil Word")

copied_word = st.text_input(
    "Paste word here",
    placeholder="உதாரணம்: மதியால்"
)

if st.button("📖 Get Meaning"):
    if not copied_word.strip():
        st.warning("Please paste a Tamil word.")
    else:
        clean_word = normalize_tamil_word(copied_word)

        meaning = fetch_meaning(clean_word)

        st.success("Meaning fetched successfully")

        st.markdown("### 🔤 Normalized Word")
        st.code(clean_word)

        st.markdown("### 📘 Meaning")
        st.write(meaning)

        st.markdown(
            "🔗 **Source:** [Tamilcube Dictionary](https://dictionary.tamilcube.com/)"
        )

        # -------------------------------
        # DOCX Export
        # -------------------------------
        doc = Document()
        doc.add_heading("Tamil Word Meaning", level=1)
        doc.add_paragraph(f"Word: {clean_word}")
        doc.add_paragraph(f"Meaning: {meaning}")
        doc.add_paragraph("Source: Tamilcube Dictionary")

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            "⬇️ Download DOCX",
            buffer,
            file_name="tamil_word_meaning.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
