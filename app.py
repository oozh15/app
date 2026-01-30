import streamlit as st
import pdfplumber

st.set_page_config(page_title="Tamil PDF Reader", layout="wide")

st.title("📘 Tamil PDF Reader (Direct Search)")
st.caption("Upload Tamil PDF → Search any word → Fetch meaning directly")

# -------------------------------
# Upload PDF
# -------------------------------
uploaded_file = st.file_uploader(
    "Upload Tamil PDF",
    type=["pdf"]
)

if uploaded_file:
    # Open PDF using pdfplumber
    with pdfplumber.open(uploaded_file) as pdf:
        # Extract all text from all pages
        pdf_text_pages = [page.extract_text() or "" for page in pdf.pages]

    st.subheader("📄 PDF Text Preview")
    combined_text = "\n\n".join(pdf_text_pages)
    st.text_area("PDF Content (scrollable)", combined_text, height=300)

    # -------------------------------
    # Word search in PDF
    # -------------------------------
    st.subheader("🔍 Search Word in PDF")
    search_word = st.text_input("Enter Tamil word to search:")

    if st.button("Search"):
        if not search_word.strip():
            st.warning("Please enter a word")
        else:
            found = False
            results = []

            for page_num, page_text in enumerate(pdf_text_pages, start=1):
                if search_word in page_text:
                    found = True
                    # Extract surrounding text (for context)
                    lines = page_text.split("\n")
                    for line in lines:
                        if search_word in line:
                            results.append(f"Page {page_num}: {line.strip()}")

            if found:
                st.success(f"Word '{search_word}' found in PDF!")
                for res in results:
                    # Highlight the word in the line
                    highlighted = res.replace(search_word, f"**{search_word}**")
                    st.markdown(highlighted)
            else:
                st.warning(f"Word '{search_word}' not found in PDF.")
