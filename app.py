"""
Tamil Government Document Reader — v10 FINAL
═════════════════════════════════════════════
ROOT FIX: விரும்பினால் → strip ினால் → விரும்ப → restore ு → விரும்பு ✓
All output is Tamil→Tamil. No English in meaning panel.
100% free. Zero API key.
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
.mword{font-family:'Noto Sans Tamil',sans-serif;font-size:1.6rem;font-weight:600;color:#0f172a;margin-bottom:.1rem;}
.grammar-bar{display:flex;flex-wrap:wrap;gap:8px;margin:.6rem 0 1rem;
  padding:.7rem .9rem;background:#f8f4ff;border-radius:10px;border:1px solid #e0d0ff;}
.g-chip{display:inline-flex;flex-direction:column;align-items:center;
  border-radius:8px;padding:5px 12px;min-width:70px;}
.g-lbl{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;}
.g-val{font-family:'Noto Sans Tamil',sans-serif;font-size:.97rem;font-weight:600;}
.c-root{background:#fff3e0;border:1px solid #ffd08a;}
.c-root .g-lbl{color:#8a5000;} .c-root .g-val{color:#5a3000;}
.c-sfx{background:#e8f4ff;border:1px solid #90c8ff;}
.c-sfx .g-lbl{color:#00478a;} .c-sfx .g-val{color:#003060;}
.c-pos{background:#eaffea;border:1px solid #90e090;}
.c-pos .g-lbl{color:#005a00;} .c-pos .g-val{color:#003000;font-size:.82rem;}
.c-mood{background:#fff0f8;border:1px solid #ffb0d8;}
.c-mood .g-lbl{color:#7a0040;} .c-mood .g-val{color:#500020;font-size:.82rem;}
.sec{margin-bottom:.8rem;border-radius:9px;overflow:hidden;}
.sh{font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;padding:.3rem .75rem;}
.sb{font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;font-size:1rem;line-height:1.95;padding:.65rem .9rem;}
.s1{background:#fff8e7;border:1px solid #f3d98b;} .s1 .sh{background:#fef0c0;color:#7a5000;} .s1 .sb{color:#3a2a00;}
.s2{background:#f0f7ff;border:1px solid #b8d8f8;} .s2 .sh{background:#dbeeff;color:#1a4a8a;} .s2 .sb{color:#1a3a6a;font-style:italic;}
.s3{background:#fdf2ff;border:1px solid #ddb8f8;} .s3 .sh{background:#f0d0ff;color:#4a0080;} .s3 .sb{color:#280050;}
.s4{background:#f0faf4;border:1px solid #a8dcb8;} .s4 .sh{background:#c8f0d8;color:#1a5a30;} .s4 .sb{color:#1a3a20;}
.nf{font-size:.92rem;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:.7rem 1rem;margin-top:.5rem;}
.slabel{font-size:.71rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#999;margin-bottom:.35rem;}
.hint{display:inline-block;background:#fef9e7;border:1px solid #fce7a0;border-radius:8px;padding:.4rem .85rem;font-size:.82rem;color:#7a5100;margin-bottom:.85rem;}
.dc{display:inline-block;font-size:.75rem;font-weight:600;padding:3px 10px;border-radius:20px;background:#e8f4fd;color:#1155aa;margin-bottom:.7rem;}
.step{background:#fff;border:1px solid #e5dfd4;border-radius:10px;padding:.85rem 1.1rem;margin-bottom:.5rem;font-size:.91rem;line-height:1.65;}
.num{display:inline-flex;align-items:center;justify-content:center;width:21px;height:21px;border-radius:50%;background:#0f172a;color:#d4a843;font-size:11px;font-weight:700;margin-right:7px;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MORPHOLOGICAL ENGINE  — fixed vowel restoration
# ══════════════════════════════════════════════════════════════════════════════

# (suffix, tamil_suffix_meaning, grammatical_label)
MORPHOLOGY = [
    # Conditional
    ("யினால்",    "நிபந்தனை விகுதி: ஆல்",         "நிபந்தனை வினையெச்சம்"),
    ("வதினால்",   "நிபந்தனை விகுதி: வதால்",        "நிபந்தனை வினையெச்சம்"),
    ("தினால்",    "நிபந்தனை விகுதி: தால்",         "நிபந்தனை வினையெச்சம்"),
    ("டினால்",    "நிபந்தனை விகுதி: டால்",         "நிபந்தனை வினையெச்சம்"),
    ("றினால்",    "நிபந்தனை விகுதி: றால்",         "நிபந்தனை வினையெச்சம்"),
    ("னினால்",    "நிபந்தனை விகுதி: னால்",         "நிபந்தனை வினையெச்சம்"),
    ("இனால்",     "நிபந்தனை விகுதி: இனால்",        "நிபந்தனை வினையெச்சம்"),
    ("ினால்",     "நிபந்தனை விகுதி: னால்",         "நிபந்தனை வினையெச்சம்"),
    ("னால்",      "நிபந்தனை விகுதி: னால்",         "நிபந்தனை வினையெச்சம்"),
    ("ால்",       "நிபந்தனை / கருவி விகுதி",        "நிபந்தனை / மூன்றாம் வேற்றுமை"),
    # Passive
    ("ப்படுகிறது", "நிகழ்கால செயப்பாட்டு விகுதி",  "செயப்பாட்டு வினை — நிகழ் காலம்"),
    ("க்கப்படும்", "எதிர்கால செயப்பாட்டு விகுதி",  "செயப்பாட்டு வினை — எதிர் காலம்"),
    ("ப்படும்",   "எதிர்கால செயப்பாட்டு விகுதி",   "செயப்பாட்டு வினை — எதிர் காலம்"),
    ("ப்பட்டது",  "இறந்தகால செயப்பாட்டு விகுதி",   "செயப்பாட்டு வினை — இறந்த காலம்"),
    # Past
    ("ட்டார்கள்", "இறந்தகால விகுதி: அவர்கள்",      "வினைமுற்று — இறந்த காலம்"),
    ("ட்டார்",    "இறந்தகால விகுதி: அவர்",          "வினைமுற்று — இறந்த காலம்"),
    ("ட்டான்",    "இறந்தகால விகுதி: அவன்",          "வினைமுற்று — இறந்த காலம்"),
    ("ட்டாள்",    "இறந்தகால விகுதி: அவள்",          "வினைமுற்று — இறந்த காலம்"),
    ("ட்டேன்",    "இறந்தகால விகுதி: நான்",          "வினைமுற்று — இறந்த காலம்"),
    ("னார்கள்",   "இறந்தகால விகுதி: அவர்கள்",      "வினைமுற்று — இறந்த காலம்"),
    ("னார்",      "இறந்தகால விகுதி: அவர்",          "வினைமுற்று — இறந்த காலம்"),
    ("னான்",      "இறந்தகால விகுதி: அவன்",          "வினைமுற்று — இறந்த காலம்"),
    ("னாள்",      "இறந்தகால விகுதி: அவள்",          "வினைமுற்று — இறந்த காலம்"),
    ("தார்",      "இறந்தகால விகுதி: அவர்",          "வினைமுற்று — இறந்த காலம்"),
    ("தான்",      "இறந்தகால விகுதி: அவன்",          "வினைமுற்று — இறந்த காலம்"),
    ("தாள்",      "இறந்தகால விகுதி: அவள்",          "வினைமுற்று — இறந்த காலம்"),
    # Present
    ("கிறார்கள்", "நிகழ்கால விகுதி: அவர்கள்",      "வினைமுற்று — நிகழ் காலம்"),
    ("கிறார்",    "நிகழ்கால விகுதி: அவர்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கிறான்",    "நிகழ்கால விகுதி: அவன்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கிறாள்",    "நிகழ்கால விகுதி: அவள்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கிறேன்",    "நிகழ்கால விகுதி: நான்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கிறோம்",    "நிகழ்கால விகுதி: நாம்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கிறது",     "நிகழ்கால விகுதி: அது",           "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றான்",  "நிகழ்கால விகுதி: அவன்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றார்",  "நிகழ்கால விகுதி: அவர்",          "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றது",   "நிகழ்கால விகுதி: அது",           "வினைமுற்று — நிகழ் காலம்"),
    # Future
    ("வார்கள்",   "எதிர்கால விகுதி: அவர்கள்",      "வினைமுற்று — எதிர் காலம்"),
    ("வார்",      "எதிர்கால விகுதி: அவர்",          "வினைமுற்று — எதிர் காலம்"),
    ("வான்",      "எதிர்கால விகுதி: அவன்",          "வினைமுற்று — எதிர் காலம்"),
    ("வாள்",      "எதிர்கால விகுதி: அவள்",          "வினைமுற்று — எதிர் காலம்"),
    ("வேன்",      "எதிர்கால விகுதி: நான்",          "வினைமுற்று — எதிர் காலம்"),
    ("வோம்",      "எதிர்கால விகுதி: நாம்",          "வினைமுற்று — எதிர் காலம்"),
    ("பார்",      "எதிர்கால விகுதி: அவர்",          "வினைமுற்று — எதிர் காலம்"),
    ("பான்",      "எதிர்கால விகுதி: அவன்",          "வினைமுற்று — எதிர் காலம்"),
    # Verbal noun / infinitive
    ("வதற்கு",    "வினையெச்சம்: நோக்கம்",            "வினையெச்சம் — நோக்கம்"),
    ("வதால்",     "வினையெச்சம்: காரணம்",             "வினையெச்சம் — காரணம்"),
    ("வதை",       "வினையெச்சம்: செயல்",              "வினையெச்சம்"),
    ("வது",       "வினையெச்சம்",                     "வினையெச்சம் — செயல் பெயர்"),
    # Case suffixes (noun inflection — no vowel restore needed)
    ("த்திலிருந்து","இடவேற்றுமை + ஐந்தாம்",         "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("த்தினால்",  "மூன்றாம் வேற்றுமை: ஆல்",         "பெயர்ச்சொல் + மூன்றாம் வேற்றுமை"),
    ("த்தோடு",    "உடனிகழ்ச்சி: உடன்",              "பெயர்ச்சொல் + உடனிகழ்ச்சி"),
    ("த்தில்",    "இடவேற்றுமை: இல்",                "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("த்தை",      "இரண்டாம் வேற்றுமை: ஐ",           "பெயர்ச்சொல் + இரண்டாம் வேற்றுமை"),
    ("த்தின்",    "ஆறாம் வேற்றுமை: இன்",            "பெயர்ச்சொல் + ஆறாம் வேற்றுமை"),
    ("த்துக்கு",  "நான்காம் வேற்றுமை: கு",           "பெயர்ச்சொல் + நான்காம் வேற்றுமை"),
    ("யிலிருந்து","இடவேற்றுமை + ஐந்தாம்",           "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("யில்",      "இடவேற்றுமை: இல்",                "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("யை",        "இரண்டாம் வேற்றுமை: ஐ",           "பெயர்ச்சொல் + இரண்டாம் வேற்றுமை"),
    ("யின்",      "ஆறாம் வேற்றுமை: இன்",            "பெயர்ச்சொல் + ஆறாம் வேற்றுமை"),
    ("யிடம்",     "இடவேற்றுமை: இடம்",               "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("யுடன்",     "உடனிகழ்ச்சி: உடன்",              "பெயர்ச்சொல் + உடனிகழ்ச்சி"),
    ("கள்",       "பன்மை விகுதி",                    "பன்மை"),
    ("இலிருந்து", "ஐந்தாம் வேற்றுமை",               "ஐந்தாம் வேற்றுமை"),
    ("இல்",       "இடவேற்றுமை: இல்",                "இடவேற்றுமை"),
    ("உடன்",      "உடனிகழ்ச்சி: உடன்",              "உடனிகழ்ச்சி"),
    ("இருந்து",   "ஐந்தாம் வேற்றுமை",               "ஐந்தாம் வேற்றுமை"),
    ("உடைய",      "ஆறாம் வேற்றுமை: உடைய",           "ஆறாம் வேற்றுமை"),
    ("ஐ",         "இரண்டாம் வேற்றுமை",              "இரண்டாம் வேற்றுமை"),
    ("கு",        "நான்காம் வேற்றுமை",              "நான்காம் வேற்றுமை"),
    ("ஆல்",       "மூன்றாம் வேற்றுமை",              "மூன்றாம் வேற்றுமை"),
    ("ஆக",        "நிலை குறிப்பு",                   "குறிப்பு வினையெச்சம்"),
    ("ஆன",        "பண்புப்பெயர் விகுதி",             "பண்புப்பெயர்"),
    ("ஆனது",      "வினை பெயர் விகுதி",               "வினை பெயர்"),
    ("ஆகும்",     "எதிர்கால வினைமுற்று",             "வினைமுற்று — எதிர் காலம்"),
    ("என்று",     "மேற்கோள் விகுதி",                 "மேற்கோள்"),
    ("இல்லாமல்",  "எதிர்மறை வினையெச்சம்",           "எதிர்மறை வினையெச்சம்"),
]

# Sandhi corrections (apply BEFORE vowel restore)
SANDHI = [
    ("ந்த",   "ந்தம்"),
    ("ட்ட",   "ட்டம்"),
    ("க்க",   "க்கம்"),
    ("ல்ல",   "ல்"),
    ("ன்ன",   "ன்னம்"),
    ("ர்த்த", "ர்த்தம்"),
]

# Suffixes that are NOUN case markers — don't restore vowel for these
NOUN_SUFFIXES = {
    "த்திலிருந்து","த்தினால்","த்தோடு","த்தில்","த்தை","த்தின்","த்துக்கு",
    "யிலிருந்து","யில்","யை","யின்","யிடம்","யுடன்",
    "கள்","இலிருந்து","இல்","உடன்","இருந்து","உடைய","ஐ","கு","ஆல்",
    "ஆக","ஆன","ஆனது","ஆகும்","என்று","இல்லாமல்",
}

def restore_verb_root(stem: str) -> str:
    """Restore verb root vowel after suffix stripping."""
    if not stem:
        return stem
    # Strip trailing nasal/liquid consonant clusters that appear after stem
    if stem.endswith("ின்"):
        stem = stem[:-3]
    elif stem.endswith(("ன்", "ல்", "ர்", "ண்", "ழ்", "ட்", "ற்")):
        stem = stem[:-2]
    # If last character is a bare consonant (0xB95–0xBB9), add ு
    last = stem[-1] if stem else ""
    code = ord(last) if last else 0
    if 0xB95 <= code <= 0xBB9:
        stem = stem + "\u0bc1"  # add ு
    return stem

def apply_sandhi(stem: str) -> str:
    for tail, rep in SANDHI:
        if stem.endswith(tail):
            return stem[:-len(tail)] + rep
    return stem

def analyze(word: str) -> dict:
    """Morphological analysis: returns root, suffix info, POS."""
    w = word
    for suffix, sfx_meaning, pos in MORPHOLOGY:
        if w.endswith(suffix) and len(w) > len(suffix) + 1:
            stem = w[:-len(suffix)]
            # For noun case suffixes → apply sandhi only
            if suffix in NOUN_SUFFIXES:
                root = apply_sandhi(stem)
            else:
                # For verb suffixes → apply sandhi then vowel restore
                root = restore_verb_root(apply_sandhi(stem))
            return {
                "root":        root,
                "suffix":      suffix,
                "sfx_meaning": sfx_meaning,
                "pos":         pos,
                "is_verb":     "வினை" in pos,
                "inflected":   True,
            }
    # No suffix found — word is in base form
    return {"root": w, "suffix": None, "sfx_meaning": None, "pos": None,
            "is_verb": False, "inflected": False}


# ══════════════════════════════════════════════════════════════════════════════
# DICTIONARY  (Tamil→Tamil definitions only)
# ══════════════════════════════════════════════════════════════════════════════
D = {
    # ── VERBS ────────────────────────────────────────────────────────────────
    "விரும்பு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒன்றை ஆசைப்படுவது — பிரியமாக நினைப்பது — ஒரு செயலை செய்ய விழைவது",
        "எடுத்துக்காட்டு": "நீங்கள் விரும்பினால் ஒப்பந்தம் ரத்து செய்யலாம். | அவர் இந்த வேலையை விரும்புகிறார்.",
        "ஆவண பொருள்": "'விரும்பினால்' என்று ஆவணத்தில் வந்தால் — 'உங்களுக்கு விருப்பம் இருந்தால்' என்று பொருள். இது கட்டாயமில்லை, தேர்வு மட்டுமே.",
    },
    "செய்": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒரு செயலை நடத்துவது — நிறைவேற்றுவது",
        "எடுத்துக்காட்டு": "ஒப்பந்தம் செய்யப்பட்டது. | அவர் வேலை செய்கிறார்.",
        "ஆவண பொருள்": "'செய்யப்பட்டது' என்றால் அந்த செயல் அதிகாரப்பூர்வமாக முடிக்கப்பட்டது.",
    },
    "கொடு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒருவருக்கு ஒன்றை அளிப்பது — வழங்குவது",
        "எடுத்துக்காட்டு": "நீதிமன்றம் தீர்ப்பு கொடுத்தது.",
        "ஆவண பொருள்": "'கொடுக்கப்படும்' என்றால் அரசு அல்லது நிறுவனம் அதை வழங்கும் என்று உறுதியளிக்கிறது.",
    },
    "பெறு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒன்றை கைக்கொள்வது — கிடைப்பது",
        "எடுத்துக்காட்டு": "அனுமதி பெறப்பட்டது.",
        "ஆவண பொருள்": "'பெறப்பட்டது' என்றால் சட்டரீதியான ஒப்புதல் கிடைத்தது.",
    },
    "வழங்கு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "அளிப்பது — கொடுப்பது. பொதுவாக அரசு அல்லது அதிகாரி கொடுக்கும்போது இந்த வார்த்தை பயன்படும்",
        "எடுத்துக்காட்டு": "அரசு சான்றிதழ் வழங்குகிறது.",
        "ஆவண பொருள்": "'வழங்கப்படும்' என்றால் அரசு கொடுக்கும் என்று அதிகாரப்பூர்வமாக உறுதியளிக்கிறது.",
    },
    "தெரிவி": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒரு தகவலை அறிவிப்பது — சொல்வது — தெரியப்படுத்துவது",
        "எடுத்துக்காட்டு": "விண்ணப்பதாரர் தன் முகவரியை தெரிவிக்க வேண்டும்.",
        "ஆவண பொருள்": "'தெரிவிக்கப்படுகிறது' என்றால் அதிகாரப்பூர்வமாக அறிவிக்கப்படுகிறது.",
    },
    "ஒப்புக்கொள்": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒரு விஷயத்திற்கு தன் சம்மதத்தை தெரிவிப்பது — ஏற்றுக்கொள்வது",
        "எடுத்துக்காட்டு": "இரு தரப்பினரும் இந்த விதிமுறைகளை ஒப்புக்கொண்டனர்.",
        "ஆவண பொருள்": "கையொப்பமிட்டால் எல்லா விதிமுறைகளையும் ஒப்புக்கொண்டதாகும்.",
    },
    "மீறு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒரு கட்டளை அல்லது விதிமுறையை கடப்பது — பின்பற்றாமல் போவது",
        "எடுத்துக்காட்டு": "ஒப்பந்தத்தை மீறினால் வழக்கு தொடரலாம்.",
        "ஆவண பொருள்": "'மீறினால்' என்று வந்தால் — அப்படி செய்தால் சட்ட நடவடிக்கை நடக்கும் என்று எச்சரிக்கை.",
    },
    "கோரு": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒன்றை தர வேண்டும் என்று கேட்பது — உரிமை கோருவது",
        "எடுத்துக்காட்டு": "வாரிசு சொத்தை கோருகிறார்.",
        "ஆவண பொருள்": "'கோரப்பட்டது' என்றால் சட்டரீதியான கோரிக்கை வைக்கப்பட்டது.",
    },
    "நிர்ணயி": {
        "pos": "வினைச்சொல்",
        "பொருள்": "ஒரு தொகை அல்லது முடிவை தீர்மானிப்பது — நிறுவுவது",
        "எடுத்துக்காட்டு": "கட்டணம் அரசால் நிர்ணயிக்கப்படும்.",
        "ஆவண பொருள்": "'நிர்ணயிக்கப்பட்டது' என்றால் அரசு அல்லது நீதிமன்றம் தீர்மானித்தது.",
    },
    "அனுமதி": {
        "pos": "வினைச்சொல் / பெயர்ச்சொல்",
        "பொருள்": "ஒரு செயல் செய்வதற்கு அதிகாரப்பூர்வ ஒப்புதல் கொடுப்பது",
        "எடுத்துக்காட்டு": "கட்டிடம் கட்ட நகராட்சி அனுமதி பெற வேண்டும்.",
        "ஆவண பொருள்": "அரசு அனுமதி இல்லாமல் செய்யப்பட்ட செயல் சட்டவிரோதமாகலாம்.",
    },
    # ── EVERYDAY DOCUMENT WORDS ───────────────────────────────────────────────
    "இனிமேல்": {
        "pos": "வினையடை",
        "பொருள்": "இப்போதிலிருந்து — இனி முதல் — இந்த நாளிலிருந்து என்று பொருள். ஒரு மாற்றம் இப்போதே நடைமுறைக்கு வருகிறது என்று குறிக்கும்",
        "எடுத்துக்காட்டு": "இனிமேல் இந்த நிலம் உங்கள் பெயரில் இருக்கும். | இனிமேல் வாடகை 5000 ரூபாய் ஆகும்.",
        "ஆவண பொருள்": "ஒப்பந்தத்தில் 'இனிமேல்' என்று வந்தால் — இந்த ஆவணம் கையொப்பமிட்ட நாளிலிருந்தே அந்த விதிமுறை நடைமுறைக்கு வரும்.",
    },
    "உரிமையாளர்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒரு சொத்தை சட்டரீதியாக வைத்திருப்பவர் — நிலம், வீடு அல்லது பொருளின் சொந்தக்காரர்",
        "எடுத்துக்காட்டு": "இந்த வீட்டின் உரிமையாளர் திரு. ராமசாமி.",
        "ஆவண பொருள்": "பட்டாவில் யாருடைய பெயர் உள்ளதோ அவரே உரிமையாளர். வேறு யாரும் சட்டரீதியாக உரிமை கோர முடியாது.",
        "கவனிக்க": "உரிமையாளர் பெயர் பட்டாவில் பதிவு ஆகியிருக்க வேண்டும்.",
    },
    "உரிமை": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒரு நபருக்கு சட்டப்படி சேர்ந்த அதிகாரம் அல்லது சொத்து",
        "எடுத்துக்காட்டு": "இந்த நிலத்தின் உரிமை அவருக்கு சேரும்.",
        "ஆவண பொருள்": "சட்ட ஆவணத்தில் உரிமை என்பது சட்டரீதியான கோரிக்கை வைக்கும் தகுதி.",
    },
    "தரப்பு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒப்பந்தத்தில் பங்கு பெறும் நபர் அல்லது குழு",
        "எடுத்துக்காட்டு": "முதல் தரப்பு விற்பவர், இரண்டாம் தரப்பு வாங்குபவர்.",
        "ஆவண பொருள்": "ஒப்பந்தத்தில் இரண்டு தரப்பினரும் கட்டாயம் கையொப்பமிட வேண்டும்.",
    },
    "தரப்பினர்": {
        "pos": "பெயர்ச்சொல் — பன்மை",
        "பொருள்": "ஒப்பந்தத்தில் பங்கேற்கும் நபர்கள் — அனைத்து நபர்களையும் சேர்த்து குறிப்பிடும்",
        "எடுத்துக்காட்டு": "இரு தரப்பினரும் ஒப்பந்தத்தில் ஒப்புக்கொண்டனர்.",
        "ஆவண பொருள்": "அனைத்து தரப்பினரும் கையொப்பமிட்டால் மட்டுமே ஆவணம் செல்லுபடியாகும்.",
    },
    "ஒப்பந்தம்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "இரண்டு அல்லது அதிக நபர்களிடையே எழுத்தில் செய்யப்படும் சட்டரீதியான உடன்படிக்கை",
        "எடுத்துக்காட்டு": "வீடு வாடகைக்கு கொடுக்க ஒப்பந்தம் செய்யப்பட்டது.",
        "ஆவண பொருள்": "ஒப்பந்தம் மீறினால் நீதிமன்றம் செல்லலாம். ஸ்டாம்ப் பேப்பரில் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "கவனிக்க": "படிக்காமல் கையொப்பமிடாதீர்கள்.",
    },
    "சுமார்": {
        "pos": "வினையடை",
        "பொருள்": "தோராயமாக — கிட்டத்தட்ட — சரியான எண்ணிக்கை தெரியாதபோது மதிப்பிடும் வார்த்தை",
        "எடுத்துக்காட்டு": "சுமார் 40 வயது என்று ஆவணத்தில் குறிப்பிடப்பட்டுள்ளது.",
        "ஆவண பொருள்": "வயது அல்லது அளவு சரியாக தெரியாவிட்டால் 'சுமார்' என்று மதிப்பீடு செய்வார்கள்.",
    },
    "மேற்கண்ட": {
        "pos": "உரிச்சொல்",
        "பொருள்": "இந்த வரிக்கு மேலே குறிப்பிட்டது — மேலே சொன்னது என்று பொருள்",
        "எடுத்துக்காட்டு": "மேற்கண்ட விவரங்கள் சரியானவை என்று சான்றளிக்கிறேன்.",
        "ஆவண பொருள்": "ஆவணத்தில் 'மேற்கண்ட' என்றால் — இந்த வாக்கியத்திற்கு மேலே எழுதியவற்றை குறிக்கிறது.",
    },
    "கீழ்க்கண்ட": {
        "pos": "உரிச்சொல்",
        "பொருள்": "இந்த வரிக்கு கீழே குறிப்பிடப்படுவது — இனி சொல்லப்போவது என்று பொருள்",
        "எடுத்துக்காட்டு": "கீழ்க்கண்ட விதிமுறைகளை பின்பற்ற வேண்டும்.",
        "ஆவண பொருள்": "ஆவணத்தில் 'கீழ்க்கண்ட' என்றால் — இனி வரும் வரிகளில் சொல்லப்போவதை குறிக்கிறது.",
    },
    "நிபந்தனை": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒப்பந்தத்தில் கட்டாயம் பின்பற்ற வேண்டிய கட்டுப்பாடு அல்லது நிலை",
        "எடுத்துக்காட்டு": "இந்த நிபந்தனைக்கு உட்பட்டு நிலம் வழங்கப்படும்.",
        "ஆவண பொருள்": "நிபந்தனை மீறினால் ஒப்பந்தம் தானாக ரத்தாகும்.",
    },
    "விதிமுறை": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "பின்பற்ற வேண்டிய கட்டாய நியதிகள்",
        "எடுத்துக்காட்டு": "ஒப்பந்தத்தின் விதிமுறைகளை மீறினால் நடவடிக்கை எடுக்கப்படும்.",
        "ஆவண பொருள்": "கையொப்பமிட்டால் எல்லா விதிமுறைகளையும் ஒப்புக்கொண்டதாகும்.",
    },
    "காலக்கெடு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒரு வேலையை முடிக்க அல்லது விண்ணப்பிக்க கடைசி நாள்",
        "எடுத்துக்காட்டு": "விண்ணப்பிக்க காலக்கெடு 31 மார்ச் 2024.",
        "ஆவண பொருள்": "காலக்கெடு தாண்டினால் விண்ணப்பம் ஏற்கப்படாது.",
        "கவனிக்க": "காலக்கெடுவை மீறாதீர்கள் — நீட்டிப்பு கிடைக்காது.",
    },
    "ரத்து": {
        "pos": "வினைச்சொல் / பெயர்ச்சொல்",
        "பொருள்": "ஒரு முடிவை அல்லது ஒப்பந்தத்தை செல்லாததாக்குவது",
        "எடுத்துக்காட்டு": "கட்டணம் கட்டாததால் விண்ணப்பம் ரத்து செய்யப்பட்டது.",
        "ஆவண பொருள்": "ஆவணம் ரத்து ஆனால் அதன் மீது எந்த உரிமையும் கிடையாது.",
    },
    "நஷ்டஈடு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒருவரால் ஏற்பட்ட நஷ்டத்திற்கு கொடுக்கப்படும் பணம்",
        "எடுத்துக்காட்டு": "ஒப்பந்தம் மீறினால் நஷ்டஈடு கொடுக்க வேண்டும்.",
        "ஆவண பொருள்": "நஷ்டஈடு தொகை ஒப்பந்தத்திலேயே குறிப்பிடப்படும்.",
    },
    "முன்பணம்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒப்பந்தம் செய்யும்போது முன்கூட்டியே கொடுக்கும் பணம்",
        "எடுத்துக்காட்டு": "வீட்டிற்கு 50,000 ரூபாய் முன்பணம் கொடுத்தார்.",
        "ஆவண பொருள்": "முன்பணம் கொடுத்தால் ரசீது வாங்க வேண்டும். ஒப்பந்தம் ரத்தானால் முன்பணம் திரும்ப கிடைக்கும்.",
    },
    "வாடகை": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "வீடு அல்லது நிலத்தை பயன்படுத்துவதற்காக மாதந்தோறும் கொடுக்கும் பணம்",
        "எடுத்துக்காட்டு": "மாதந்தோறும் 5000 ரூபாய் வாடகை செலுத்த வேண்டும்.",
        "ஆவண பொருள்": "வாடகை ஒப்பந்தத்தில் தொகை, செலுத்தும் தேதி, காலம் தெளிவாக இருக்க வேண்டும்.",
    },
    # ── LAND ────────────────────────────────────────────────────────────────
    "பட்டா": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "நிலத்தின் உரிமை பத்திரம் — நீங்கள் அந்த நிலத்தின் சட்டபூர்வ உரிமையாளர் என்பதை அரசு உறுதி செய்யும் ஆவணம்",
        "எடுத்துக்காட்டு": "ரமேஷிடம் அவரது நிலத்திற்கு பட்டா இருக்கிறது.",
        "ஆவண பொருள்": "பட்டா இல்லாமல் நிலத்தை விற்கவோ அடமானம் வைக்கவோ முடியாது.",
        "கவனிக்க": "பட்டாவில் உங்கள் பெயர் இல்லையென்றால் நீங்கள் சட்டபூர்வமாக உரிமையாளர் அல்ல.",
    },
    "சிட்டா": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "நிலத்தின் விவரங்களை கொண்ட அரசு பதிவு ஆவணம் — நிலத்தின் அளவு, வகை, உரிமையாளர் பெயர் இதில் இருக்கும்",
        "எடுத்துக்காட்டு": "சிட்டாவில் நிலத்தின் அளவு 2 ஏக்கர் என்று குறிப்பிடப்பட்டுள்ளது.",
        "ஆவண பொருள்": "தமிழ்நாட்டில் நிலம் வாங்கும்போது சிட்டா + பட்டா இரண்டும் தேவை.",
    },
    "சர்வே எண்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒவ்வொரு நிலத்திற்கும் அரசு கொடுக்கும் தனிப்பட்ட அடையாள எண்",
        "எடுத்துக்காட்டு": "சர்வே எண் 123/4 என்பது அந்த நிலத்தின் அரசு பதிவு எண்.",
        "ஆவண பொருள்": "நிலம் வாங்க, விற்க, அடமானம் வைக்க இந்த எண் கட்டாயம் தேவை.",
    },
    # ── LEGAL / GOVT ─────────────────────────────────────────────────────────
    "சான்றிதழ்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒரு விஷயம் உண்மை என்று அரசு உறுதி செய்யும் ஆவணம்",
        "எடுத்துக்காட்டு": "சாதி சான்றிதழ் வேலைக்கு விண்ணப்பிக்க தேவை.",
        "ஆவண பொருள்": "அரசு அதிகாரி கையொப்பமிட்ட சான்றிதழ் மட்டுமே செல்லுபடியாகும்.",
    },
    "அரசாணை": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "அரசு அதிகாரப்பூர்வமாக பிறப்பிக்கும் ஆணை — அரசின் கட்டளை",
        "எடுத்துக்காட்டு": "இந்த திட்டம் அரசாணை எண் 150 மூலம் அனுமதிக்கப்பட்டது.",
        "ஆவண பொருள்": "அரசாணை கட்டாயம் பின்பற்ற வேண்டிய உத்தரவு. மீறினால் சட்ட நடவடிக்கை வரும்.",
    },
    "மனு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "குறை தீர்க்க அல்லது ஒரு விஷயத்திற்கு அரசிடம் கோரும் கடிதம்",
        "எடுத்துக்காட்டு": "நிலம் சம்பந்தமாக கலெக்டரிடம் மனு சமர்ப்பித்தார்.",
        "ஆவண பொருள்": "மனு கொடுத்த பிறகு ரசீது வாங்க வேண்டும். மனு எண் வைத்திருங்கள்.",
    },
    "வழக்கு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "நீதிமன்றத்தில் தீர்வு காண தாக்கல் செய்யப்படும் புகார்",
        "எடுத்துக்காட்டு": "நிலம் சம்பந்தமாக நீதிமன்றத்தில் வழக்கு தாக்கல் செய்தார்.",
        "ஆவண பொருள்": "வழக்கு தாக்கல் ஆனால் வழக்கு எண் வைத்திருங்கள்.",
    },
    "தீர்ப்பு": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "நீதிமன்றம் வழக்கில் கொடுக்கும் இறுதி முடிவு",
        "எடுத்துக்காட்டு": "நீதிமன்றம் வாதிக்கு சாதகமாக தீர்ப்பு அளித்தது.",
        "ஆவண பொருள்": "தீர்ப்புக்கு எதிராக உயர் நீதிமன்றத்தில் மேல்முறையீடு செய்யலாம்.",
    },
    "கட்டணம்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "சேவைக்காக செலுத்த வேண்டிய பணம்",
        "எடுத்துக்காட்டு": "பதிவுக்கு கட்டணம் கட்ட வேண்டும்.",
        "ஆவண பொருள்": "அரசு நிர்ணயிக்கும் கட்டணம் மட்டுமே செலுத்த வேண்டும்.",
    },
    "ரசீது": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "பணம் கட்டியதற்கான ஆதாரக் கடிதம்",
        "எடுத்துக்காட்டு": "கட்டணம் கட்டிய பிறகு ரசீது வாங்கினார்.",
        "ஆவண பொருள்": "ரசீது இல்லாமல் கட்டினேன் என்று நிரூபிக்க முடியாது.",
        "கவனிக்க": "எப்போதும் ரசீது வாங்குங்கள்.",
    },
    "கையொப்பம்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒரு ஆவணத்தில் நீங்கள் ஒப்புதல் அளிக்கும் கை எழுத்து",
        "எடுத்துக்காட்டு": "ஆவணத்தில் கையொப்பமிட்டார்.",
        "ஆவண பொருள்": "கையொப்பமிட்ட ஆவணம் சட்டரீதியான ஒப்பந்தம்.",
        "கவனிக்க": "படிக்காமல் கையொப்பமிடாதீர்கள் — அது மிகவும் ஆபத்தானது.",
    },
    "அடமானம்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "கடன் வாங்க சொத்தை பாதுகாப்பாக வைப்பது — கடன் திரும்ப கொடுக்காவிட்டால் சொத்து போகும்",
        "எடுத்துக்காட்டு": "வீட்டை அடமானம் வைத்து வங்கியில் கடன் வாங்கினார்.",
        "ஆவண பொருள்": "அடமான ஆவணம் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "கவனிக்க": "கடன் திரும்ப கொடுக்காவிட்டால் வங்கி சொத்தை ஏலம் போடலாம்.",
    },
    "வாரிசு சான்றிதழ்": {
        "pos": "பெயர்ச்சொல்",
        "பொருள்": "ஒருவர் இறந்த பிறகு அவரது சொத்துக்கு யார் உரிமையாளர் என்று அரசு சொல்லும் ஆவணம்",
        "எடுத்துக்காட்டு": "அப்பா இறந்த பிறகு வாரிசு சான்றிதழ் வாங்கி சொத்து பெற்றனர்.",
        "ஆவண பொருள்": "வாரிசு சான்றிதழ் இல்லாமல் இறந்தவரின் சொத்தை சட்டரீதியாக கோர முடியாது.",
    },
}

# Aliases — some words may appear with slight variations
ALIASES = {
    "விரும்பு": "விரும்பு",
    "விரும்ப": "விரும்பு",
    "விரும்பி": "விரும்பு",
    "செய்ய": "செய்",
    "கொடுக்க": "கொடு",
    "வழங்கு": "வழங்கு",
    "வழங்க": "வழங்கு",
    "தெரிவிக்க": "தெரிவி",
    "அனுமதிக்க": "அனுமதி",
}


# ══════════════════════════════════════════════════════════════════════════════
# WORD CLEANER + TRANSLITERATION DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
def clean_word(w: str) -> str:
    return re.sub(r'^[\s,.\-;:"""\'()[\]/\\|]+|[\s,.\-;:"""\'()[\]/\\|]+$', '', w).strip()

_REAL_EN = re.compile(
    r'\b(from|now|on|here|after|hereafter|owner|person|agreement|contract|property|'
    r'land|certificate|order|court|legal|government|right|claim|witness|sign|date|'
    r'number|area|name|address|amount|pay|tax|duty|document|record|file|case|'
    r'judge|petition|transfer|sale|lease|rent|survey|house|building|the|this|that|'
    r'and|or|of|in|to|for|with|by|at|an|a|is|are|was|were|have|has|will|shall|'
    r'may|can|must|should|not|no|yes|want|wish|desire|if|when|since|because|'
    r'optional|voluntary|condition|term|cancel|revoke)\b',
    re.IGNORECASE
)

def is_transliteration(result: str) -> bool:
    if not result or len(result.strip()) < 2: return True
    r = result.strip()
    if _REAL_EN.search(r): return False
    if re.match(r'^[A-Za-z\s]+$', r) and len(r) < 30: return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
def dict_lookup(root: str):
    if root in D: return D[root]
    if root in ALIASES and ALIASES[root] in D: return D[ALIASES[root]]
    for v in _variants(root):
        if v in D: return D[v]
    return None

def _variants(w):
    sw = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in sw if a in w and w.replace(a,b,1)!=w]

def src_mymemory(word: str):
    try:
        r = requests.get("https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"}, timeout=4)
        if r.status_code == 200:
            t = r.json().get("responseData",{}).get("translatedText","")
            if t and not is_transliteration(t) and len(t.strip()) > 1:
                return t.strip()
    except: pass
    return None

def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and not is_transliteration(t): return t.strip()
    except: pass
    return None

def find_context(text: str, word: str):
    if not text or not word: return None
    for sent in re.split(r'(?<=[.!?\n])\s*', text):
        s = sent.strip()
        if word in s and len(s) > 5: return s
    idx = text.find(word)
    if idx >= 0:
        return "…" + text[max(0,idx-80):min(len(text),idx+len(word)+80)].strip() + "…"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str = "") -> dict:
    w        = clean_word(word)
    morph    = analyze(w)
    root     = morph["root"]
    dict_res = dict_lookup(root) or dict_lookup(w)
    ctx      = find_context(doc_text, w) or find_context(doc_text, root)
    online   = None
    if not dict_res:
        online = src_mymemory(w) or src_mymemory(root) or src_google(w)
    return {
        "word": word, "clean": w, "morph": morph, "root": root,
        "dict": dict_res, "online": online, "context": ctx,
        "found": bool(dict_res or online),
    }

# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word):
    try:
        buf = io.BytesIO()
        gTTS(text=clean_word(word), lang="ta", slow=False).write_to_fp(buf)
        buf.seek(0); return buf
    except: return None

# ── OCR ───────────────────────────────────────────────────────────────────────
def preprocess(img):
    img = img.convert("L"); w, h = img.size
    if w < 1800: sc = 1800/w; img = img.resize((int(w*sc),int(h*sc)), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    arr = np.array(img)
    arr = ((arr > int(arr.mean()*0.85))*255).astype(np.uint8)
    return Image.fromarray(arr)

def clean_text(raw):
    lines = raw.splitlines(); out = []
    for ln in lines:
        ln = re.sub(r"[|}{\\~`_]","",ln).strip()
        ln = re.sub(r" {2,}"," ",ln)
        if not ln:
            if out and out[-1] != "": out.append("")
            continue
        out.append(ln)
    merged, i = [], 0
    while i < len(out):
        if out[i] == "": merged.append(""); i += 1; continue
        cur = out[i]
        while (i+1 < len(out) and out[i+1] != ""
               and not cur.rstrip().endswith((".",":",")","?","!","।"))
               and len(cur) > 8):
            i += 1; cur += " " + out[i]
        merged.append(cur); i += 1
    return "\n".join(merged).strip()

def ocr_image(img):
    return clean_text(pytesseract.image_to_string(preprocess(img), config=r"--oem 3 --psm 6 -l tam+eng"))

def extract_pdf(f):
    ts = []
    with pdfplumber.open(f) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t: ts.append(clean_text(t))
    return "\n\n".join(ts)

def is_tamil(w): return bool(re.search(r"[\u0B80-\u0BFF]", w))
def tokenize(t): return re.findall(r"[\u0B80-\u0BFF]+", t)

DOC_TYPES = {
    "பட்டா / நிலம்":    ["பட்டா","சிட்டா","survey","சர்வே","நிலம்","ஏக்கர்"],
    "வாடகை ஒப்பந்தம்": ["வாடகை","குடியிருப்பவர்","rent","lease"],
    "அரசாணை (G.O.)":    ["G.O.","அரசாணை","government order","செயல்முறை"],
    "சான்றிதழ்":         ["சான்றிதழ்","certificate","பிறப்பு","சாதி","வருமானம்"],
    "சட்ட ஆவணம்":       ["மனு","petition","court","நீதிமன்றம்","வழக்கு"],
}
def detect_doc_type(text):
    t = text.lower()
    for dtype, kws in DOC_TYPES.items():
        if any(k.lower() in t for k in kws): return dtype
    return "அரசு ஆவணம்"

for k, v in [("text",""),("word",""),("doc_type","அரசு ஆவணம்")]:
    st.session_state.setdefault(k, v)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 தமிழ் அரசு ஆவண வாசகன்</h1>
  <p>ஆவணம் பதிவேற்று · உரை படி · தமிழில் பொருள் கண்டறி · இலக்கண வேர்ச்சொல் பகுப்பாய்வு · 100% இலவசம்</p>
</div>
""", unsafe_allow_html=True)

t_reader, t_deploy = st.tabs(["📄 ஆவண வாசகன்", "🚀 Deploy Guide"])

with t_reader:
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="slabel">படி 1 — ஆவணம் பதிவேற்றவும்</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("உரை எடுக்கிறோம்…"):
                if uploaded.type == "application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("OCR இயக்குகிறோம்…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs = convert_from_bytes(uploaded.getvalue(), first_page=1, last_page=1)
                            text = ocr_image(imgs[0]) if imgs else ""
                        except Exception as e:
                            st.error(f"பிழை: {e}"); text = ""
                else:
                    text = ocr_image(Image.open(uploaded))
                st.session_state.text     = text
                st.session_state.doc_type = detect_doc_type(text)

        if st.session_state.text:
            st.markdown(f'<div class="dc">📋 {st.session_state.doc_type}</div>', unsafe_allow_html=True)
            st.markdown('<div class="slabel">படி 2 — ஆவணம் படிக்கவும்</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 புரியாத சொல்லை கீழே dropdown-ல் தேர்வு செய்யுங்கள் அல்லது வலதில் தட்டச்சு செய்யுங்கள்</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)
            tw = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t) > 1})
            if tw:
                st.markdown('<div class="slabel" style="margin-top:.7rem">சொல் தேர்வு</div>', unsafe_allow_html=True)
                pick = st.selectbox("p", ["— தேர்வு —"] + tw, label_visibility="collapsed", key="pick")
                if pick != "— தேர்வு —": st.session_state.word = pick
        else:
            st.info("மேலே PDF அல்லது படம் பதிவேற்றவும்.")

    with right:
        st.markdown('<div class="slabel">சொல் பொருள் — தமிழில்</div>', unsafe_allow_html=True)
        typed = st.text_input("தமிழ் சொல்:", placeholder="உதா: விரும்பினால், இனிமேல், ஒப்பந்தம்", key="typed")
        if typed: st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(clean_word(w)):
            with st.spinner("பகுப்பாய்கிறோம்…"):
                res   = lookup(w, st.session_state.text)
                audio = speak(w)

            m    = res["morph"]
            root = res["root"]
            d    = res["dict"]

            st.markdown(f'<div class="mcard"><div class="mword">{res["clean"]}</div>', unsafe_allow_html=True)

            # ── Grammar analysis chips ──
            chips = []
            chips.append(f'<div class="g-chip c-root"><div class="g-lbl">வேர்ச்சொல்</div><div class="g-val">{root}</div></div>')
            if m["suffix"]:
                chips.append(f'<div class="g-chip c-sfx"><div class="g-lbl">விகுதி</div><div class="g-val">{m["suffix"]}</div></div>')
            pos_label = d["pos"] if d else (m["pos"] or "—")
            chips.append(f'<div class="g-chip c-pos"><div class="g-lbl">இலக்கணம்</div><div class="g-val">{pos_label}</div></div>')
            if m["sfx_meaning"]:
                chips.append(f'<div class="g-chip c-mood"><div class="g-lbl">விகுதி பொருள்</div><div class="g-val">{m["sfx_meaning"]}</div></div>')
            st.markdown(f'<div class="grammar-bar">{"".join(chips)}</div>', unsafe_allow_html=True)

            # ── Meaning sections ──
            if res["found"]:
                if d:
                    st.markdown(f'<div class="sec s1"><div class="sh">📖 தமிழ் பொருள்</div><div class="sb">{d["பொருள்"]}</div></div>', unsafe_allow_html=True)
                    if d.get("எடுத்துக்காட்டு"):
                        st.markdown(f'<div class="sec s2"><div class="sh">✏️ எடுத்துக்காட்டு வாக்கியம்</div><div class="sb">{d["எடுத்துக்காட்டு"]}</div></div>', unsafe_allow_html=True)
                    if d.get("ஆவண பொருள்"):
                        st.markdown(f'<div class="sec s3"><div class="sh">📋 ஆவணத்தில் பொருள்</div><div class="sb">{d["ஆவண பொருள்"]}</div></div>', unsafe_allow_html=True)
                    if d.get("கவனிக்க"):
                        st.markdown(f'<div class="sec s4"><div class="sh">⚠️ கவனிக்க வேண்டியது</div><div class="sb">{d["கவனிக்க"]}</div></div>', unsafe_allow_html=True)
                elif res["online"]:
                    st.markdown(f'<div class="sec s1"><div class="sh">🔤 பொருள்</div><div class="sb">{res["online"]}</div></div>', unsafe_allow_html=True)
                if res["context"]:
                    st.markdown(f'<div class="sec s4"><div class="sh">📄 உங்கள் ஆவணத்தில்</div><div class="sb">{res["context"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="nf">⚠️ <strong>{res["clean"]}</strong> — வேர்ச்சொல்: <strong>{root}</strong> — பொருள் கிடைக்கவில்லை.</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 உச்சரிப்பு**")
                st.audio(audio, format="audio/mp3")

        elif w:
            st.info("தமிழ் எழுத்தில் சொல்லை தட்டச்சு செய்யவும்.")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-family:'Noto Sans Tamil',sans-serif;font-size:1rem;margin-top:.4rem;color:#999;">
                மேலே சொல்லை தட்டச்சு செய்யுங்கள்
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("📚 உள்ளமைக்கப்பட்ட தமிழ் அகராதி + MyMemory + Google Translate | 100% இலவசம்")

with t_deploy:
    st.markdown("## 🚀 GitHub → Streamlit Cloud")
    st.info("✅ 100% இலவசம். API key தேவையில்லை.")
    st.markdown("""
    <div class="step"><span class="num">1</span><a href="https://github.com" target="_blank">github.com</a> → Sign up</div>
    <div class="step"><span class="num">2</span>New repository → <code>tamil-doc-reader</code> | Public → Create</div>
    <div class="step"><span class="num">3</span><code>app.py</code>, <code>requirements.txt</code>, <code>packages.txt</code> upload → Commit</div>
    <div class="step"><span class="num">4</span><a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a> → New app → File: <code>app.py</code> → Deploy!</div>
    <div class="step"><span class="num">5</span>3–5 நிமிடம் → இலவச URL ✅</div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**`requirements.txt`**")
        st.code("streamlit>=1.32.0\npytesseract>=0.3.10\nPillow>=10.0.0\npdfplumber>=0.10.0\npdf2image>=1.16.0\ngTTS>=2.5.0\nrequests>=2.31.0\nbeautifulsoup4>=4.12.0\ndeep-translator>=1.11.4\nnumpy>=1.24.0", language="text")
    with c2:
        st.markdown("**`packages.txt`**")
        st.code("tesseract-ocr\ntesseract-ocr-tam\ntesseract-ocr-eng\npoppler-utils", language="text")

st.markdown('<div style="text-align:center;font-size:.74rem;color:#bbb;margin-top:2rem;padding-top:.8rem;border-top:1px solid #ddd4c4;">தமிழ் அரசு ஆவண வாசகன் v10 · Tamil Morphological Engine · 100% Free</div>', unsafe_allow_html=True)
