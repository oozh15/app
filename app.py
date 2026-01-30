import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="Tamil Dictionary Reader",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Tamil Professional Reader (Non-AI)")
st.write("Select a Tamil word and get its verified meaning from online academic sources.")

# Input box
word = st.text_input("🔍 Enter a Tamil word", placeholder="உதாரணம்: மதியால்")

def fetch_tamilcube_meaning(word):
    url = f"https://dictionary.tamilcube.com/tamil-dictionary.aspx?term={word}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    result_div = soup.find("div", {"class": "meaning"})

    if result_div:
        return result_div.get_text(strip=True)

    return None


if st.button("📖 Get Meaning"):
    if not word.strip():
        st.warning("Please enter a Tamil word.")
    else:
        with st.spinner("Fetching meaning from online dictionary..."):
            meaning = fetch_tamilcube_meaning(word)

        if meaning:
            st.success("Meaning found ✅")

            st.markdown("### 📌 Meaning")
            st.write(meaning)

            st.markdown("---")
            st.markdown(
                "🔗 **Source:** [Tamilcube Dictionary](https://dictionary.tamilcube.com/)"
            )
        else:
            st.error("Meaning not found or source temporarily unavailable.")
