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

st.set_page_config(page_title="Tamil Reader", page_icon="📘")

st.title("📘 Tamil PDF / Image Reader (Improved)")
st.write("Copy Tamil word → normalize → fetch meaning from online dataset")

# -------------------------
# STRONG Tamil Normalizer
# -------------------------
def normalize_tamil_word(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\u200b\u200c\u200d]", "", text)
    text = re.sub(r"[^அ-ஹா-௺]", "", text)  # keep only Tamil chars
    return text.strip()

# -------------------------
# STRONG Dictionary Fetch
# -------------------------
def fetch_dictionary(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200:
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")

    meaning = None
    antonyms = []

    # --- Meaning fallback search ---
    possible_blocks = soup.find_all(["div", "span", "p"])
    for block in possible_blocks:
        text = block.get_text(strip=True)
        if len(text) > 20 and word in text:
            meaning = text
            break

    # --- Antonyms ---
    for tag in soup.find_all("b"):
        if "Antonym" in tag.text:
            ul = tag.find_next("ul")
            if ul:
                antonyms = [li.text.strip() for li in ul.find_all("li")]

    return meaning, antonyms

# -------------------------
# File Upload
# -------------------------
file = st.file_uploader("Upload Tamil PDF or Image", ["pdf", "png", "jpg", "jpeg"])
extracted_text = ""

if file:
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted_text += (page.extract_text() or "") + "\n"
    else:
        img = Image.open(file)
        extracted_text = pytesseract.image_to_string(img, lang="tam")

# -------------------------
# Display extracted text
# -------------------------
if extracted_text:
    st.subheader("📄 Extracted Text (manual copy)")
    st.text_area("Copy Tamil word from below", extracted_text, height=220)

# -------------------------
# User copy-paste
# -------------------------
st.subheader("✂️ Paste Copied Tamil Word")
raw_word = st.text_input("Paste here")

if st.button("📖 Get Meaning"):
    if not raw_word:
        st.warning("Paste a Tamil word")
    else:
        clean_word = normalize_tamil_word(raw_word)

        st.markdown("### 🔧 Normalized Word")
        st.code(clean_word)

        meaning, antonyms = fetch_dictionary(clean_word)

        if not meaning:
            st.error("Meaning not found. Try copying word again carefully.")
        else:
            st.success("Meaning fetched")

            st.markdown("### 📘 Meaning")
            st.write(meaning)

            st.markdown("### 🔁 Antonyms")
            if antonyms:
                for a in antonyms:
                    st.write("•", a)
            else:
                st.write("No antonyms available")

            # DOCX Export
            doc = Document()
            doc.add_heading("Tamil Dictionary Result", 1)
            doc.add_paragraph(f"Word: {clean_word}")
            doc.add_paragraph(f"Meaning: {meaning}")

            if antonyms:
                doc.add_paragraph("Antonyms:")
                for a in antonyms:
                    doc.add_paragraph(f"- {a}")

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            st.download_button(
                "⬇️ Download DOCX",
                buffer,
                "tamil_dictionary.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
