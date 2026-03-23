"""
Tamil Government Document Reader — v8
══════════════════════════════════════
FIXES in this version:
  1. Word cleaner — strips leading/trailing punctuation (, . ; : " ' () []) before lookup
  2. Transliteration detector — if MyMemory/Google returns Roman letters for a
     Tamil word it's just transliterating (e.g. "Inaimal"), not translating.
     We detect this and show "not found" instead of garbage.
  3. Massively expanded built-in dictionary — everyday Tamil words that
     online APIs fail on: இனிமேல், உரிமையாளர், ஒப்பந்தம், சாட்சி, etc.
  4. 100% free — zero API key, zero cost
"""

import io, re, requests
import streamlit as st
from gtts import gTTS
from PIL import Image, ImageEnhance
import pdfplumber, pytesseract
import numpy as np

st.set_page_config(page_title="தமிழ் ஆவண வாசகன்", page_icon="📜", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#f2ede6;}
.hdr{background:#0f172a;border-left:5px solid #d4a843;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.3rem;}
.hdr h1{color:#f8ecd4;font-size:1.6rem;font-weight:600;margin:0 0 .2rem;}
.hdr p{color:#a89880;font-size:.87rem;margin:0;}
.docbox{background:#fffef8;border:1px solid #ddd0b8;border-radius:12px;padding:1.5rem 1.9rem;
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;font-size:1.1rem;line-height:2.5;
  color:#111;white-space:pre-wrap;word-break:break-word;max-height:520px;overflow-y:auto;}
.mcard{background:#fff;border-radius:14px;border:1px solid #e2d8c8;
  box-shadow:0 4px 18px rgba(0,0,0,.06);padding:1.3rem 1.5rem;margin-top:.2rem;}
.mword{font-family:'Noto Sans Tamil',sans-serif;font-size:1.5rem;font-weight:600;color:#0f172a;margin-bottom:.05rem;}
.mroot{font-size:.74rem;color:#bbb;margin-bottom:1rem;}
.sec{margin-bottom:.85rem;border-radius:9px;overflow:hidden;}
.sec-head{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;padding:.3rem .75rem;}
.sec-body{font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;font-size:1rem;line-height:1.9;padding:.6rem .85rem;}
.s-tamil{background:#fff8e7;border:1px solid #f3d98b;}
.s-tamil .sec-head{background:#fef0c0;color:#7a5000;}
.s-tamil .sec-body{color:#3a2a00;}
.s-example{background:#f0f7ff;border:1px solid #b8d8f8;}
.s-example .sec-head{background:#dbeeff;color:#1a4a8a;}
.s-example .sec-body{color:#1a3a6a;font-style:italic;}
.s-doc{background:#fdf2ff;border:1px solid #ddb8f8;}
.s-doc .sec-head{background:#f0d0ff;color:#4a0080;}
.s-doc .sec-body{color:#280050;}
.s-note{background:#f0faf4;border:1px solid #a8dcb8;}
.s-note .sec-head{background:#c8f0d8;color:#1a5a30;}
.s-note .sec-body{color:#1a3a20;}
.s-online{background:#f8f8f8;border:1px solid #ddd;}
.s-online .sec-head{background:#eee;color:#444;}
.s-online .sec-body{color:#333;}
.notfound{font-size:.92rem;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:.7rem 1rem;margin-top:.5rem;}
.slabel{font-size:.71rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#999;margin-bottom:.35rem;}
.hint{display:inline-block;background:#fef9e7;border:1px solid #fce7a0;border-radius:8px;padding:.4rem .85rem;font-size:.82rem;color:#7a5100;margin-bottom:.85rem;}
.doc-chip{display:inline-block;font-size:.75rem;font-weight:600;padding:3px 10px;border-radius:20px;background:#e8f4fd;color:#1155aa;margin-bottom:.7rem;}
.step{background:#fff;border:1px solid #e5dfd4;border-radius:10px;padding:.85rem 1.1rem;margin-bottom:.5rem;font-size:.91rem;line-height:1.65;}
.num{display:inline-flex;align-items:center;justify-content:center;width:21px;height:21px;border-radius:50%;background:#0f172a;color:#d4a843;font-size:11px;font-weight:700;margin-right:7px;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# WORD CLEANER  — strips OCR noise before lookup
# ══════════════════════════════════════════════════════════════════════════════
def clean_word(w: str) -> str:
    """Remove leading/trailing punctuation and whitespace that OCR adds."""
    return re.sub(r'^[\s,.\-;:"""\'()[\]/\\|]+|[\s,.\-;:"""\'()[\]/\\|]+$', '', w).strip()


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLITERATION DETECTOR
# MyMemory/Google sometimes returns Roman phonetic spelling instead of meaning.
# e.g. இனிமேல் → "Inimel"  /  உரிமையாளர் → "Urimaiyalar"
# We detect this by checking if the result looks like Tamil word sounds spelled
# in English (no real English content words).
# ══════════════════════════════════════════════════════════════════════════════
# Common Tamil syllable patterns that appear in transliterations
_TRANSLIT_PATTERN = re.compile(
    r'^[A-Z][a-z]*(aa?|ii?|uu?|ee?|oo?|ai|au)'  # starts with Tamil vowel sound
    r'|^(Ini|Iru|Uru|Ula|Uma|Eli|Oru|Ath|Ith|Idh|Und|Nam|Sel|Ven|Poi|Van|Per|Mar|Kan|Sol|Kol|Pal|Val|Vil|Mel|Nal|Tal|Kal|Mun|Pin|Mut|Put|Nir|Tir|Nit)',
    re.IGNORECASE
)

# Real English words (even short ones) that are valid translations
_REAL_ENGLISH = re.compile(
    r'\b(from|now|on|here|after|hereafter|owner|person|agreement|contract|property|'
    r'land|certificate|order|court|legal|district|revenue|government|right|claim|'
    r'witness|seal|sign|date|number|area|name|address|amount|pay|tax|duty|'
    r'document|record|file|case|judge|petition|transfer|sale|lease|rent|'
    r'survey|boundary|village|house|building|the|this|that|and|or|of|in|to|'
    r'for|with|by|at|an|a|is|are|was|were|be|been|have|has|had|will|shall|'
    r'may|can|must|should|would|could|not|no|yes|new|old|first|last|total|'
    r'one|two|three|four|five|six|seven|eight|nine|ten)\b',
    re.IGNORECASE
)

def is_transliteration(tamil_input: str, result: str) -> bool:
    """Return True if result is just a transliteration of the Tamil input, not a real meaning."""
    if not result or len(result.strip()) < 2:
        return True
    r = result.strip()
    # If result contains real English words → it's a translation, not transliteration
    if _REAL_ENGLISH.search(r):
        return False
    # If result is purely Roman letters with no spaces and looks like Tamil sounds → transliteration
    if re.match(r'^[A-Za-z]+$', r) and len(r) < 20:
        return True
    # If result matches transliteration pattern
    if _TRANSLIT_PATTERN.match(r) and not _REAL_ENGLISH.search(r):
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN TAMIL GOVERNMENT + EVERYDAY WORD DICTIONARY
# ══════════════════════════════════════════════════════════════════════════════
GOVT_DICT = {

    # ── EVERYDAY LEGAL / DOCUMENT WORDS (most commonly looked up) ────────────
    "இனிமேல்": {
        "tamil": "இனிமேல் என்றால் 'இனி முதல்' அல்லது 'இப்போதிலிருந்து' என்று பொருள் — இனி செய்வோம், இனி நடக்கும் என்று குறிக்கும்",
        "example": "இனிமேல் இந்த நிலம் உங்கள் பெயரில் இருக்கும்.",
        "doc_context": "ஒப்பந்தம் அல்லது ஆணையில் 'இனிமேல்' என்று வந்தால் 'இந்த ஆவணம் கையொப்பமிட்ட நாளிலிருந்து' என்று பொருள்.",
    },
    "இனி": {
        "tamil": "இப்போதிலிருந்து / இனி முதல் / இனிவரும் காலத்தில்",
        "example": "இனி இந்த சொத்து உங்களுக்கு சொந்தம்.",
        "doc_context": "ஆவணத்தில் 'இனி' என்றால் இந்த ஆவணம் நடைமுறைக்கு வந்த நாளிலிருந்து என்று பொருள்.",
    },
    "உரிமையாளர்": {
        "tamil": "சொத்தின் உரிமை உள்ளவர் — நிலம், வீடு அல்லது பொருளின் சட்டபூர்வ சொந்தக்காரர்",
        "example": "இந்த வீட்டின் உரிமையாளர் திரு. ராமசாமி.",
        "doc_context": "ஆவணத்தில் உரிமையாளர் என்று வந்தால் அந்த சொத்தை சட்டரீதியாக வைத்திருப்பவர்.",
        "note": "உரிமையாளர் பெயர் பட்டாவில் பதிவு ஆகியிருக்க வேண்டும்."
    },
    "உரிமை": {
        "tamil": "ஒரு நபருக்கு சட்டப்படி சேர்ந்த அதிகாரம் அல்லது சொத்து",
        "example": "இந்த நிலத்தின் உரிமை அவருக்கு சேரும்.",
        "doc_context": "சட்ட ஆவணத்தில் உரிமை என்பது சட்டரீதியான உரிமைக்கோரல்.",
    },
    "வாடகை": {
        "tamil": "வீடு அல்லது நிலத்தை பயன்படுத்துவதற்காக ஒவ்வொரு மாதமும் கொடுக்கும் பணம்",
        "example": "மாதந்தோறும் 5000 ரூபாய் வாடகை செலுத்த வேண்டும்.",
        "doc_context": "வாடகை ஒப்பந்தத்தில் வாடகை தொகை, செலுத்தும் தேதி தெளிவாக இருக்க வேண்டும்.",
    },
    "குடியிருப்பவர்": {
        "tamil": "வீட்டில் வாடகையோ அல்லது வேறு வகையிலோ வசிக்கும் நபர்",
        "example": "குடியிருப்பவர் ஒவ்வொரு மாதமும் வாடகை கொடுக்க வேண்டும்.",
        "doc_context": "வாடகை ஒப்பந்தத்தில் குடியிருப்பவர் என்பவர் வீட்டை பயன்படுத்துபவர்.",
    },
    "வீட்டு உரிமையாளர்": {
        "tamil": "வீட்டை சொந்தமாக வைத்திருப்பவர் — வீட்டை வாடகைக்கு கொடுப்பவர்",
        "example": "வீட்டு உரிமையாளர் ஒப்பந்தத்தில் கையொப்பமிட்டார்.",
        "doc_context": "வாடகை ஆவணத்தில் வீட்டை கொடுப்பவர் 'வீட்டு உரிமையாளர்' என்று குறிப்பிடப்படுவார்.",
    },
    "ஒப்பந்தம்": {
        "tamil": "இரண்டு நபர்கள் அல்லது தரப்பினர் இடையே எழுத்தில் செய்யப்படும் உடன்படிக்கை",
        "example": "வீடு வாங்க விற்பனையாளர் மற்றும் வாங்குபவர் இடையே ஒப்பந்தம் செய்யப்பட்டது.",
        "doc_context": "ஒப்பந்தம் சட்டரீதியான ஆவணம். இதை மீறினால் நீதிமன்றம் போகலாம்.",
        "note": "ஸ்டாம்ப் பேப்பரில் எழுதி பதிவு செய்தால் மட்டுமே முழு சட்ட பாதுகாப்பு கிடைக்கும்."
    },
    "சாட்சி": {
        "tamil": "ஒரு நிகழ்ச்சி நடந்தது என்று கண்டு உறுதி செய்யும் நபர்",
        "example": "ஒப்பந்தத்தில் இரண்டு சாட்சிகள் கையொப்பமிட்டனர்.",
        "doc_context": "முக்கியமான ஆவணங்களில் 2 சாட்சிகள் கையொப்பமிட வேண்டும் — இல்லையென்றால் ஆவணம் சட்டரீதியாக பலவீனமாகலாம்.",
    },
    "தேதி": {
        "tamil": "ஒரு நிகழ்ச்சி நடந்த அல்லது ஆவணம் எழுதப்பட்ட நாள்",
        "example": "இந்த ஒப்பந்தம் 17 மே 2024 தேதியில் செய்யப்பட்டது.",
        "doc_context": "ஆவணத்தில் தேதி மிக முக்கியம் — இந்த நாளிலிருந்தே சட்டம் செல்லுபடியாகும்.",
    },
    "கையொப்பம்": {
        "tamil": "ஒரு ஆவணத்தில் நீங்கள் ஒப்புதல் அளிக்கும் கை எழுத்து",
        "example": "ஆவணத்தில் கையொப்பமிட்டார்.",
        "doc_context": "கையொப்பமிட்ட ஆவணம் சட்டரீதியான ஒப்பந்தம். படிக்காமல் கையொப்பமிடாதீர்கள்.",
        "note": "படிக்காமல் கையொப்பமிடாதீர்கள் — அது மிகவும் ஆபத்தானது."
    },
    "சுமார்": {
        "tamil": "தோராயமாக / கிட்டத்தட்ட என்று பொருள் — சரியான எண்ணிக்கை இல்லாமல் மதிப்பிடும்போது சொல்வார்கள்",
        "example": "சுமார் 40 வயது என்று ஆவணத்தில் குறிப்பிடப்பட்டுள்ளது.",
        "doc_context": "ஆவணத்தில் 'சுமார் வயது' என்றால் சரியான வயது தெரியாதபோது மதிப்பீடு செய்வார்கள்.",
    },
    "வயது": {
        "tamil": "ஒரு நபர் பிறந்தது முதல் இப்போது வரை ஆன ஆண்டுகளின் எண்ணிக்கை",
        "example": "விண்ணப்பதாரர் வயது 35.",
        "doc_context": "ஆவணத்தில் வயது குறிப்பிட வேண்டும் — பிறப்பு சான்றிதழ் வைத்திருங்கள்.",
    },
    "முகவரி": {
        "tamil": "ஒருவர் வசிக்கும் இடத்தின் விவரம் — வீட்டு எண், தெரு, நகரம்",
        "example": "விண்ணப்பதாரர் முகவரி: 12, மெயின் ரோடு, சென்னை - 600001.",
        "doc_context": "ஆவணங்களில் முழு முகவரி சரியாக எழுத வேண்டும். தவறான முகவரியால் ஆவணம் நிராகரிக்கப்படலாம்.",
    },
    "பின்கோடு": {
        "tamil": "ஒரு இடத்தை அடையாளம் காட்டும் 6 இலக்க அஞ்சல் எண்",
        "example": "சென்னை மைலாப்பூரின் பின்கோடு 600004.",
        "doc_context": "தபால் மற்றும் அரசு ஆவணங்களில் பின்கோடு கட்டாயம் தேவை.",
    },
    "திரு": {
        "tamil": "ஆண்களுக்கு பெயருக்கு முன் வரும் மரியாதை வார்த்தை — Mr. என்பதன் தமிழ்",
        "example": "திரு. குமார் கையொப்பமிட்டார்.",
        "doc_context": "ஆவணத்தில் திரு / திருமதி என்று தெளிவாக குறிப்பிட வேண்டும்.",
    },
    "திருமதி": {
        "tamil": "திருமணமான பெண்களுக்கு பெயருக்கு முன் வரும் மரியாதை வார்த்தை — Mrs. என்பதன் தமிழ்",
        "example": "திருமதி. லட்சுமி ஆவணத்தில் கையொப்பமிட்டார்.",
        "doc_context": "திருமணமான பெண்ணுக்கு திருமதி, திருமணமாகாதவருக்கு செல்வி என்று குறிப்பிடுவார்கள்.",
    },
    "செல்வி": {
        "tamil": "திருமணமாகாத பெண்களுக்கு பெயருக்கு முன் வரும் மரியாதை வார்த்தை — Miss என்பதன் தமிழ்",
        "example": "செல்வி. மீனாட்சி விண்ணப்பம் சமர்ப்பித்தார்.",
        "doc_context": "ஆவணத்தில் திருமண நிலைக்கு ஏற்ப திருமதி அல்லது செல்வி குறிப்பிட வேண்டும்.",
    },
    "மகன்": {
        "tamil": "ஒருவரின் ஆண் பிள்ளை",
        "example": "இவர் திரு. ராமசாமியின் மகன்.",
        "doc_context": "ஆவணத்தில் 'யாருடைய மகன்' என்று குறிப்பிடுவது அடையாளத்திற்கு உதவும்.",
    },
    "மகள்": {
        "tamil": "ஒருவரின் பெண் பிள்ளை",
        "example": "இவர் திருமதி. கமலாவின் மகள்.",
        "doc_context": "ஆவணத்தில் குடும்ப உறவு குறிப்பிட வேண்டும்.",
    },
    "மனைவி": {
        "tamil": "திருமணமான ஆணின் துணைவியார் / உடன்வாழ்பவர்",
        "example": "திரு. குமாரின் மனைவி திருமதி. கவிதா.",
        "doc_context": "சொத்து ஆவணங்களில் மனைவியின் பெயரும் சேர்க்கப்படுவது நல்லது.",
    },
    "கணவர்": {
        "tamil": "திருமணமான பெண்ணின் துணைவர்",
        "example": "திருமதி. கவிதாவின் கணவர் திரு. குமார்.",
        "doc_context": "சொத்து ஆவணத்தில் கணவர் / மனைவி பெயர் குறிப்பிடப்படும்.",
    },
    "தரப்பினர்": {
        "tamil": "ஒப்பந்தத்தில் பங்கு பெறும் ஒவ்வொருவரும் — ஒப்பந்தத்தில் இருக்கும் இரண்டு அல்லது அதிகமான நபர்கள்",
        "example": "இந்த ஒப்பந்தத்தில் இரு தரப்பினரும் ஒப்புக்கொண்டனர்.",
        "doc_context": "ஒப்பந்தத்தில் 'முதல் தரப்பு' மற்றும் 'இரண்டாம் தரப்பு' என்று குறிப்பிடுவார்கள்.",
    },
    "முதல் தரப்பு": {
        "tamil": "ஒப்பந்தத்தில் முதலில் குறிப்பிடப்படும் நபர் அல்லது நிறுவனம் — பொதுவாக விற்பவர் அல்லது வீட்டு உரிமையாளர்",
        "example": "முதல் தரப்பினர் திரு. ராமசாமி — வீட்டை வாடகைக்கு கொடுப்பவர்.",
        "doc_context": "ஒப்பந்த ஆவணத்தில் முதலில் பெயர் வருபவர் 'முதல் தரப்பு'.",
    },
    "இரண்டாம் தரப்பு": {
        "tamil": "ஒப்பந்தத்தில் இரண்டாவதாக குறிப்பிடப்படும் நபர் — பொதுவாக வாங்குபவர் அல்லது வாடகைக்கு எடுப்பவர்",
        "example": "இரண்டாம் தரப்பினர் திரு. கிருஷ்ணன் — வீட்டை வாடகைக்கு எடுப்பவர்.",
        "doc_context": "ஒப்பந்தத்தில் இரண்டாவதாக பெயர் வருபவர் 'இரண்டாம் தரப்பு'.",
    },
    "ஆம்": {
        "tamil": "ஒப்புதல் தெரிவிக்கும் வார்த்தை — 'yes' என்பதன் தமிழ்",
        "example": "ஆம், இந்த ஒப்பந்தம் சரிதான்.",
        "doc_context": "ஆவணத்தில் 'ஆம்' என்று வந்தால் முன்பு சொன்னதை ஒப்புக்கொள்கிறோம் என்று பொருள்.",
    },
    "இல்லை": {
        "tamil": "மறுப்பை தெரிவிக்கும் வார்த்தை — 'no' என்பதன் தமிழ்",
        "example": "இந்த நிலத்தில் வேறு யாருக்கும் உரிமை இல்லை.",
        "doc_context": "ஆவணத்தில் 'இல்லை' என்று வந்தால் அந்த விஷயம் இல்லை என்று உறுதிப்படுத்துகிறார்கள்.",
    },
    "மேற்கண்ட": {
        "tamil": "இதற்கு மேலே குறிப்பிட்டது — 'மேலே சொன்னது' என்று பொருள்",
        "example": "மேற்கண்ட விவரங்கள் சரியானவை.",
        "doc_context": "ஆவணத்தில் 'மேற்கண்ட' என்று வந்தால் அதற்கு முன்பு எழுதியவற்றை குறிக்கும்.",
    },
    "கீழ்க்கண்ட": {
        "tamil": "இதற்கு கீழே குறிப்பிடப்பட்டது — 'கீழே சொன்னது' என்று பொருள்",
        "example": "கீழ்க்கண்ட விதிமுறைகளை பின்பற்ற வேண்டும்.",
        "doc_context": "ஆவணத்தில் 'கீழ்க்கண்ட' என்றால் அடுத்து வரும் விவரங்களை குறிக்கும்.",
    },
    "நடைமுறை": {
        "tamil": "இப்போது பயன்படுத்தப்படும் வழிமுறை அல்லது செயல்முறை",
        "example": "புதிய நடைமுறைப்படி விண்ணப்பிக்க வேண்டும்.",
        "doc_context": "ஆவணத்தில் நடைமுறை என்றால் இப்போது செல்லுபடியாகும் வழிமுறை.",
    },
    "விதிமுறை": {
        "tamil": "பின்பற்ற வேண்டிய கட்டாய நியதிகள் அல்லது சட்டங்கள்",
        "example": "ஒப்பந்தத்தின் விதிமுறைகளை மீறினால் நடவடிக்கை எடுக்கப்படும்.",
        "doc_context": "ஆவணத்தில் விதிமுறை என்பது கட்டாயம் பின்பற்ற வேண்டியது.",
    },
    "நிபந்தனை": {
        "tamil": "ஒப்பந்தத்தில் கட்டாயம் பின்பற்ற வேண்டிய நிலை அல்லது கட்டுப்பாடு",
        "example": "இந்த நிபந்தனைக்கு உட்பட்டு நிலம் வழங்கப்படும்.",
        "doc_context": "நிபந்தனை மீறினால் ஒப்பந்தம் ரத்தாகலாம்.",
    },
    "ரத்து": {
        "tamil": "ஒரு முடிவை அல்லது ஒப்பந்தத்தை செல்லாததாக்குவது — cancel செய்வது",
        "example": "கட்டணம் கட்டாததால் விண்ணப்பம் ரத்து செய்யப்பட்டது.",
        "doc_context": "ஆவணத்தில் ரத்து என்றால் அந்த ஒப்பந்தம் அல்லது அனுமதி இனி செல்லாது.",
    },
    "செல்லுபடியாகும்": {
        "tamil": "சட்டரீதியாக ஏற்றுக்கொள்ளப்படும் — valid என்று பொருள்",
        "example": "இந்த சான்றிதழ் ஒரு வருடம் செல்லுபடியாகும்.",
        "doc_context": "ஆவணம் செல்லுபடியான காலத்திற்கு மட்டுமே பயன்படுத்தலாம்.",
    },
    "காலக்கெடு": {
        "tamil": "ஒரு வேலையை முடிக்க அல்லது விண்ணப்பிக்க கடைசி நாள்",
        "example": "விண்ணப்பிக்க காலக்கெடு 31 மார்ச் 2024.",
        "doc_context": "காலக்கெடு தாண்டினால் விண்ணப்பம் ஏற்கப்படாது.",
        "note": "காலக்கெடுவை மீறாதீர்கள் — நீட்டிப்பு கிடைக்காது."
    },
    "முன்பணம்": {
        "tamil": "ஒப்பந்தம் செய்யும்போது முன்கூட்டியே கொடுக்கும் பணம் — advance என்று ஆங்கிலத்தில் சொல்வார்கள்",
        "example": "வீட்டிற்கு 50,000 ரூபாய் முன்பணம் கொடுத்தார்.",
        "doc_context": "முன்பணம் கொடுத்தால் ரசீது வாங்க வேண்டும். ஒப்பந்தம் ரத்தானால் முன்பணம் திரும்ப கிடைக்கும்.",
    },
    "நஷ்டஈடு": {
        "tamil": "ஒருவரால் ஏற்பட்ட நஷ்டத்திற்கு கொடுக்கப்படும் பணம்",
        "example": "ஒப்பந்தம் மீறினால் நஷ்டஈடு கொடுக்க வேண்டும்.",
        "doc_context": "நஷ்டஈடு தொகை ஒப்பந்தத்திலேயே குறிப்பிடப்படும்.",
    },
    "செய்யப்பட்டது": {
        "tamil": "ஒரு செயல் முடிக்கப்பட்டது / நிறைவேற்றப்பட்டது என்று பொருள்",
        "example": "இந்த ஒப்பந்தம் 17 மே 2024 அன்று செய்யப்பட்டது.",
        "doc_context": "ஆவணத்தில் 'செய்யப்பட்டது' என்பது அந்த செயல் நடந்தது என்று உறுதிப்படுத்துகிறது.",
    },
    "வழங்கப்படும்": {
        "tamil": "கொடுக்கப்படும் / தரப்படும் என்று பொருள்",
        "example": "அனுமதி வழங்கப்படும்.",
        "doc_context": "ஆவணத்தில் 'வழங்கப்படும்' என்றால் அரசு அல்லது நிறுவனம் அதை கொடுக்கும் என்று பொருள்.",
    },
    "கட்டாயம்": {
        "tamil": "தப்பிக்க முடியாதது — must / compulsory என்று பொருள்",
        "example": "சான்றிதழ் சமர்ப்பிப்பது கட்டாயம்.",
        "doc_context": "ஆவணத்தில் 'கட்டாயம்' என்றால் இதை செய்யாமல் விட முடியாது.",
    },
    "அதாவது": {
        "tamil": "அதாவது என்றால் 'என்னவெனில்' அல்லது 'விளக்கமாக சொன்னால்' என்று பொருள்",
        "example": "இந்த சொத்தின் மதிப்பு, அதாவது சந்தை விலை, 50 லட்சம்.",
        "doc_context": "ஆவணத்தில் 'அதாவது' வந்தால் முன்பு சொன்னதை விளக்கப்போகிறார்கள்.",
    },
    "மேலும்": {
        "tamil": "கூடுதலாக / இதோடு சேர்த்து என்று பொருள் — furthermore என்பதன் தமிழ்",
        "example": "மேலும், இந்த ஒப்பந்தம் 11 மாத காலத்திற்கு செல்லும்.",
        "doc_context": "ஆவணத்தில் 'மேலும்' என்றால் இன்னும் கூடுதல் விதிமுறைகள் வருகின்றன என்று பொருள்.",
    },
    "அல்லது": {
        "tamil": "இரண்டில் ஒன்றை தேர்வு செய்யும்போது பயன்படுத்தும் வார்த்தை — 'or' என்பதன் தமிழ்",
        "example": "பணமாக அல்லது காசோலையாக கட்டலாம்.",
        "doc_context": "ஒப்பந்தத்தில் 'அல்லது' என்றால் இரண்டு விருப்பங்களில் ஒன்றை தேர்வு செய்யலாம்.",
    },
    "மற்றும்": {
        "tamil": "இரண்டையும் சேர்த்து குறிக்கும் வார்த்தை — 'and' என்பதன் தமிழ்",
        "example": "விற்பவர் மற்றும் வாங்குபவர் இருவரும் கையொப்பமிட வேண்டும்.",
        "doc_context": "ஆவணத்தில் 'மற்றும்' என்றால் இரண்டுமே கட்டாயம் என்று பொருள்.",
    },
    "இதன்படி": {
        "tamil": "இந்த ஒப்பந்தம் அல்லது ஆவணத்தில் சொன்னதன்படி என்று பொருள்",
        "example": "இதன்படி வாடகை 1ஆம் தேதி கட்ட வேண்டும்.",
        "doc_context": "ஆவணத்தில் 'இதன்படி' என்றால் இந்த விதிமுறையை பின்பற்ற வேண்டும் என்று பொருள்.",
    },
    "பதிவு செய்யப்பட்டது": {
        "tamil": "அரசு ஆவணத்தில் சட்டரீதியாக பதிந்து வைக்கப்பட்டது",
        "example": "இந்த ஒப்பந்தம் பதிவு அலுவலகத்தில் பதிவு செய்யப்பட்டது.",
        "doc_context": "பதிவு செய்யப்பட்ட ஆவணம் மட்டுமே நீதிமன்றத்தில் முழு ஆதாரமாக ஏற்கப்படும்.",
    },
    "ஆதாரம்": {
        "tamil": "ஒரு விஷயம் உண்மை என்று நிரூபிக்க உதவும் ஆவணம் அல்லது தகவல்",
        "example": "பட்டா ஆதாரமாக சமர்ப்பிக்கவும்.",
        "doc_context": "சட்ட நடவடிக்கைக்கு ஆதாரங்கள் இல்லாமல் வழக்கு நடக்காது.",
    },
    "அறிவிக்கப்படுகிறது": {
        "tamil": "அதிகாரப்பூர்வமாக அனைவருக்கும் தெரியப்படுத்தப்படுகிறது",
        "example": "புதிய திட்டம் அறிவிக்கப்படுகிறது.",
        "doc_context": "அரசு ஒரு விஷயத்தை முறையாக தெரிவிக்கும்போது இந்த வார்த்தை பயன்படும்.",
    },
    "இணைக்கப்பட்டுள்ளது": {
        "tamil": "ஒரு ஆவணம் அல்லது விவரம் இந்த ஆவணத்தோடு சேர்க்கப்பட்டுள்ளது",
        "example": "தேவையான ஆவணங்கள் இணைக்கப்பட்டுள்ளன.",
        "doc_context": "இணைப்பு ஆவணங்கள் சரிபார்த்து சமர்ப்பிக்க வேண்டும்.",
    },
    "நகர்": {
        "tamil": "நகரம் / town — ஒரு குறிப்பிட்ட இடத்தின் பெயர் குறிக்கும் வார்த்தை",
        "example": "சென்னை நகரில் வசிக்கிறார்.",
        "doc_context": "முகவரியில் நகர் என்பது நகரத்தின் பெயரை குறிக்கும்.",
    },
    "இலவசிக்கிறார்": {
        "tamil": "வசிக்கிறார் / தங்கியிருக்கிறார் — ஒரு இடத்தில் வாழ்கிறார் என்று பொருள்",
        "example": "சென்னையில் இலவசிக்கிறார்.",
        "doc_context": "ஆவணத்தில் ஒருவரின் வசிப்பிடம் குறிப்பிடும்போது இந்த வார்த்தை வரும்.",
    },

    # ── LAND / PROPERTY ──────────────────────────────────────────────────────
    "பட்டா": {
        "tamil": "நிலத்தின் உரிமை பத்திரம் — நீங்கள் அந்த நிலத்தின் சட்டபூர்வ உரிமையாளர் என்பதை அரசு உறுதி செய்யும் ஆவணம்",
        "example": "ரமேஷிடம் அவரது நிலத்திற்கு பட்டா இருக்கிறது.",
        "doc_context": "பட்டா இல்லாமல் நிலத்தை விற்கவோ அடமானம் வைக்கவோ முடியாது.",
        "note": "பட்டாவில் உங்கள் பெயர் இல்லையென்றால் நீங்கள் சட்டபூர்வமாக உரிமையாளர் அல்ல."
    },
    "சிட்டா": {
        "tamil": "நிலத்தின் விவரங்களை கொண்ட அரசு பதிவு ஆவணம் — நிலத்தின் அளவு, வகை, உரிமையாளர் பெயர் இதில் இருக்கும்",
        "example": "சிட்டாவில் அவரது நிலத்தின் அளவு 2 ஏக்கர் என்று குறிப்பிடப்பட்டுள்ளது.",
        "doc_context": "சிட்டா என்பது நிலத்தின் பதிவு விவரங்களை கொண்ட அட்டவணை.",
    },
    "சர்வே": {
        "tamil": "நிலத்தை அளந்து எண் கொடுக்கும் அரசு நடவடிக்கை",
        "example": "இந்த நிலத்தின் சர்வே எண் 45/2.",
        "doc_context": "ஒவ்வொரு நிலத்திற்கும் ஒரு தனி சர்வே எண் இருக்கும்.",
    },
    "சர்வே எண்": {
        "tamil": "ஒவ்வொரு நிலத்திற்கும் அரசு கொடுக்கும் தனிப்பட்ட அடையாள எண்",
        "example": "சர்வே எண் 123/4 என்பது அந்த நிலத்தின் அரசு பதிவு எண்.",
        "doc_context": "நிலம் வாங்க, விற்க, அடமானம் வைக்க இந்த எண் கட்டாயம் தேவை.",
    },
    "ஏக்கர்": {
        "tamil": "நிலத்தின் அளவை குறிக்கும் அலகு — 1 ஏக்கர் = 100 சென்ட்",
        "example": "அவரிடம் 2.5 ஏக்கர் நிலம் உள்ளது.",
        "doc_context": "தமிழ்நாட்டில் நிலம் ஏக்கர் மற்றும் சென்ட்டில் அளக்கப்படுகிறது.",
    },
    "சென்ட்": {
        "tamil": "நிலத்தின் சிறிய அளவு அலகு — 100 சென்ட் = 1 ஏக்கர்",
        "example": "அவரிடம் 30 சென்ட் நிலம் உள்ளது.",
        "doc_context": "வீட்டு மனை போன்ற சிறிய நிலங்கள் பொதுவாக சென்ட்டில் அளக்கப்படும்.",
    },
    "தஹசில்": {
        "tamil": "வட்டார நிர்வாக அலுவலகம் — நிலம், சான்றிதழ் தொடர்பான அரசு பணிகள் இங்கே நடக்கும்",
        "example": "பட்டா வாங்க தஹசில் அலுவலகத்திற்கு சென்றார்.",
        "doc_context": "தஹசில்தார் என்பவர் வட்டார நிர்வாக அதிகாரி.",
    },
    "எல்லை": {
        "tamil": "நிலத்தின் ஒரு பக்கம் — வடக்கு, தெற்கு, கிழக்கு, மேற்கு எல்லை குறிக்கப்படும்",
        "example": "வடக்கு எல்லை: ரமேஷின் நிலம், தெற்கு எல்லை: அரசு சாலை.",
        "doc_context": "பட்டாவில் நான்கு திசைகளிலும் என்ன இருக்கிறது என்று எல்லை குறிப்பிடப்படும்.",
    },
    "பட்டா மாற்றம்": {
        "tamil": "நிலத்தின் உரிமை ஒருவரிடம் இருந்து மற்றொருவருக்கு சட்டரீதியாக மாறுவது",
        "example": "தந்தை இறந்த பிறகு மகன் பெயரில் பட்டா மாற்றம் செய்யப்பட்டது.",
        "doc_context": "நிலம் வாங்கும்போது, வாரிசு உரிமை கோரும்போது பட்டா மாற்றம் கட்டாயம்.",
    },
    "மானியம்": {
        "tamil": "அரசால் இலவசமாக அல்லது குறைந்த விலையில் கொடுக்கப்பட்ட நிலம் அல்லது உதவி",
        "example": "இந்த நிலம் அரசு மானியமாக கொடுக்கப்பட்டது.",
        "doc_context": "மானிய நிலங்களை சட்டப்படி குறிப்பிட்ட காலத்திற்கு விற்க முடியாது.",
        "note": "மானிய நிலம் விற்கும் முன் அரசிடம் அனுமதி வாங்க வேண்டும்."
    },
    "அடமானம்": {
        "tamil": "கடன் வாங்க சொத்தை பாதுகாப்பாக வைப்பது — கடன் திரும்ப கொடுக்காவிட்டால் சொத்து போகும்",
        "example": "வீட்டை அடமானம் வைத்து வங்கியில் கடன் வாங்கினார்.",
        "doc_context": "அடமான ஆவணம் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "note": "கடன் திரும்ப கொடுக்காவிட்டால் வங்கி சொத்தை ஏலம் போடலாம்."
    },
    "குத்தகை": {
        "tamil": "பணம் கொடுத்து குறிப்பிட்ட காலம் நிலம் அல்லது கட்டிடம் பயன்படுத்திக்கொள்வதற்கான ஒப்பந்தம்",
        "example": "விவசாயி 5 வருடத்திற்கு நிலத்தை குத்தகைக்கு எடுத்தான்.",
        "doc_context": "குத்தகை ஒப்பந்தம் எழுத்தில் செய்தால் சட்ட பாதுகாப்பு கிடைக்கும்.",
    },

    # ── GOVT / CERTIFICATE ────────────────────────────────────────────────────
    "சான்றிதழ்": {
        "tamil": "ஒரு விஷயம் உண்மை என்று அரசு உறுதி செய்யும் ஆவணம்",
        "example": "சாதி சான்றிதழ் வேலைக்கு விண்ணப்பிக்க தேவை.",
        "doc_context": "சான்றிதழ் என்பது அரசு அதிகாரி கையொப்பமிட்ட முறையான ஆவணம்.",
    },
    "அரசாணை": {
        "tamil": "அரசு அதிகாரப்பூர்வமாக பிறப்பிக்கும் ஆணை அல்லது உத்தரவு",
        "example": "இந்த திட்டம் அரசாணை எண் 150 மூலம் அனுமதிக்கப்பட்டது.",
        "doc_context": "அரசாணை (G.O.) என்பது அரசின் முறையான உத்தரவு. இதை மீற முடியாது.",
    },
    "விண்ணப்பம்": {
        "tamil": "ஒரு விஷயத்திற்காக அரசிடம் எழுத்தில் கோரும் கடிதம்",
        "example": "வீட்டுமனை பெற விண்ணப்பம் சமர்ப்பித்தார்.",
        "doc_context": "அரசு சேவைகளுக்கு விண்ணப்பம் சமர்ப்பிக்க வேண்டும். விண்ணப்ப எண் வைத்திருங்கள்.",
    },
    "வாரிசு சான்றிதழ்": {
        "tamil": "ஒருவர் இறந்த பிறகு அவரது சொத்துக்கு யார் உரிமையாளர் என்று அரசு சொல்லும் ஆவணம்",
        "example": "அப்பா இறந்த பிறகு வாரிசு சான்றிதழ் வாங்கி சொத்து பெற்றனர்.",
        "doc_context": "வாரிசு சான்றிதழ் இல்லாமல் இறந்தவரின் சொத்தை சட்டரீதியாக கோர முடியாது.",
    },
    "நோட்டரி": {
        "tamil": "ஆவணங்களை சட்டரீதியாக சான்றளிக்கும் அரசால் நியமிக்கப்பட்ட நபர்",
        "example": "நோட்டரி ஆவணத்தை சான்றளித்தார்.",
        "doc_context": "நோட்டரி சான்றளித்த ஆவணங்கள் சட்டரீதியாக செல்லுபடியாகும்.",
    },
    "ஸ்டாம்ப் டியூட்டி": {
        "tamil": "சொத்து பதிவு செய்யும்போது அரசுக்கு கட்ட வேண்டிய வரி",
        "example": "வீடு வாங்கும்போது 7% ஸ்டாம்ப் டியூட்டி கட்ட வேண்டும்.",
        "doc_context": "ஸ்டாம்ப் டியூட்டி கட்டாவிட்டால் ஆவணம் செல்லாது.",
    },
    "ரசீது": {
        "tamil": "பணம் கட்டியதற்கான அல்லது ஆவணம் கொடுத்ததற்கான ஆதாரக் கடிதம்",
        "example": "கட்டணம் கட்டிய பிறகு ரசீது வாங்கினார்.",
        "doc_context": "ஒவ்வொரு பணம் கட்டலுக்கும் ரசீது வாங்கி வைத்திருங்கள்.",
        "note": "ரசீது இல்லாமல் கட்டினேன் என்று நிரூபிக்க முடியாது."
    },
    "நகல்": {
        "tamil": "ஒரு ஆவணத்தின் நகல் அல்லது copy",
        "example": "பட்டாவின் நகல் தஹசில் அலுவலகத்தில் கிடைக்கும்.",
        "doc_context": "அசல் ஆவணம் இல்லாதபோது சான்றளிக்கப்பட்ட நகல் பயன்படும்.",
    },

    # ── LEGAL ─────────────────────────────────────────────────────────────────
    "பதிவு": {
        "tamil": "சொத்து உரிமை அரசு ஆவணத்தில் பதிவு செய்யப்படுவது",
        "example": "வீடு வாங்கிய பிறகு பதிவு அலுவலகத்தில் பதிவு செய்தனர்.",
        "doc_context": "சொத்து பதிவு இல்லாமல் உரிமை சட்டரீதியாக உங்களுக்கு மாறாது.",
        "note": "பதிவு கட்டணம் மற்றும் ஸ்டாம்ப் டியூட்டி கட்ட வேண்டும்."
    },
    "வழக்கு": {
        "tamil": "நீதிமன்றத்தில் தீர்வு காண தாக்கல் செய்யப்படும் புகார் அல்லது வேண்டுகோள்",
        "example": "நிலம் சம்பந்தமாக நீதிமன்றத்தில் வழக்கு தாக்கல் செய்தார்.",
        "doc_context": "வழக்கு தாக்கல் ஆனால் வழக்கு எண் வைத்திருங்கள்.",
    },
    "தீர்ப்பு": {
        "tamil": "நீதிமன்றம் வழக்கில் கொடுக்கும் இறுதி முடிவு",
        "example": "நீதிமன்றம் வாதிக்கு சாதகமாக தீர்ப்பு அளித்தது.",
        "doc_context": "தீர்ப்புக்கு எதிராக உயர் நீதிமன்றத்தில் மேல்முறையீடு செய்யலாம்.",
    },
    "உத்தரவு": {
        "tamil": "நீதிமன்றம் அல்லது அரசு கொடுக்கும் கட்டளை",
        "example": "நீதிமன்றம் நிலத்தை திரும்ப கொடுக்க உத்தரவிட்டது.",
        "doc_context": "உத்தரவை கட்டாயம் பின்பற்ற வேண்டும். மீறினால் நீதிமன்ற அவமதிப்பு வழக்கு வரும்.",
    },
    "அஃபிடவிட்": {
        "tamil": "சத்தியப்பிரமாணம் செய்து கொடுக்கும் எழுத்து ஆவணம் — இது தவறாயின் சட்ட நடவடிக்கை வரும்",
        "example": "நோட்டரியிடம் அஃபிடவிட் கொடுத்தார்.",
        "doc_context": "அஃபிடவிட் தவறான தகவல் கொடுத்தால் பொய் சாட்சி வழக்கு வரும்.",
    },
    "கையகப்படுத்தல்": {
        "tamil": "அரசு பொது நலனுக்காக தனியார் நிலத்தை எடுத்துக்கொள்வது",
        "example": "சாலை அமைக்க அரசு நிலத்தை கையகப்படுத்தியது.",
        "doc_context": "கையகப்படுத்தும்போது சந்தை மதிப்பில் இழப்பீடு கொடுப்பது கட்டாயம்.",
        "note": "இழப்பீடு போதுமானதாக இல்லையென்றால் நீதிமன்றம் போகலாம்."
    },
    "இழப்பீடு": {
        "tamil": "நஷ்டத்திற்கு ஈடாக கொடுக்கப்படும் பணம் அல்லது சொத்து",
        "example": "நிலம் கையகப்படுத்தப்பட்டதால் இழப்பீடு கொடுக்கப்பட்டது.",
        "doc_context": "இழப்பீடு சந்தை மதிப்பை விட அதிகமாக இருக்க வேண்டும் என்று சட்டம் சொல்கிறது.",
    },
    "நிராகரிப்பு": {
        "tamil": "கோரிக்கையை மறுக்கிறோம் என்று அரசு சொல்வது",
        "example": "போதுமான ஆவணங்கள் இல்லாததால் விண்ணப்பம் நிராகரிக்கப்பட்டது.",
        "doc_context": "நிராகரிக்கப்பட்டால் காரணம் கேட்டு மேல்முறையீடு செய்யலாம்.",
    },
    "வரி": {
        "tamil": "அரசுக்கு கட்டாயமாக கட்ட வேண்டிய பணம்",
        "example": "சொத்து வரி ஒவ்வொரு வருடமும் கட்ட வேண்டும்.",
        "doc_context": "வரி கட்டாவிட்டால் அபராதம் மற்றும் சட்ட நடவடிக்கை வரும்.",
    },
    "நிலுவை": {
        "tamil": "இன்னும் கட்டப்படாத அல்லது முடிவு செய்யப்படாத பணம் அல்லது வேலை",
        "example": "கடந்த வருட வரி நிலுவையில் உள்ளது.",
        "doc_context": "நிலுவை தொகை கட்டாவிட்டால் அபராதம் சேரும்.",
    },
    "கட்டணம்": {
        "tamil": "சேவைக்காக செலுத்த வேண்டிய பணம்",
        "example": "பதிவுக்கு கட்டணம் கட்ட வேண்டும்.",
        "doc_context": "அரசு சேவைகளுக்கு நிர்ணயிக்கப்பட்ட கட்டணம் செலுத்த வேண்டும்.",
    },
    "மனு": {
        "tamil": "குறை தீர்க்க அல்லது ஒரு விஷயத்திற்கு அரசிடம் கோரும் கடிதம்",
        "example": "நிலம் சம்பந்தமாக கலெக்டரிடம் மனு சமர்ப்பித்தார்.",
        "doc_context": "மனு கொடுத்த பிறகு ரசீது வாங்கவும். மனு எண் வைத்திருங்கள்.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TYPE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
DOC_TYPES = {
    "பட்டா / நிலம்":  ["பட்டா","சிட்டா","survey","சர்வே","நிலம்","ஏக்கர்","chitta"],
    "வாடகை ஒப்பந்தம்": ["வாடகை","குடியிருப்பவர்","வீட்டு உரிமையாளர்","rent","lease","வாடகைக்கு"],
    "அரசாணை (G.O.)":  ["G.O.","அரசாணை","government order","செயல்முறை"],
    "சான்றிதழ்":       ["சான்றிதழ்","certificate","பிறப்பு","சாதி","வருமானம்"],
    "சட்ட ஆவணம்":     ["மனு","petition","court","நீதிமன்றம்","வழக்கு","affidavit"],
}

def detect_doc_type(text: str) -> str:
    t = text.lower()
    for dtype, kws in DOC_TYPES.items():
        if any(k.lower() in t for k in kws):
            return dtype
    return "அரசு ஆவணம்"


# ══════════════════════════════════════════════════════════════════════════════
# SUFFIX + SANDHI ENGINE
# ══════════════════════════════════════════════════════════════════════════════
SUFFIXES = [
    "ப்படுகிறது","ப்படுகின்றது","க்கப்படும்","ப்படும்","ப்பட்டது",
    "படுத்தப்படும்","வைக்கப்படும்",
    "யினால்","வதினால்","தினால்","டினால்","றினால்","னினால்","இனால்","ினால்","னால்","ால்",
    "ன்றனர்","னார்கள்","னார்","ட்டார்கள்","ட்டார்","தார்கள்","தார்",
    "ட்டேன்","தேன்","டேன்","ினான்","ினாள்","னான்","னாள்",
    "த்தான்","த்தாள்","ிட்டான்","ிட்டாள்",
    "கிறார்கள்","கிறார்","கிறான்","கிறாள்","கிறோம்",
    "கின்றார்","கின்றான்","கிறது","கின்றது",
    "வார்கள்","வார்","வான்","வாள்","வோம்","பார்","பான்","வீர்கள்",
    "வதற்கு","படுவது","வதை","தலை","கல்","வது",
    "த்திலிருந்து","த்தினால்","த்துடன்","த்தோடு",
    "த்தில்","த்தை","த்தின்","த்துக்கு","த்தோ",
    "இல்லாமல்","இருந்தால்","இருந்து","உடைய","யுடன்","உடன்",
    "என்று","ஆகும்","ஆனது","ஆல்","ஆக","ஆன",
    "யில்","யை","யின்","யிடம்","கள்","இல்","ஐ","கு",
    "க்கான","ிய","்ற","்த","ின்","இன்",
]
SANDHI = [("ந்த","ந்தம்"),("ட்ட","ட்டம்"),("க்க","க்கம்"),("ல்ல","ல்"),("ன்ன","ன்னம்")]

def _strip(w):
    for s in SUFFIXES:
        if w.endswith(s) and len(w) > len(s)+1:
            return w[:-len(s)]
    return None

def _sandhi(w): return [w[:-len(t)]+r for t,r in SANDHI if w.endswith(t)]
def _variants(w):
    sw = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in sw if a in w and w.replace(a,b,1)!=w]

def get_candidates(word: str) -> list:
    seen, res = set(), []
    def add(w):
        if w and w not in seen: seen.add(w); res.append(w)
    add(word)
    cur = word
    for _ in range(6):
        nxt = _strip(cur)
        if not nxt: break
        add(nxt)
        for s in _sandhi(nxt): add(s)
        for v in _variants(nxt): add(v)
        cur = nxt
    for v in _variants(word): add(v)
    return res


# ══════════════════════════════════════════════════════════════════════════════
# DICTIONARY + ONLINE LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
def dict_lookup(word: str):
    for c in get_candidates(word):
        if c in GOVT_DICT:
            return GOVT_DICT[c], c
    return None, None

def src_mymemory(word: str):
    try:
        r = requests.get("https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"}, timeout=4)
        if r.status_code == 200:
            t = r.json().get("responseData",{}).get("translatedText","")
            if t and not is_transliteration(word, t) and len(t.strip())>1:
                return t.strip()
    except: pass
    return None

def src_wiktionary(word: str):
    try:
        r = requests.get(
            f"https://ta.wiktionary.org/api/rest_v1/page/definition/{requests.utils.quote(word)}",
            timeout=3)
        if r.status_code == 200:
            data = r.json()
            for key in data:
                entries = data[key]
                if isinstance(entries, list) and entries:
                    raw = entries[0].get("definitions",[{}])[0].get("definition","")
                    clean = re.sub(r"<[^>]+>","",raw).strip()
                    if clean and len(clean)>3:
                        return clean
    except: pass
    return None

def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and not is_transliteration(word, t):
            return t.strip()
    except: pass
    return None

def find_context(text: str, word: str):
    for c in get_candidates(word):
        for sent in re.split(r'(?<=[.!?\n])\s*', text):
            s = sent.strip()
            if c in s and len(s)>5:
                return s
        idx = text.find(c)
        if idx >= 0:
            return "…"+text[max(0,idx-80):min(len(text),idx+len(c)+80)].strip()+"…"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str="", doc_type: str="அரசு ஆவணம்") -> dict:
    w         = clean_word(word)  # strip OCR noise first
    cands     = get_candidates(w)
    dict_res, dict_root = dict_lookup(w)
    ctx       = find_context(doc_text, w) if doc_text else None
    online    = None
    root_used = dict_root or w

    if not dict_res:
        # Try original, then each stripped root
        for candidate in [w] + cands[1:]:
            t = src_mymemory(candidate)
            if t: root_used = candidate; online = t; break
        if not online:
            for candidate in cands:
                t = src_wiktionary(candidate)
                if t: root_used = candidate; online = t; break
        if not online:
            t = src_google(w)
            if t: online = t

    return {
        "word":    word,          # original as typed
        "clean":   w,             # after noise removal
        "root":    root_used,
        "dict":    dict_res,
        "online":  online,
        "context": ctx,
        "found":   bool(dict_res or online),
        "tried":   cands,
    }


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word):
    try:
        w = clean_word(word)
        buf=io.BytesIO(); gTTS(text=w,lang="ta",slow=False).write_to_fp(buf); buf.seek(0); return buf
    except: return None

# ── OCR ───────────────────────────────────────────────────────────────────────
def preprocess(img):
    img=img.convert("L"); w,h=img.size
    if w<1800: sc=1800/w; img=img.resize((int(w*sc),int(h*sc)),Image.LANCZOS)
    img=ImageEnhance.Contrast(img).enhance(2.2)
    img=ImageEnhance.Sharpness(img).enhance(2.0)
    arr=np.array(img)
    arr=((arr>int(arr.mean()*0.85))*255).astype(np.uint8)
    return Image.fromarray(arr)

def clean_text(raw):
    lines=raw.splitlines(); out=[]
    for ln in lines:
        ln=re.sub(r"[|}{\\~`_]","",ln).strip()
        ln=re.sub(r" {2,}"," ",ln)
        if not ln:
            if out and out[-1]!="": out.append("")
            continue
        out.append(ln)
    merged,i=[],0
    while i<len(out):
        if out[i]=="": merged.append(""); i+=1; continue
        cur=out[i]
        while(i+1<len(out) and out[i+1]!="" and
              not cur.rstrip().endswith((".",":",")","?","!","।")) and len(cur)>8):
            i+=1; cur+=" "+out[i]
        merged.append(cur); i+=1
    return "\n".join(merged).strip()

def ocr_image(img): return clean_text(pytesseract.image_to_string(preprocess(img),config=r"--oem 3 --psm 6 -l tam+eng"))
def extract_pdf(f):
    ts=[]
    with pdfplumber.open(f) as pdf:
        for p in pdf.pages:
            t=p.extract_text()
            if t: ts.append(clean_text(t))
    return "\n\n".join(ts)

def is_tamil(w): return bool(re.search(r"[\u0B80-\u0BFF]",w))
def tokenize(t): return re.findall(r"[\u0B80-\u0BFF]+",t)

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("text",""),("word",""),("doc_type","அரசு ஆவணம்")]:
    st.session_state.setdefault(k,v)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 தமிழ் அரசு ஆவண வாசகன்</h1>
  <p>Upload PDF or image · Extract text · Search any Tamil word · Get exact Tamil meaning · 100% free</p>
</div>
""", unsafe_allow_html=True)

t_reader, t_deploy = st.tabs(["📄 ஆவண வாசகன்", "🚀 GitHub → Streamlit Cloud Guide"])

with t_reader:
    left, right = st.columns([3,2], gap="large")

    with left:
        st.markdown('<div class="slabel">படி 1 — ஆவணம் பதிவேற்றவும்</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("உரை எடுக்கிறோம்…"):
                if uploaded.type=="application/pdf":
                    text=extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("OCR இயக்குகிறோம்…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs=convert_from_bytes(uploaded.getvalue(),first_page=1,last_page=1)
                            text=ocr_image(imgs[0]) if imgs else ""
                        except Exception as e: st.error(f"OCR பிழை: {e}"); text=""
                else:
                    text=ocr_image(Image.open(uploaded))
                st.session_state.text=text
                st.session_state.doc_type=detect_doc_type(text)

        if st.session_state.text:
            st.markdown(f'<div class="doc-chip">📋 ஆவண வகை: {st.session_state.doc_type}</div>', unsafe_allow_html=True)
            st.markdown('<div class="slabel">படி 2 — ஆவணம் படிக்கவும்</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 புரியாத சொல்லை கீழே dropdown-ல் தேர்வு செய்யுங்கள் அல்லது வலதில் தட்டச்சு செய்யுங்கள்</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)
            tw=sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t)>1})
            if tw:
                st.markdown('<div class="slabel" style="margin-top:.7rem">சொல் தேர்வு</div>', unsafe_allow_html=True)
                pick=st.selectbox("pick",["— தேர்வு செய்யவும் —"]+tw,label_visibility="collapsed",key="pick")
                if pick!="— தேர்வு செய்யவும் —": st.session_state.word=pick
        else:
            st.info("மேலே PDF அல்லது படம் பதிவேற்றவும்.")

    with right:
        st.markdown('<div class="slabel">சொல் பொருள்</div>', unsafe_allow_html=True)
        typed=st.text_input("தமிழ் சொல்:", placeholder="உதா: இனிமேல், உரிமையாளர், ஒப்பந்தம்", key="typed")
        if typed: st.session_state.word=typed.strip()

        w=st.session_state.word.strip()

        if w and is_tamil(clean_word(w)):
            with st.spinner(f"பொருள் தேடுகிறோம்…"):
                res=lookup(w, st.session_state.text, st.session_state.doc_type)
                audio=speak(w)

            cleaned_display = res["clean"]
            root_note = f"(அடி வடிவம்: {res['root']})" if res["root"]!=cleaned_display else ""

            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{cleaned_display}</div>
              <div class="mroot">{root_note}</div>
            """, unsafe_allow_html=True)

            if res["found"]:
                d=res["dict"]
                if d:
                    st.markdown(f'<div class="sec s-tamil"><div class="sec-head">📖 தமிழ் பொருள்</div><div class="sec-body">{d["tamil"]}</div></div>', unsafe_allow_html=True)
                    if d.get("example"):
                        st.markdown(f'<div class="sec s-example"><div class="sec-head">✏️ எடுத்துக்காட்டு வாக்கியம்</div><div class="sec-body">{d["example"]}</div></div>', unsafe_allow_html=True)
                    if d.get("doc_context"):
                        st.markdown(f'<div class="sec s-doc"><div class="sec-head">📋 அரசு ஆவணத்தில் பொருள்</div><div class="sec-body">{d["doc_context"]}</div></div>', unsafe_allow_html=True)
                    if d.get("note"):
                        st.markdown(f'<div class="sec s-note"><div class="sec-head">⚠️ கவனிக்க வேண்டியது</div><div class="sec-body">{d["note"]}</div></div>', unsafe_allow_html=True)
                elif res["online"]:
                    st.markdown(f'<div class="sec s-online"><div class="sec-head">🔤 பொருள் (ஆன்லைன்)</div><div class="sec-body">{res["online"]}</div></div>', unsafe_allow_html=True)

                if res["context"]:
                    st.markdown(f'<div class="sec s-note"><div class="sec-head">📄 உங்கள் ஆவணத்தில்</div><div class="sec-body">{res["context"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="notfound">⚠️ <strong>{cleaned_display}</strong> — பொருள் கிடைக்கவில்லை.<br>{len(res["tried"])} வடிவங்கள் தேடப்பட்டன. சிறிய வடிவில் முயற்சிக்கவும்.</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            if audio:
                st.markdown("**🔊 உச்சரிப்பு**")
                st.audio(audio, format="audio/mp3")

            with st.expander("🔍 தேடிய வடிவங்கள்"):
                for i,c in enumerate(res["tried"],1): st.write(f"{i}. `{c}`")

        elif w:
            cw=clean_word(w)
            if cw and not is_tamil(cw):
                st.info("தமிழ் எழுத்தில் சொல்லை தட்டச்சு செய்யவும்.")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-family:'Noto Sans Tamil',sans-serif;font-size:1rem;margin-top:.4rem;color:#999;">
                மேலே சொல்லை தட்டச்சு செய்யுங்கள்<br>அல்லது ஆவணத்தில் இருந்து தேர்வு செய்யுங்கள்
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("📚 உள்ளமைக்கப்பட்ட தமிழ் அகராதி + MyMemory + Google Translate + Tamil Wiktionary | 100% இலவசம்")

with t_deploy:
    st.markdown("## 🚀 GitHub → Streamlit Cloud (இலவசம் — API key தேவையில்லை)")
    st.info("✅ இந்த version-க்கு எந்த API key-உம் தேவையில்லை. உடனே deploy ஆகும்.")
    st.markdown("""
    <div class="step"><span class="num">1</span><strong>GitHub account</strong> → <a href="https://github.com" target="_blank">github.com</a> → Sign up (இலவசம்)</div>
    <div class="step"><span class="num">2</span><strong>New repository</strong> → Name: <code>tamil-doc-reader</code> | Public → Create</div>
    <div class="step"><span class="num">3</span><strong>3 files upload</strong>: <code>app.py</code>, <code>requirements.txt</code>, <code>packages.txt</code> → Commit changes</div>
    <div class="step"><span class="num">4</span><a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a> → GitHub sign in → New app → Repo: <code>tamil-doc-reader</code> | File: <code>app.py</code> → Deploy!</div>
    <div class="step"><span class="num">5</span>3–5 நிமிடம் → இலவச URL கிடைக்கும் ✅</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**`requirements.txt`**")
        st.code("streamlit>=1.32.0\npytesseract>=0.3.10\nPillow>=10.0.0\npdfplumber>=0.10.0\npdf2image>=1.16.0\ngTTS>=2.5.0\nrequests>=2.31.0\nbeautifulsoup4>=4.12.0\ndeep-translator>=1.11.4\nnumpy>=1.24.0", language="text")
    with c2:
        st.markdown("**`packages.txt`**")
        st.code("tesseract-ocr\ntesseract-ocr-tam\ntesseract-ocr-eng\npoppler-utils", language="text")
    st.success("✅ பணம் கட்ட வேண்டியதில்லை. API key வேண்டியதில்லை.")

st.markdown('<div style="text-align:center;font-size:.74rem;color:#bbb;margin-top:2rem;padding-top:.8rem;border-top:1px solid #ddd4c4;">தமிழ் அரசு ஆவண வாசகன் v8 · 100% Free · No API Key · Built-in Tamil Dictionary + Transliteration Filter</div>', unsafe_allow_html=True)
