"""
Tamil Government Document Reader — v9 PROFESSIONAL
════════════════════════════════════════════════════
KEY UPGRADE: Full Tamil Morphological Engine
  • Identifies grammatical root (வேர்ச்சொல்) — விரும்பினால் → விரும்பு
  • Shows suffix breakdown (விகுதி) — ினால் = conditional "if"
  • Tamil→Tamil definition from built-in verb + noun dictionary
  • Part of speech label (வினைச்சொல் / பெயர்ச்சொல் etc.)
  • Example sentence in Tamil
  • Document context in Tamil
  100% free — zero API key
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

/* Grammar analysis bar */
.grammar-bar{
  display:flex;flex-wrap:wrap;gap:8px;
  margin:.5rem 0 1rem;padding:.7rem .9rem;
  background:#f8f4ff;border-radius:10px;border:1px solid #e0d0ff;
}
.g-chip{
  display:inline-flex;flex-direction:column;align-items:center;
  border-radius:8px;padding:4px 10px;min-width:60px;
}
.g-chip-label{font-size:.6rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:2px;}
.g-chip-value{font-family:'Noto Sans Tamil',sans-serif;font-size:.95rem;font-weight:500;}

.chip-root  {background:#fff3e0;border:1px solid #ffd08a;}
.chip-root .g-chip-label{color:#8a5000;}
.chip-root .g-chip-value{color:#5a3000;}

.chip-suffix{background:#e8f4ff;border:1px solid #90c8ff;}
.chip-suffix .g-chip-label{color:#00478a;}
.chip-suffix .g-chip-value{color:#003060;}

.chip-pos   {background:#eaffea;border:1px solid #90e090;}
.chip-pos .g-chip-label{color:#005a00;}
.chip-pos .g-chip-value{color:#003000;font-size:.82rem;}

.chip-mood  {background:#fff0f8;border:1px solid #ffb0d8;}
.chip-mood .g-chip-label{color:#7a0040;}
.chip-mood .g-chip-value{color:#500020;font-size:.82rem;}

/* Meaning sections */
.sec{margin-bottom:.8rem;border-radius:9px;overflow:hidden;}
.sec-head{font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;padding:.3rem .75rem;}
.sec-body{font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;font-size:1rem;line-height:1.95;padding:.6rem .85rem;}
.s-def{background:#fff8e7;border:1px solid #f3d98b;}
.s-def .sec-head{background:#fef0c0;color:#7a5000;}
.s-def .sec-body{color:#3a2a00;}
.s-ex {background:#f0f7ff;border:1px solid #b8d8f8;}
.s-ex .sec-head{background:#dbeeff;color:#1a4a8a;}
.s-ex .sec-body{color:#1a3a6a;font-style:italic;}
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
# MORPHOLOGICAL ENGINE
# Maps suffix → (meaning_in_tamil, grammatical_mood, part_of_speech)
# ══════════════════════════════════════════════════════════════════════════════

SUFFIX_MORPHOLOGY = [
    # Conditional (நிபந்தனை வினையெச்சம்)
    ("யினால்",   "நிபந்தனை: -ஆல்",      "நிபந்தனை (if/because)"),
    ("வதினால்",  "நிபந்தனை: -வதால்",     "நிபந்தனை (because)"),
    ("தினால்",   "நிபந்தனை: -தால்",      "நிபந்தனை (if/because)"),
    ("டினால்",   "நிபந்தனை: -டால்",      "நிபந்தனை (if)"),
    ("றினால்",   "நிபந்தனை: -றால்",      "நிபந்தனை (if)"),
    ("னினால்",   "நிபந்தனை: -னால்",      "நிபந்தனை (if)"),
    ("இனால்",    "நிபந்தனை: -இனால்",     "நிபந்தனை (if/when)"),
    ("ினால்",    "நிபந்தனை: -னால்",      "நிபந்தனை (if/when)"),
    ("னால்",     "நிபந்தனை: -னால்",      "நிபந்தனை (if)"),
    ("ால்",      "நிபந்தனை: -ால்",       "நிபந்தனை (if/by)"),
    # Past tense (இறந்த கால விகுதி)
    ("ட்டான்",   "இறந்த காலம்: அவன்",    "வினைமுற்று — இறந்த காலம்"),
    ("ட்டாள்",   "இறந்த காலம்: அவள்",    "வினைமுற்று — இறந்த காலம்"),
    ("ட்டார்",   "இறந்த காலம்: அவர்",    "வினைமுற்று — இறந்த காலம்"),
    ("ட்டார்கள்","இறந்த காலம்: அவர்கள்","வினைமுற்று — இறந்த காலம்"),
    ("ட்டேன்",   "இறந்த காலம்: நான்",    "வினைமுற்று — இறந்த காலம்"),
    ("தான்",     "இறந்த காலம்: அவன்",    "வினைமுற்று — இறந்த காலம்"),
    ("தாள்",     "இறந்த காலம்: அவள்",    "வினைமுற்று — இறந்த காலம்"),
    ("தார்",     "இறந்த காலம்: அவர்",    "வினைமுற்று — இறந்த காலம்"),
    ("னான்",     "இறந்த காலம்: அவன்",    "வினைமுற்று — இறந்த காலம்"),
    ("னாள்",     "இறந்த காலம்: அவள்",    "வினைமுற்று — இறந்த காலம்"),
    ("னார்",     "இறந்த காலம்: அவர்",    "வினைமுற்று — இறந்த காலம்"),
    # Present tense (நிகழ் கால விகுதி)
    ("கிறான்",   "நிகழ் காலம்: அவன்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கிறாள்",   "நிகழ் காலம்: அவள்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கிறார்",   "நிகழ் காலம்: அவர்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கிறார்கள்","நிகழ் காலம்: அவர்கள்","வினைமுற்று — நிகழ் காலம்"),
    ("கிறேன்",   "நிகழ் காலம்: நான்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கிறோம்",   "நிகழ் காலம்: நாம்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கிறது",    "நிகழ் காலம்: அது",     "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றான்", "நிகழ் காலம்: அவன்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றார்", "நிகழ் காலம்: அவர்",    "வினைமுற்று — நிகழ் காலம்"),
    ("கின்றது",  "நிகழ் காலம்: அது",     "வினைமுற்று — நிகழ் காலம்"),
    # Future tense (எதிர் கால விகுதி)
    ("வான்",     "எதிர் காலம்: அவன்",    "வினைமுற்று — எதிர் காலம்"),
    ("வாள்",     "எதிர் காலம்: அவள்",    "வினைமுற்று — எதிர் காலம்"),
    ("வார்",     "எதிர் காலம்: அவர்",    "வினைமுற்று — எதிர் காலம்"),
    ("வார்கள்",  "எதிர் காலம்: அவர்கள்","வினைமுற்று — எதிர் காலம்"),
    ("வேன்",     "எதிர் காலம்: நான்",    "வினைமுற்று — எதிர் காலம்"),
    ("வோம்",     "எதிர் காலம்: நாம்",    "வினைமுற்று — எதிர் காலம்"),
    ("பான்",     "எதிர் காலம்: அவன்",    "வினைமுற்று — எதிர் காலம்"),
    ("பார்",     "எதிர் காலம்: அவர்",    "வினைமுற்று — எதிர் காலம்"),
    # Verbal participle (வினையெச்சம்)
    ("வதால்",    "வினையெச்சம்: காரணம்",  "வினையெச்சம்"),
    ("வது",      "வினையெச்சம்: செயல்",   "வினையெச்சம் (verbal noun)"),
    ("வதை",      "வினையெச்சம்: செயல்",   "வினையெச்சம்"),
    ("வதற்கு",   "வினையெச்சம்: நோக்கம்","வினையெச்சம் (infinitive)"),
    # Passive (செயப்பாட்டு வினை)
    ("ப்படும்",  "செயப்பாட்டு வினை",    "செயப்பாட்டு வினை (passive)"),
    ("ப்பட்டது", "செயப்பாட்டு இறந்த காலம்","செயப்பாட்டு வினை (passive past)"),
    ("க்கப்படும்","செயப்பாட்டு வினை",   "செயப்பாட்டு வினை (passive)"),
    # Case suffixes (வேற்றுமை விகுதி)
    ("த்தில்",   "இடவேற்றுமை: -இல்",    "பெயர்ச்சொல் + இடவேற்றுமை (locative)"),
    ("த்தை",     "இரண்டாம் வேற்றுமை: -ஐ","பெயர்ச்சொல் + இரண்டாம் வேற்றுமை (accusative)"),
    ("த்தின்",   "ஆறாம் வேற்றுமை: -இன்","பெயர்ச்சொல் + ஆறாம் வேற்றுமை (genitive)"),
    ("த்துக்கு", "நான்காம் வேற்றுமை: -கு","பெயர்ச்சொல் + நான்காம் வேற்றுமை (dative)"),
    ("யில்",     "இடவேற்றுமை: -இல்",    "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("யை",       "இரண்டாம் வேற்றுமை",   "பெயர்ச்சொல் + இரண்டாம் வேற்றுமை"),
    ("யின்",     "ஆறாம் வேற்றுமை",      "பெயர்ச்சொல் + ஆறாம் வேற்றுமை"),
    ("யிடம்",    "இடவேற்றுமை: -இடம்",   "பெயர்ச்சொல் + இடவேற்றுமை"),
    ("கள்",      "பன்மை விகுதி",         "பன்மை (plural)"),
    ("இல்",      "இடவேற்றுமை: -இல்",    "இடவேற்றுமை (locative)"),
    ("ஐ",        "இரண்டாம் வேற்றுமை",   "இரண்டாம் வேற்றுமை (accusative)"),
    ("கு",       "நான்காம் வேற்றுமை",   "நான்காம் வேற்றுமை (dative)"),
    ("ஆல்",      "மூன்றாம் வேற்றுமை: -ஆல்","மூன்றாம் வேற்றுமை (instrumental)"),
    ("உடன்",     "உடனிகழ்ச்சி: -உடன்",  "உடனிகழ்ச்சி (comitative)"),
    ("யுடன்",    "உடனிகழ்ச்சி: -உடன்",  "உடனிகழ்ச்சி (comitative)"),
    ("இருந்து",  "ஐந்தாம் வேற்றுமை: -இலிருந்து","ஐந்தாம் வேற்றுமை (ablative)"),
    ("உடைய",     "ஆறாம் வேற்றுமை: -உடைய","ஆறாம் வேற்றுமை (genitive)"),
    ("ஆக",       "இரண்டாம் வேற்றுமை: -ஆக","நிலை (manner/as)"),
    ("ஆன",       "பண்புப்பெயர் விகுதி",  "பண்புப்பெயர் (adjective)"),
    ("ஆனது",     "நாமகரண வினை",          "வினை பெயர் (verbal noun)"),
    ("ஆகும்",    "எதிர்கால வினைமுற்று",  "வினைமுற்று — எதிர் காலம்"),
    ("என்று",    "மேற்கோள் விகுதி",      "மேற்கோள் (quotative)"),
    ("இல்லாமல்", "எதிர்மறை வினையெச்சம்","எதிர்மறை வினையெச்சம் (negative)"),
    ("ஆக",       "வகை/முறை குறிப்பு",    "குறிப்பு வினையெச்சம்"),
]

# Sandhi corrections: after stripping suffix, stem may need ending fix
SANDHI_CORRECTIONS = [
    ("ந்த",   "ந்தம்"),
    ("ட்ட",   "ட்டம்"),
    ("க்க",   "க்கம்"),
    ("ல்ல",   "ல்"),
    ("ன்ன",   "ன்னம்"),
    ("ர்த்த", "ர்த்தம்"),
]

def analyze_morphology(word: str) -> dict:
    """
    Returns:
        root        — வேர்ச்சொல் (base form)
        suffix      — stripped suffix
        suffix_tamil — suffix meaning in Tamil
        pos         — part of speech in Tamil
        root_is_verb — bool
    """
    w = clean_word(word)
    for suffix, suffix_tamil, pos in SUFFIX_MORPHOLOGY:
        if w.endswith(suffix) and len(w) > len(suffix) + 1:
            stem = w[:-len(suffix)]
            # Apply sandhi correction
            for tail, replacement in SANDHI_CORRECTIONS:
                if stem.endswith(tail):
                    stem = stem[:-len(tail)] + replacement
                    break
            return {
                "root":         stem,
                "suffix":       suffix,
                "suffix_tamil": suffix_tamil,
                "pos":          pos,
                "root_is_verb": "வினை" in pos or "verbal" in pos.lower(),
                "modified":     True,
            }
    # No suffix found — word is already in base form
    return {
        "root":         w,
        "suffix":       None,
        "suffix_tamil": None,
        "pos":          None,
        "root_is_verb": False,
        "modified":     False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN DICTIONARY
# Format: word → {pos, tamil_def, example, doc_context, note(optional)}
# pos: வினைச்சொல் / பெயர்ச்சொல் / உரிச்சொல் / வினையடை etc.
# ══════════════════════════════════════════════════════════════════════════════
DICTIONARY = {

    # ── HIGH-FREQUENCY VERBS (வினைச்சொற்கள்) ─────────────────────────────
    "விரும்பு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒன்றை ஆசைப்படுவது, விரும்புவது, பிரியமாக நினைப்பது — ஒரு செயலை செய்ய விழைவது",
        "example": "அவர் இந்த வேலையை விரும்புகிறார். | நீங்கள் விரும்பினால் ஒப்பந்தம் ரத்து செய்யலாம்.",
        "doc_context": "ஆவணத்தில் 'விரும்பினால்' என்றால் — உங்களுக்கு விருப்பம் இருந்தால் / நீங்கள் ஒப்புக்கொண்டால் என்று பொருள். இது ஒரு விருப்பத்தை மட்டுமே குறிக்கிறது, கட்டாயமில்லை.",
    },
    "செய்": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு செயலை நடத்துவது / நிறைவேற்றுவது",
        "example": "அவர் வேலை செய்கிறார். | ஒப்பந்தம் செய்யப்பட்டது.",
        "doc_context": "ஆவணத்தில் 'செய்யப்பட்டது' என்றால் — அந்த செயல் முடிக்கப்பட்டது என்று பொருள்.",
    },
    "கொடு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒருவருக்கு ஒன்றை அளிப்பது / வழங்குவது",
        "example": "நீதிமன்றம் தீர்ப்பு கொடுத்தது.",
        "doc_context": "ஆவணத்தில் கொடுக்கப்பட்டது / வழங்கப்பட்டது என்பது சட்டரீதியான அனுமதியை குறிக்கும்.",
    },
    "பெறு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒன்றை கைக்கொள்வது / பெற்றுக்கொள்வது / கிடைப்பது",
        "example": "அனுமதி பெறப்பட்டது.",
        "doc_context": "ஆவணத்தில் 'பெறப்பட்டது' என்றால் சட்டரீதியான ஒப்புதல் கிடைத்தது என்று பொருள்.",
    },
    "தெரிவி": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு தகவலை அறிவிப்பது / சொல்வது / தெரியப்படுத்துவது",
        "example": "விண்ணப்பதாரர் தன் முகவரியை தெரிவிக்க வேண்டும்.",
        "doc_context": "ஆவணத்தில் 'தெரிவிக்கப்படுகிறது' என்றால் அதிகாரப்பூர்வமாக அறிவிக்கப்படுகிறது என்று பொருள்.",
    },
    "ஒப்புக்கொள்": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு விஷயத்திற்கு தன் சம்மதத்தை தெரிவிப்பது / ஏற்றுக்கொள்வது",
        "example": "இரு தரப்பினரும் இந்த விதிமுறைகளை ஒப்புக்கொண்டனர்.",
        "doc_context": "ஒப்பந்தத்தில் 'ஒப்புக்கொள்கிறோம்' என்று வந்தால் அது சட்டரீதியான கட்டுப்பாடு.",
    },
    "சமர்பி": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஆவணங்களை அலுவலகத்தில் கொடுப்பது / தாக்கல் செய்வது",
        "example": "விண்ணப்பதாரர் ஆவணங்களை சமர்பித்தார்.",
        "doc_context": "சமர்பித்த பிறகு ரசீது வாங்க வேண்டும்.",
    },
    "நிர்ணயி": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு தொகை அல்லது முடிவை நிறுவுவது / தீர்மானிப்பது",
        "example": "கட்டணம் அரசால் நிர்ணயிக்கப்படும்.",
        "doc_context": "ஆவணத்தில் 'நிர்ணயிக்கப்பட்டது' என்றால் அரசு அல்லது நீதிமன்றம் தீர்மானித்தது என்று பொருள்.",
    },
    "நடத்து": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு நடவடிக்கையை நிறைவேற்றுவது / நிர்வகிப்பது",
        "example": "நிர்வாகம் திட்டத்தை நடத்துகிறது.",
        "doc_context": "ஆவணத்தில் 'நடத்தப்படும்' என்றால் நடவடிக்கை தொடரும் என்று பொருள்.",
    },
    "அனுமதி": {
        "pos": "பெயர்ச்சொல் / வினைச்சொல்",
        "tamil_def": "ஒரு செயல் செய்வதற்கு அதிகாரப்பூர்வ ஒப்புதல் கொடுப்பது",
        "example": "கட்டிடம் கட்ட நகராட்சி அனுமதி பெற வேண்டும்.",
        "doc_context": "அரசு அனுமதி இல்லாமல் செய்யப்பட்ட செயல் சட்டவிரோதமாகலாம்.",
    },
    "வழங்கு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "அளிப்பது / கொடுப்பது — பொதுவாக அரசு அல்லது அதிகாரி கொடுக்கும்போது பயன்படும்",
        "example": "அரசு சான்றிதழ் வழங்குகிறது.",
        "doc_context": "ஆவணத்தில் 'வழங்கப்படும்' என்றால் அரசு கொடுக்கும் என்று அதிகாரப்பூர்வமாக உறுதியளிக்கிறது.",
    },
    "கோரு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒன்றை தர வேண்டும் என்று கேட்பது / உரிமை கோருவது",
        "example": "வாரிசு சொத்தை கோருகிறார்.",
        "doc_context": "ஆவணத்தில் 'கோரப்பட்டது' என்றால் சட்டரீதியான கோரிக்கை வைக்கப்பட்டது என்று பொருள்.",
    },
    "மீறு": {
        "pos": "வினைச்சொல்",
        "tamil_def": "ஒரு கட்டளை அல்லது விதிமுறையை கடப்பது / பின்பற்றாமல் போவது",
        "example": "ஒப்பந்தத்தை மீறினால் வழக்கு தொடரலாம்.",
        "doc_context": "ஆவணத்தில் 'மீறினால்' என்று வந்தால் — அப்படி செய்தால் சட்ட நடவடிக்கை நடக்கும் என்று எச்சரிக்கை.",
    },

    # ── HIGH-FREQUENCY NOUNS (பெயர்ச்சொற்கள்) ────────────────────────────
    "இனிமேல்": {
        "pos": "வினையடை (adverb)",
        "tamil_def": "இப்போதிலிருந்து / இனி முதல் / இந்த நாளிலிருந்து என்று பொருள். ஒரு மாற்றம் நடைமுறைக்கு வருகிறது என்று குறிக்கும்",
        "example": "இனிமேல் இந்த நிலம் உங்கள் பெயரில் இருக்கும். | இனிமேல் வாடகை 5000 ரூபாய் ஆகும்.",
        "doc_context": "ஒப்பந்தம் அல்லது ஆணையில் 'இனிமேல்' என்று வந்தால் — இந்த ஆவணம் கையொப்பமிட்ட நாளிலிருந்தே நடைமுறைக்கு வரும் என்று பொருள்.",
    },
    "உரிமையாளர்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒரு சொத்தை சட்டரீதியாக வைத்திருப்பவர் — நிலம், வீடு அல்லது பொருளின் சொந்தக்காரர்",
        "example": "இந்த வீட்டின் உரிமையாளர் திரு. ராமசாமி.",
        "doc_context": "ஆவணத்தில் 'உரிமையாளர்' என்று வந்தால் அந்த சொத்தை பட்டாவில் பெயர் உள்ளவர்.",
        "note": "உரிமையாளர் பெயர் பட்டாவில் பதிவு ஆகியிருக்க வேண்டும்."
    },
    "உரிமை": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒரு நபருக்கு சட்டப்படி சேர்ந்த அதிகாரம் அல்லது சொத்து — right என்பதன் தமிழ்",
        "example": "இந்த நிலத்தின் உரிமை அவருக்கு சேரும்.",
        "doc_context": "சட்ட ஆவணத்தில் உரிமை என்பது சட்டரீதியான கோரிக்கை வைக்கும் தகுதி.",
    },
    "தரப்பு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒப்பந்தத்தில் பங்கு பெறும் நபர் அல்லது குழு — party என்பதன் தமிழ்",
        "example": "முதல் தரப்பு விற்பவர், இரண்டாம் தரப்பு வாங்குபவர்.",
        "doc_context": "ஒப்பந்தத்தில் இரண்டு தரப்பினரும் கட்டாயம் கையொப்பமிட வேண்டும்.",
    },
    "தரப்பினர்": {
        "pos": "பெயர்ச்சொல் — பன்மை",
        "tamil_def": "ஒப்பந்தத்தில் பங்கேற்கும் நபர்கள் — parties என்பதன் தமிழ்",
        "example": "இரு தரப்பினரும் ஒப்பந்தத்தில் ஒப்புக்கொண்டனர்.",
        "doc_context": "ஒப்பந்தத்தில் அனைத்து தரப்பினரும் கையொப்பமிட்டால் மட்டுமே ஆவணம் செல்லுபடியாகும்.",
    },
    "ஒப்பந்தம்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "இரண்டு அல்லது அதிக நபர்களிடையே எழுத்தில் செய்யப்படும் சட்டரீதியான உடன்படிக்கை — agreement / contract என்பதன் தமிழ்",
        "example": "வீடு வாடகைக்கு கொடுக்க ஒப்பந்தம் செய்யப்பட்டது.",
        "doc_context": "ஒப்பந்தம் மீறினால் நீதிமன்றம் செல்லலாம். ஸ்டாம்ப் பேப்பரில் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "note": "படிக்காமல் கையொப்பமிடாதீர்கள்."
    },
    "சுமார்": {
        "pos": "வினையடை",
        "tamil_def": "தோராயமாக / கிட்டத்தட்ட / சரியான எண்ணிக்கை தெரியாதபோது மதிப்பிடும் வார்த்தை — approximately என்பதன் தமிழ்",
        "example": "சுமார் 40 வயது என்று ஆவணத்தில் குறிப்பிடப்பட்டுள்ளது.",
        "doc_context": "ஆவணத்தில் வயது அல்லது அளவு சரியாக தெரியாவிட்டால் 'சுமார்' என்று போட்டு மதிப்பீடு செய்வார்கள்.",
    },
    "மேற்கண்ட": {
        "pos": "உரிச்சொல்",
        "tamil_def": "இந்த வரிக்கு மேலே குறிப்பிட்டது — above-mentioned என்பதன் தமிழ்",
        "example": "மேற்கண்ட விவரங்கள் சரியானவை என்று சான்றளிக்கிறேன்.",
        "doc_context": "ஆவணத்தில் 'மேற்கண்ட' என்றால் — இந்த வாக்கியத்திற்கு மேலே எழுதியவற்றை குறிக்கிறது.",
    },
    "கீழ்க்கண்ட": {
        "pos": "உரிச்சொல்",
        "tamil_def": "இந்த வரிக்கு கீழே குறிப்பிடப்படுவது — below-mentioned / following என்பதன் தமிழ்",
        "example": "கீழ்க்கண்ட விதிமுறைகளை பின்பற்ற வேண்டும்.",
        "doc_context": "ஆவணத்தில் 'கீழ்க்கண்ட' என்றால் — இனி வரும் வரிகளில் சொல்லப்போவதை குறிக்கிறது.",
    },
    "நிபந்தனை": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒப்பந்தத்தில் கட்டாயம் பின்பற்ற வேண்டிய நிலை அல்லது கட்டுப்பாடு — condition / term என்பதன் தமிழ்",
        "example": "இந்த நிபந்தனைக்கு உட்பட்டு நிலம் வழங்கப்படும்.",
        "doc_context": "நிபந்தனை மீறினால் ஒப்பந்தம் தானாக ரத்தாகும் / நிறைவேறாது.",
    },
    "விதிமுறை": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "பின்பற்ற வேண்டிய கட்டாய நியதிகள் — terms and conditions என்பதன் தமிழ்",
        "example": "ஒப்பந்தத்தின் விதிமுறைகளை மீறினால் நடவடிக்கை எடுக்கப்படும்.",
        "doc_context": "விதிமுறைகளை கவனமாக படியுங்கள் — கையொப்பமிட்டால் எல்லாவற்றையும் ஒப்புக்கொண்டதாகும்.",
    },
    "காலக்கெடு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒரு வேலையை முடிக்க அல்லது விண்ணப்பிக்க கடைசி நாள் — deadline என்பதன் தமிழ்",
        "example": "விண்ணப்பிக்க காலக்கெடு 31 மார்ச் 2024.",
        "doc_context": "காலக்கெடு தாண்டினால் விண்ணப்பம் ஏற்கப்படாது.",
        "note": "காலக்கெடுவை மீறாதீர்கள் — நீட்டிப்பு கிடைக்காது."
    },
    "ரத்து": {
        "pos": "வினைச்சொல் / பெயர்ச்சொல்",
        "tamil_def": "ஒரு முடிவை அல்லது ஒப்பந்தத்தை செல்லாததாக்குவது — cancel / revoke என்பதன் தமிழ்",
        "example": "கட்டணம் கட்டாததால் விண்ணப்பம் ரத்து செய்யப்பட்டது.",
        "doc_context": "ஆவணம் ரத்து ஆனால் அதன் மீது எந்த உரிமையும் கிடையாது.",
    },
    "நஷ்டஈடு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒருவரால் ஏற்பட்ட நஷ்டத்திற்கு கொடுக்கப்படும் பணம் — compensation / damages என்பதன் தமிழ்",
        "example": "ஒப்பந்தம் மீறினால் நஷ்டஈடு கொடுக்க வேண்டும்.",
        "doc_context": "நஷ்டஈடு தொகை ஒப்பந்தத்திலேயே முன்கூட்டியே குறிப்பிடப்படும்.",
    },
    "முன்பணம்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒப்பந்தம் செய்யும்போது முன்கூட்டியே கொடுக்கும் பணம் — advance payment என்பதன் தமிழ்",
        "example": "வீட்டிற்கு 50,000 ரூபாய் முன்பணம் கொடுத்தார்.",
        "doc_context": "முன்பணம் கொடுத்தால் ரசீது வாங்க வேண்டும். ஒப்பந்தம் ரத்தானால் முன்பணம் திரும்ப கிடைக்கும்.",
    },
    "வாடகை": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "வீடு அல்லது நிலத்தை பயன்படுத்துவதற்காக மாதந்தோறும் கொடுக்கும் பணம் — rent என்பதன் தமிழ்",
        "example": "மாதந்தோறும் 5000 ரூபாய் வாடகை செலுத்த வேண்டும்.",
        "doc_context": "வாடகை ஒப்பந்தத்தில் தொகை, செலுத்தும் தேதி, காலம் தெளிவாக இருக்க வேண்டும்.",
    },
    "பட்டா": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "நிலத்தின் உரிமை பத்திரம் — நீங்கள் அந்த நிலத்தின் சட்டபூர்வ உரிமையாளர் என்பதை அரசு உறுதி செய்யும் ஆவணம்",
        "example": "ரமேஷிடம் அவரது நிலத்திற்கு பட்டா இருக்கிறது.",
        "doc_context": "பட்டா இல்லாமல் நிலத்தை விற்கவோ அடமானம் வைக்கவோ முடியாது.",
        "note": "பட்டாவில் உங்கள் பெயர் இல்லையென்றால் நீங்கள் சட்டபூர்வமாக உரிமையாளர் அல்ல."
    },
    "சிட்டா": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "நிலத்தின் விவரங்களை கொண்ட அரசு பதிவு ஆவணம் — நிலத்தின் அளவு, வகை, உரிமையாளர் பெயர் இதில் இருக்கும்",
        "example": "சிட்டாவில் நிலத்தின் அளவு 2 ஏக்கர் என்று குறிப்பிடப்பட்டுள்ளது.",
        "doc_context": "தமிழ்நாட்டில் நிலம் வாங்கும்போது சிட்டா + பட்டா இரண்டும் தேவை.",
    },
    "சர்வே": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "நிலத்தை அளந்து ஒவ்வொரு நிலத்திற்கும் தனி எண் கொடுக்கும் அரசு நடவடிக்கை",
        "example": "இந்த நிலத்தின் சர்வே எண் 45/2.",
        "doc_context": "நிலம் வாங்க, விற்க, அடமானம் வைக்க சர்வே எண் கட்டாயம் தேவை.",
    },
    "சான்றிதழ்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒரு விஷயம் உண்மை என்று அரசு உறுதி செய்யும் ஆவணம் — certificate என்பதன் தமிழ்",
        "example": "சாதி சான்றிதழ் வேலைக்கு விண்ணப்பிக்க தேவை.",
        "doc_context": "அரசு அதிகாரி கையொப்பமிட்ட சான்றிதழ் மட்டுமே செல்லுபடியாகும்.",
    },
    "அரசாணை": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "அரசு அதிகாரப்பூர்வமாக பிறப்பிக்கும் ஆணை — Government Order (G.O.) என்பதன் தமிழ்",
        "example": "இந்த திட்டம் அரசாணை எண் 150 மூலம் அனுமதிக்கப்பட்டது.",
        "doc_context": "அரசாணை என்பது கட்டாயம் பின்பற்ற வேண்டிய அரசு உத்தரவு. மீறினால் சட்ட நடவடிக்கை வரும்.",
    },
    "மனு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "குறை தீர்க்க அல்லது ஒரு விஷயத்திற்கு அரசிடம் கோரும் கடிதம் — petition என்பதன் தமிழ்",
        "example": "நிலம் சம்பந்தமாக கலெக்டரிடம் மனு சமர்ப்பித்தார்.",
        "doc_context": "மனு கொடுத்த பிறகு ரசீது வாங்க வேண்டும். மனு எண் வைத்திருங்கள்.",
    },
    "வழக்கு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "நீதிமன்றத்தில் தீர்வு காண தாக்கல் செய்யப்படும் புகார் — case / lawsuit என்பதன் தமிழ்",
        "example": "நிலம் சம்பந்தமாக நீதிமன்றத்தில் வழக்கு தாக்கல் செய்தார்.",
        "doc_context": "வழக்கு தாக்கல் ஆனால் வழக்கு எண் வைத்திருங்கள். இது எல்லா ஆவணங்களிலும் தேவைப்படும்.",
    },
    "தீர்ப்பு": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "நீதிமன்றம் வழக்கில் கொடுக்கும் இறுதி முடிவு — judgment / verdict என்பதன் தமிழ்",
        "example": "நீதிமன்றம் வாதிக்கு சாதகமாக தீர்ப்பு அளித்தது.",
        "doc_context": "தீர்ப்புக்கு எதிராக உயர் நீதிமன்றத்தில் மேல்முறையீடு செய்யலாம்.",
    },
    "கட்டணம்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "சேவைக்காக செலுத்த வேண்டிய பணம் — fee / charge என்பதன் தமிழ்",
        "example": "பதிவுக்கு கட்டணம் கட்ட வேண்டும்.",
        "doc_context": "அரசு நிர்ணயிக்கும் கட்டணம் மட்டுமே செலுத்த வேண்டும். கூடுதலாக கேட்டால் புகார் அளிக்கலாம்.",
    },
    "ரசீது": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "பணம் கட்டியதற்கான அல்லது ஆவணம் கொடுத்ததற்கான ஆதாரக் கடிதம் — receipt என்பதன் தமிழ்",
        "example": "கட்டணம் கட்டிய பிறகு ரசீது வாங்கினார்.",
        "doc_context": "ரசீது இல்லாமல் கட்டினேன் என்று நிரூபிக்க முடியாது. எப்போதும் ரசீது வாங்குங்கள்.",
        "note": "ரசீது இல்லாமல் கட்டினேன் என்று நிரூபிக்க முடியாது."
    },
    "அடமானம்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "கடன் வாங்க சொத்தை பாதுகாப்பாக வைப்பது — mortgage என்பதன் தமிழ்",
        "example": "வீட்டை அடமானம் வைத்து வங்கியில் கடன் வாங்கினார்.",
        "doc_context": "அடமான ஆவணம் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "note": "கடன் திரும்ப கொடுக்காவிட்டால் வங்கி சொத்தை ஏலம் போடலாம்."
    },
    "கையொப்பம்": {
        "pos": "பெயர்ச்சொல்",
        "tamil_def": "ஒரு ஆவணத்தில் நீங்கள் ஒப்புதல் அளிக்கும் கை எழுத்து — signature என்பதன் தமிழ்",
        "example": "ஆவணத்தில் கையொப்பமிட்டார்.",
        "doc_context": "கையொப்பமிட்ட ஆவணம் சட்டரீதியான ஒப்பந்தம். படிக்காமல் கையொப்பமிடாதீர்கள்.",
        "note": "படிக்காமல் கையொப்பமிடாதீர்கள்."
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# WORD CLEANER + TRANSLITERATION DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
def clean_word(w: str) -> str:
    return re.sub(r'^[\s,.\-;:"""\'()[\]/\\|]+|[\s,.\-;:"""\'()[\]/\\|]+$','',w).strip()

_REAL_EN = re.compile(
    r'\b(from|now|on|here|after|hereafter|owner|person|agreement|contract|property|'
    r'land|certificate|order|court|legal|district|revenue|government|right|claim|'
    r'witness|sign|date|number|area|name|address|amount|pay|tax|duty|document|'
    r'record|file|case|judge|petition|transfer|sale|lease|rent|survey|boundary|'
    r'house|building|the|this|that|and|or|of|in|to|for|with|by|at|an|a|is|are|'
    r'was|were|be|been|have|has|had|will|shall|may|can|must|should|would|could|'
    r'not|no|yes|new|old|first|last|total|one|two|three|want|wish|desire|love|'
    r'like|need|if|when|since|because|optional|voluntary)\b',
    re.IGNORECASE
)

def is_transliteration(tamil_input: str, result: str) -> bool:
    if not result or len(result.strip()) < 2: return True
    r = result.strip()
    if _REAL_EN.search(r): return False
    if re.match(r'^[A-Za-z]+$', r) and len(r) < 25: return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# LOOKUP ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
def dict_lookup(root: str):
    if root in DICTIONARY: return DICTIONARY[root]
    for v in _spelling_variants(root):
        if v in DICTIONARY: return DICTIONARY[v]
    return None

def _spelling_variants(w):
    sw=[("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in sw if a in w and w.replace(a,b,1)!=w]

def src_mymemory(word: str):
    try:
        r=requests.get("https://api.mymemory.translated.net/get",
            params={"q":word,"langpair":"ta|en"},timeout=4)
        if r.status_code==200:
            t=r.json().get("responseData",{}).get("translatedText","")
            if t and not is_transliteration(word,t) and len(t.strip())>1:
                return t.strip()
    except: pass
    return None

def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t=GoogleTranslator(source="ta",target="en").translate(word)
        if t and not is_transliteration(word,t): return t.strip()
    except: pass
    return None

def find_context(text: str, root: str):
    if not text or not root: return None
    for sent in re.split(r'(?<=[.!?\n])\s*', text):
        s = sent.strip()
        if root in s and len(s)>5: return s
    idx = text.find(root)
    if idx>=0:
        return "…"+text[max(0,idx-80):min(len(text),idx+len(root)+80)].strip()+"…"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str="") -> dict:
    w         = clean_word(word)
    morph     = analyze_morphology(w)
    root      = morph["root"]
    dict_res  = dict_lookup(root)
    # also try original if root lookup fails
    if not dict_res:
        dict_res = dict_lookup(w)
    ctx       = find_context(doc_text, root) or find_context(doc_text, w)
    online    = None
    if not dict_res:
        online = src_mymemory(w) or src_mymemory(root) or src_google(w)
    return {
        "word":    word,
        "clean":   w,
        "morph":   morph,
        "root":    root,
        "dict":    dict_res,
        "online":  online,
        "context": ctx,
        "found":   bool(dict_res or online),
    }


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word):
    try:
        buf=io.BytesIO(); gTTS(text=clean_word(word),lang="ta",slow=False).write_to_fp(buf)
        buf.seek(0); return buf
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
        while(i+1<len(out) and out[i+1]!=""
              and not cur.rstrip().endswith((".",":",")","?","!","।"))
              and len(cur)>8):
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

DOC_TYPES = {
    "பட்டா / நிலம்":     ["பட்டா","சிட்டா","survey","சர்வே","நிலம்","ஏக்கர்"],
    "வாடகை ஒப்பந்தம்":  ["வாடகை","குடியிருப்பவர்","rent","lease"],
    "அரசாணை (G.O.)":     ["G.O.","அரசாணை","government order","செயல்முறை"],
    "சான்றிதழ்":          ["சான்றிதழ்","certificate","பிறப்பு","சாதி","வருமானம்"],
    "சட்ட ஆவணம்":        ["மனு","petition","court","நீதிமன்றம்","வழக்கு"],
}
def detect_doc_type(text):
    t=text.lower()
    for dtype,kws in DOC_TYPES.items():
        if any(k.lower() in t for k in kws): return dtype
    return "அரசு ஆவணம்"

for k,v in [("text",""),("word",""),("doc_type","அரசு ஆவணம்")]:
    st.session_state.setdefault(k,v)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 தமிழ் அரசு ஆவண வாசகன்</h1>
  <p>Upload PDF or image · Extract text · Search any Tamil word · Tamil definition + Grammar root · 100% free</p>
</div>
""", unsafe_allow_html=True)

t_reader, t_deploy = st.tabs(["📄 ஆவண வாசகன்", "🚀 Deploy Guide"])

with t_reader:
    left, right = st.columns([3,2], gap="large")

    with left:
        st.markdown('<div class="slabel">படி 1 — ஆவணம் பதிவேற்றவும்</div>', unsafe_allow_html=True)
        uploaded=st.file_uploader("file",type=["pdf","png","jpg","jpeg"],label_visibility="collapsed")
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
                        except Exception as e: st.error(f"பிழை: {e}"); text=""
                else:
                    text=ocr_image(Image.open(uploaded))
                st.session_state.text=text
                st.session_state.doc_type=detect_doc_type(text)

        if st.session_state.text:
            st.markdown(f'<div class="doc-chip">📋 {st.session_state.doc_type}</div>', unsafe_allow_html=True)
            st.markdown('<div class="slabel">படி 2 — ஆவணம் படிக்கவும்</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 புரியாத சொல்லை கீழே dropdown-ல் தேர்வு செய்யுங்கள் அல்லது வலதில் தட்டச்சு செய்யுங்கள்</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)
            tw=sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t)>1})
            if tw:
                st.markdown('<div class="slabel" style="margin-top:.7rem">சொல் தேர்வு</div>', unsafe_allow_html=True)
                pick=st.selectbox("p",["— தேர்வு —"]+tw,label_visibility="collapsed",key="pick")
                if pick!="— தேர்வு —": st.session_state.word=pick
        else:
            st.info("மேலே PDF அல்லது படம் பதிவேற்றவும்.")

    with right:
        st.markdown('<div class="slabel">சொல் பொருள் + இலக்கண பகுப்பாய்வு</div>', unsafe_allow_html=True)
        typed=st.text_input("தமிழ் சொல்:", placeholder="உதா: விரும்பினால், இனிமேல், ஒப்பந்தம்", key="typed")
        if typed: st.session_state.word=typed.strip()

        w=st.session_state.word.strip()

        if w and is_tamil(clean_word(w)):
            with st.spinner("பகுப்பாய்கிறோம்…"):
                res  = lookup(w, st.session_state.text)
                audio= speak(w)

            m    = res["morph"]
            root = res["root"]
            d    = res["dict"]

            # ── WORD DISPLAY ──
            st.markdown(f'<div class="mcard"><div class="mword">{res["clean"]}</div>', unsafe_allow_html=True)

            # ── GRAMMAR ANALYSIS BAR ──
            chips = []
            chips.append(f'<div class="g-chip chip-root"><div class="g-chip-label">வேர்ச்சொல்</div><div class="g-chip-value">{root}</div></div>')
            if m["suffix"]:
                chips.append(f'<div class="g-chip chip-suffix"><div class="g-chip-label">விகுதி</div><div class="g-chip-value">{m["suffix"]}</div></div>')
            pos_display = d["pos"] if d else (m["pos"] or "—")
            chips.append(f'<div class="g-chip chip-pos"><div class="g-chip-label">இலக்கணம்</div><div class="g-chip-value">{pos_display}</div></div>')
            if m["suffix_tamil"]:
                chips.append(f'<div class="g-chip chip-mood"><div class="g-chip-label">விகுதி பொருள்</div><div class="g-chip-value">{m["suffix_tamil"]}</div></div>')
            st.markdown(f'<div class="grammar-bar">{"".join(chips)}</div>', unsafe_allow_html=True)

            # ── MEANING SECTIONS ──
            if res["found"]:
                if d:
                    st.markdown(f'<div class="sec s-def"><div class="sec-head">📖 தமிழ் பொருள் (வேர்ச்சொல்: {root})</div><div class="sec-body">{d["tamil_def"]}</div></div>', unsafe_allow_html=True)
                    if d.get("example"):
                        st.markdown(f'<div class="sec s-ex"><div class="sec-head">✏️ எடுத்துக்காட்டு வாக்கியம்</div><div class="sec-body">{d["example"]}</div></div>', unsafe_allow_html=True)
                    if d.get("doc_context"):
                        st.markdown(f'<div class="sec s-doc"><div class="sec-head">📋 அரசு ஆவணத்தில் பொருள்</div><div class="sec-body">{d["doc_context"]}</div></div>', unsafe_allow_html=True)
                    if d.get("note"):
                        st.markdown(f'<div class="sec s-note"><div class="sec-head">⚠️ கவனிக்க வேண்டியது</div><div class="sec-body">{d["note"]}</div></div>', unsafe_allow_html=True)
                elif res["online"]:
                    st.markdown(f'<div class="sec s-online"><div class="sec-head">🔤 பொருள் (English — ஆன்லைன்)</div><div class="sec-body">{res["online"]}</div></div>', unsafe_allow_html=True)
                if res["context"]:
                    st.markdown(f'<div class="sec s-note"><div class="sec-head">📄 உங்கள் ஆவணத்தில்</div><div class="sec-body">{res["context"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="notfound">⚠️ <strong>{res["clean"]}</strong> — வேர்ச்சொல் <strong>{root}</strong> — பொருள் கிடைக்கவில்லை.</div>', unsafe_allow_html=True)

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
    st.markdown("## 🚀 GitHub → Streamlit Cloud (API key தேவையில்லை)")
    st.info("✅ 100% இலவசம். எந்த API key-உம் வேண்டியதில்லை.")
    st.markdown("""
    <div class="step"><span class="num">1</span><a href="https://github.com" target="_blank">github.com</a> → Sign up (இலவசம்)</div>
    <div class="step"><span class="num">2</span>New repository → Name: <code>tamil-doc-reader</code> | Public → Create</div>
    <div class="step"><span class="num">3</span>3 files upload: <code>app.py</code>, <code>requirements.txt</code>, <code>packages.txt</code> → Commit</div>
    <div class="step"><span class="num">4</span><a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a> → GitHub sign in → New app → File: <code>app.py</code> → Deploy!</div>
    <div class="step"><span class="num">5</span>3–5 நிமிடம் → இலவச URL கிடைக்கும் ✅</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**`requirements.txt`**")
        st.code("streamlit>=1.32.0\npytesseract>=0.3.10\nPillow>=10.0.0\npdfplumber>=0.10.0\npdf2image>=1.16.0\ngTTS>=2.5.0\nrequests>=2.31.0\nbeautifulsoup4>=4.12.0\ndeep-translator>=1.11.4\nnumpy>=1.24.0",language="text")
    with c2:
        st.markdown("**`packages.txt`**")
        st.code("tesseract-ocr\ntesseract-ocr-tam\ntesseract-ocr-eng\npoppler-utils",language="text")
    st.success("✅ பணம் கட்ட வேண்டியதில்லை.")

st.markdown('<div style="text-align:center;font-size:.74rem;color:#bbb;margin-top:2rem;padding-top:.8rem;border-top:1px solid #ddd4c4;">தமிழ் அரசு ஆவண வாசகன் v9 · Tamil Morphological Engine · Built-in Dictionary · 100% Free</div>', unsafe_allow_html=True)
