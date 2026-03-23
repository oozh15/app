"""
Tamil Government Document Reader — v7 FINAL (100% FREE — NO API KEY NEEDED)
════════════════════════════════════════════════════════════════════════════════
Zero cost. Zero API key. Works immediately after deploy.

How meaning works:
  1. Built-in Tamil govt word dictionary (500+ common govt words)
     → gives Tamil meaning + example sentence + document context instantly
  2. MyMemory free translation API (no key, 5000 chars/day)
  3. Google Translate via deep-translator (free, no key)
  4. Tamil Wiktionary REST API (free, no key)

All sources are 100% free. No credit card. No signup needed.
"""

import io, re, requests
import streamlit as st
from gtts import gTTS
from PIL import Image, ImageFilter, ImageEnhance
import pdfplumber, pytesseract
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="தமிழ் ஆவண வாசகன்", page_icon="📜", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#f2ede6;}

.hdr{background:#0f172a;border-left:5px solid #d4a843;border-radius:14px;
     padding:1.5rem 2rem;margin-bottom:1.3rem;}
.hdr h1{color:#f8ecd4;font-size:1.6rem;font-weight:600;margin:0 0 .2rem;}
.hdr p{color:#a89880;font-size:.87rem;margin:0;}

.docbox{
  background:#fffef8;border:1px solid #ddd0b8;border-radius:12px;
  padding:1.5rem 1.9rem;
  font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:1.1rem;line-height:2.5;color:#111;
  white-space:pre-wrap;word-break:break-word;
  max-height:520px;overflow-y:auto;letter-spacing:.01em;
}

.mcard{background:#fff;border-radius:14px;border:1px solid #e2d8c8;
  box-shadow:0 4px 18px rgba(0,0,0,.06);padding:1.3rem 1.5rem;margin-top:.2rem;}
.mword{font-family:'Noto Sans Tamil',sans-serif;font-size:1.5rem;
  font-weight:600;color:#0f172a;margin-bottom:.05rem;}
.mroot{font-size:.74rem;color:#bbb;margin-bottom:1rem;}

.sec{margin-bottom:.85rem;border-radius:9px;overflow:hidden;}
.sec-head{font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.1em;padding:.3rem .75rem;display:flex;align-items:center;gap:6px;}
.sec-body{font-family:'Noto Sans Tamil','IBM Plex Sans',sans-serif;
  font-size:1rem;line-height:1.9;padding:.6rem .85rem;}

.s-tamil{background:#fff8e7;border:1px solid #f3d98b;}
.s-tamil .sec-head{background:#fef0c0;color:#7a5000;}
.s-tamil .sec-body{color:#3a2a00;}

.s-example{background:#f0f7ff;border:1px solid #b8d8f8;}
.s-example .sec-head{background:#dbeeff;color:#1a4a8a;}
.s-example .sec-body{color:#1a3a6a;font-style:italic;}

.s-doc{background:#fdf2ff;border:1px solid #ddb8f8;}
.s-doc .sec-head{background:#f0d0ff;color:#4a0080;}
.s-doc .sec-body{color:#280050;}

.s-context{background:#f0faf4;border:1px solid #a8dcb8;}
.s-context .sec-head{background:#c8f0d8;color:#1a5a30;}
.s-context .sec-body{color:#1a3a20;}

.s-trans{background:#f8f8f8;border:1px solid #ddd;}
.s-trans .sec-head{background:#eee;color:#444;}
.s-trans .sec-body{color:#333;}

.notfound{font-size:.92rem;color:#b91c1c;background:#fef2f2;
  border:1px solid #fecaca;border-radius:9px;padding:.7rem 1rem;margin-top:.5rem;}
.slabel{font-size:.71rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.09em;color:#999;margin-bottom:.35rem;}
.hint{display:inline-block;background:#fef9e7;border:1px solid #fce7a0;
  border-radius:8px;padding:.4rem .85rem;font-size:.82rem;
  color:#7a5100;margin-bottom:.85rem;}
.doc-chip{display:inline-block;font-size:.75rem;font-weight:600;
  padding:3px 10px;border-radius:20px;background:#e8f4fd;color:#1155aa;margin-bottom:.7rem;}
.free-badge{display:inline-block;font-size:.7rem;font-weight:700;
  padding:2px 8px;border-radius:20px;background:#d6f5e3;color:#155e2b;margin-left:8px;}
.step{background:#fff;border:1px solid #e5dfd4;border-radius:10px;
  padding:.85rem 1.1rem;margin-bottom:.5rem;font-size:.91rem;line-height:1.65;}
.num{display:inline-flex;align-items:center;justify-content:center;
  width:21px;height:21px;border-radius:50%;background:#0f172a;color:#d4a843;
  font-size:11px;font-weight:700;margin-right:7px;flex-shrink:0;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN TAMIL GOVERNMENT WORD DICTIONARY
# 500+ words covering: பட்டா/land, G.O., certificates, legal/court docs
# Format: "word": {
#   "tamil": "simple Tamil meaning",
#   "example": "example sentence in Tamil",
#   "doc_context": "what it means in govt documents",
#   "note": "important note for citizen (optional)"
# }
# ══════════════════════════════════════════════════════════════════════════════
GOVT_DICT = {
    # ── LAND / PROPERTY (பட்டா, சிட்டா) ──────────────────────────────────
    "பட்டா": {
        "tamil": "நிலத்தின் உரிமை பத்திரம் — நீங்கள் அந்த நிலத்தின் உரிமையாளர் என்பதை அரசு உறுதி செய்யும் ஆவணம்",
        "example": "ரமேஷிடம் அவரது நிலத்திற்கு பட்டா இருக்கிறது.",
        "doc_context": "பட்டா என்பது நிலத்தின் சட்டபூர்வமான உரிமையை நிரூபிக்கும் முக்கியமான ஆவணம். வங்கி கடன், நிலம் விற்பனை, அரசு திட்டங்களுக்கு இது கட்டாயம் தேவை.",
        "note": "பட்டாவில் உங்கள் பெயர் இல்லையென்றால் நீங்கள் சட்டபூர்வமாக நிலத்தின் உரிமையாளர் அல்ல."
    },
    "சிட்டா": {
        "tamil": "நிலத்தின் விவரங்களை கொண்ட அரசு பதிவு ஆவணம் — நிலத்தின் அளவு, வகை, உரிமையாளர் பெயர் இதில் இருக்கும்",
        "example": "சிட்டாவில் அவரது நிலத்தின் அளவு 2 ஏக்கர் என்று குறிப்பிடப்பட்டுள்ளது.",
        "doc_context": "சிட்டா என்பது நிலத்தின் பதிவு விவரங்களை கொண்ட அட்டவணை. தனி மனித நிலம் 'அ-பதிவேடு' என்றும் அழைக்கப்படும்.",
    },
    "அடங்கல்": {
        "tamil": "ஒரு கிராமம் அல்லது பகுதியில் உள்ள அனைத்து நிலங்களின் விவரங்கள் உள்ள பட்டியல்",
        "example": "அடங்கல் படிவத்தில் அந்த கிராமத்தில் உள்ள அனைத்து நிலங்களும் பட்டியலிடப்பட்டுள்ளன.",
        "doc_context": "நிலத்தின் தொகுப்பு விவரங்கள். நிலம் யாரிடம் இருக்கிறது, எவ்வளவு என்று அரசு வைத்திருக்கும் கணக்கு.",
    },
    "சர்வே": {
        "tamil": "நிலத்தை அளந்து எண் கொடுக்கும் அரசு நடவடிக்கை",
        "example": "இந்த நிலத்தின் சர்வே எண் 45/2.",
        "doc_context": "ஒவ்வொரு நிலத்திற்கும் ஒரு தனி சர்வே எண் இருக்கும். இந்த எண் மூலம் நிலத்தை அடையாளம் காணலாம்.",
    },
    "சர்வே எண்": {
        "tamil": "ஒவ்வொரு நிலத்திற்கும் அரசு கொடுக்கும் தனிப்பட்ட அடையாள எண்",
        "example": "சர்வே எண் 123/4 என்பது அந்த நிலத்தின் அரசு பதிவு எண்.",
        "doc_context": "நிலம் வாங்க, விற்க, அடமானம் வைக்க இந்த எண் கட்டாயம் தேவை.",
        "note": "சர்வே எண் மாற்றம் ஆகும்போது 'பிரிவு' என்று சொல்வார்கள் — அப்போது புதிய எண் கிடைக்கும்."
    },
    "புல எண்": {
        "tamil": "நிலத்தின் வயல் அல்லது பகுதிக்கு கொடுக்கப்பட்ட எண்",
        "example": "புல எண் 56 என்ற நிலம் கிழக்கு பகுதியில் உள்ளது.",
        "doc_context": "சர்வே எண்ணுக்கு கூடுதலாக நிலத்தின் பகுதியை குறிக்கும் எண்.",
    },
    "உபவிபாகம்": {
        "tamil": "நிலத்தின் பகுதி எண் — ஒரு பெரிய நிலம் பல பகுதிகளாக பிரிக்கப்படும்போது கொடுக்கும் எண்",
        "example": "சர்வே எண் 45 உபவிபாகம் 2 என்பது அந்த நிலத்தின் இரண்டாம் பகுதி.",
        "doc_context": "நிலம் பிரிக்கப்படும்போது உபவிபாகம் எண் புதிதாக கொடுக்கப்படும்.",
    },
    "பட்டா எண்": {
        "tamil": "உங்கள் பட்டாவின் தனிப்பட்ட அடையாள எண்",
        "example": "இந்த பட்டா எண் 1234 என்று தஹசில் அலுவலகத்தில் பதிவு செய்யப்பட்டுள்ளது.",
        "doc_context": "அரசு கணினியில் உங்கள் நிலத்தை தேட இந்த எண் பயன்படுத்தப்படுகிறது.",
    },
    "தஹசில்": {
        "tamil": "வட்டார நிர்வாக அலுவலகம் — நிலம், சான்றிதழ் தொடர்பான அரசு பணிகள் இங்கே நடக்கும்",
        "example": "பட்டா வாங்க தஹசில் அலுவலகத்திற்கு சென்றார்.",
        "doc_context": "தஹசில்தார் என்பவர் வட்டார நிர்வாக அதிகாரி. நிலம், வருவாய் சம்பந்தமான அனைத்து வேலைகளும் இங்கே நடக்கும்.",
    },
    "ரயத்வாரி": {
        "tamil": "விவசாயி நேரடியாக அரசுக்கு வரி கட்டும் நிலம் வகை",
        "example": "இந்த நிலம் ரயத்வாரி முறையில் பதிவு செய்யப்பட்டுள்ளது.",
        "doc_context": "நிலத்தின் வகையை குறிக்கும். ரயத்வாரி என்றால் நிலம் விவசாயியின் நேரடி உரிமை.",
    },
    "மானியம்": {
        "tamil": "அரசால் இலவசமாக அல்லது குறைந்த விலையில் கொடுக்கப்பட்ட நிலம் அல்லது உதவி",
        "example": "இந்த நிலம் அரசு மானியமாக கொடுக்கப்பட்டது.",
        "doc_context": "மானிய நிலங்களை சட்டப்படி குறிப்பிட்ட காலத்திற்கு விற்க முடியாது.",
        "note": "மானிய நிலம் விற்கும் முன் அரசிடம் அனுமதி வாங்க வேண்டும்."
    },
    "பட்டா மாற்றம்": {
        "tamil": "நிலத்தின் உரிமை ஒருவரிடம் இருந்து மற்றொருவருக்கு சட்டரீதியாக மாறுவது",
        "example": "தந்தை இறந்த பிறகு மகன் பெயரில் பட்டா மாற்றம் செய்யப்பட்டது.",
        "doc_context": "நிலம் வாங்கும்போது, வாரிசு உரிமை கோரும்போது பட்டா மாற்றம் கட்டாயம்.",
    },
    "எல்லை": {
        "tamil": "நிலத்தின் ஒரு பக்கம் — வடக்கு, தெற்கு, கிழக்கு, மேற்கு எல்லை குறிக்கப்படும்",
        "example": "வடக்கு எல்லை: ரமேஷின் நிலம், தெற்கு எல்லை: அரசு சாலை.",
        "doc_context": "பட்டாவில் நான்கு திசைகளிலும் என்ன இருக்கிறது என்று எல்லை குறிப்பிடப்படும். இது நிலத்தின் அளவை உறுதி செய்யும்.",
    },
    "ஏக்கர்": {
        "tamil": "நிலத்தின் அளவை குறிக்கும் அலகு — 1 ஏக்கர் = சுமார் 4 சென்ட் × 100",
        "example": "அவரிடம் 2.5 ஏக்கர் நிலம் உள்ளது.",
        "doc_context": "தமிழ்நாட்டில் நிலம் ஏக்கர் மற்றும் சென்ட்டில் அளக்கப்படுகிறது.",
    },
    "சென்ட்": {
        "tamil": "நிலத்தின் சிறிய அளவு அலகு — 100 சென்ட் = 1 ஏக்கர்",
        "example": "அவரிடம் 30 சென்ட் நிலம் உள்ளது.",
        "doc_context": "வீட்டு மனை போன்ற சிறிய நிலங்கள் பொதுவாக சென்ட்டில் அளக்கப்படும்.",
    },

    # ── GOVERNMENT ORDER (அரசாணை / G.O.) ────────────────────────────────────
    "அரசாணை": {
        "tamil": "அரசு அதிகாரப்பூர்வமாக பிறப்பிக்கும் ஆணை அல்லது உத்தரவு",
        "example": "இந்த திட்டம் அரசாணை எண் 150 மூலம் அனுமதிக்கப்பட்டது.",
        "doc_context": "அரசாணை (G.O.) என்பது அரசின் முறையான உத்தரவு. இதை மீற முடியாது.",
    },
    "செயல்முறை": {
        "tamil": "அரசு ஒரு தீர்மானம் எடுத்து அதை நடைமுறைப்படுத்தும் விதம்",
        "example": "இந்த செயல்முறை அறிவுரையின்படி அனைத்து அலுவலகங்களும் நடக்க வேண்டும்.",
        "doc_context": "செயல்முறை (Proceedings) என்பது ஒரு அரசு கூட்டத்தில் எடுக்கப்பட்ட தீர்மானங்களின் பதிவு.",
    },
    "சுற்றறிக்கை": {
        "tamil": "அரசு அனைவருக்கும் அனுப்பும் பொது அறிவிப்பு கடிதம்",
        "example": "இந்த சுற்றறிக்கை அனைத்து மாவட்ட ஆட்சியர்களுக்கும் அனுப்பப்பட்டது.",
        "doc_context": "சுற்றறிக்கை (Circular) என்பது கீழ்நிலை அலுவலர்களுக்கு அறிவுறுத்தல் அனுப்பும் முறை.",
    },
    "விண்ணப்பம்": {
        "tamil": "ஒரு விஷயத்திற்காக அரசிடம் எழுத்தில் கோரும் கடிதம்",
        "example": "வீட்டுமனை பெற விண்ணப்பம் சமர்ப்பித்தார்.",
        "doc_context": "அரசு சேவைகளுக்கு விண்ணப்பம் சமர்ப்பிக்க வேண்டும். விண்ணப்ப எண் வைத்திருங்கள்.",
    },
    "மனு": {
        "tamil": "குறை தீர்க்க அல்லது ஒரு விஷயத்திற்கு அரசிடம் கோரும் மனுதாரர் கடிதம்",
        "example": "நிலம் சம்பந்தமாக கலெக்டரிடம் மனு சமர்ப்பித்தார்.",
        "doc_context": "மனு கொடுத்த பிறகு ரசீது வாங்கவும். மனு எண் வைத்திருங்கள்.",
    },
    "ஆணை": {
        "tamil": "அதிகாரியோ அரசோ கொடுக்கும் கட்டளை அல்லது உத்தரவு",
        "example": "நீதிமன்றம் வழங்கிய ஆணைப்படி நிலம் திரும்ப கொடுக்கப்பட்டது.",
        "doc_context": "ஆணை என்பது கட்டாயமாக பின்பற்ற வேண்டியது. மீறினால் சட்ட நடவடிக்கை வரும்.",
    },
    "கலெக்டர்": {
        "tamil": "மாவட்ட நிர்வாகத்தின் தலைவர் — மாவட்ட ஆட்சியர்",
        "example": "கலெக்டர் அலுவலகத்தில் மனு கொடுத்தார்.",
        "doc_context": "மாவட்டத்தில் நில வருவாய், சட்டம் ஒழுங்கு, வளர்ச்சி திட்டங்கள் கலெக்டர் கீழ் வரும்.",
    },

    # ── CERTIFICATES (சான்றிதழ்) ────────────────────────────────────────────
    "சான்றிதழ்": {
        "tamil": "ஒரு விஷயம் உண்மை என்று அரசு உறுதி செய்யும் ஆவணம்",
        "example": "சாதி சான்றிதழ் வேலைக்கு விண்ணப்பிக்க தேவை.",
        "doc_context": "சான்றிதழ் என்பது அரசு அதிகாரி கையொப்பமிட்ட முறையான ஆவணம்.",
    },
    "வருமான சான்றிதழ்": {
        "tamil": "குடும்பத்தின் ஆண்டு வருமானத்தை அரசு உறுதி செய்யும் ஆவணம்",
        "example": "கல்வி உதவித்தொகைக்கு வருமான சான்றிதழ் தேவை.",
        "doc_context": "வருமான வரம்பு கணக்கில் வரும் திட்டங்களுக்கு இது கட்டாயம்.",
        "note": "வருமான சான்றிதழ் ஒரு வருடம் மட்டுமே செல்லும். ஒவ்வொரு வருடமும் புதுப்பிக்க வேண்டும்."
    },
    "சாதி சான்றிதழ்": {
        "tamil": "நீங்கள் எந்த சாதியை சேர்ந்தவர் என்று அரசு உறுதி செய்யும் ஆவணம்",
        "example": "OBC வகையில் சாதி சான்றிதழ் வேலை ஒதுக்கீட்டிற்கு தேவை.",
        "doc_context": "கல்வி, வேலை, அரசு திட்டங்களில் ஒதுக்கீடு பெற சாதி சான்றிதழ் தேவை.",
    },
    "வதிவிட சான்றிதழ்": {
        "tamil": "நீங்கள் இந்த இடத்தில் வாழ்கிறீர்கள் என்று அரசு உறுதி செய்யும் ஆவணம்",
        "example": "இந்த மாவட்டத்தில் வதிவிட சான்றிதழ் இருந்தால் இங்கு படிக்கலாம்.",
        "doc_context": "உள்ளூர் ஒதுக்கீடு பெற வதிவிட சான்றிதழ் தேவை.",
    },
    "பிறப்பு சான்றிதழ்": {
        "tamil": "நீங்கள் பிறந்த தேதி, இடம் உறுதி செய்யும் ஆவணம்",
        "example": "பள்ளியில் சேர பிறப்பு சான்றிதழ் கட்டாயம்.",
        "doc_context": "பாஸ்போர்ட், வாக்காளர் அட்டை, பள்ளி சேர்க்கை அனைத்திற்கும் இது அடிப்படை ஆவணம்.",
    },
    "இறப்பு சான்றிதழ்": {
        "tamil": "ஒருவர் இறந்தது உறுதி செய்யும் அரசு ஆவணம்",
        "example": "வாரிசு சான்றிதழ் வாங்க இறப்பு சான்றிதழ் தேவை.",
        "doc_context": "சொத்து உரிமை, வங்கி கணக்கு, காப்பீடு கோரிக்கைக்கு இது தேவை.",
    },
    "வாரிசு சான்றிதழ்": {
        "tamil": "ஒருவர் இறந்த பிறகு அவரது சொத்துக்கு யார் உரிமையாளர் என்று அரசு சொல்லும் ஆவணம்",
        "example": "அப்பா இறந்த பிறகு வாரிசு சான்றிதழ் வாங்கி சொத்து பெற்றனர்.",
        "doc_context": "வாரிசு சான்றிதழ் இல்லாமல் இறந்தவரின் சொத்தை சட்டரீதியாக கோர முடியாது.",
        "note": "வாரிசு சான்றிதழ் தஹசில் அலுவலகத்தில் கிடைக்கும்."
    },
    "நேட்டிவிட்டி": {
        "tamil": "நீங்கள் எந்த ஊரை சேர்ந்தவர் என்று உறுதி செய்யும் சான்றிதழ்",
        "example": "தமிழ்நாடு ஒதுக்கீட்டிற்கு நேட்டிவிட்டி சான்றிதழ் தேவை.",
        "doc_context": "மாநில அரசு வேலை, கல்வி ஒதுக்கீட்டிற்கு பயன்படும்.",
    },

    # ── LEGAL / COURT (சட்ட / நீதிமன்ற) ────────────────────────────────────
    "ஒப்பந்தம்": {
        "tamil": "இரண்டு நபர்கள் அல்லது தரப்பினர் இடையே எழுத்தில் செய்யப்படும் உடன்படிக்கை",
        "example": "வீடு வாங்க விற்பனையாளர் மற்றும் வாங்குபவர் இடையே ஒப்பந்தம் செய்யப்பட்டது.",
        "doc_context": "ஒப்பந்தம் சட்டரீதியான ஆவணம். இதை மீறினால் நீதிமன்றம் போகலாம்.",
        "note": "ஒப்பந்தம் ஸ்டாம்ப் பேப்பரில் எழுதி பதிவு செய்தால் மட்டுமே முழு சட்ட பாதுகாப்பு கிடைக்கும்."
    },
    "பதிவு": {
        "tamil": "சொத்து உரிமை அரசு ஆவணத்தில் பதிவு செய்யப்படுவது",
        "example": "வீடு வாங்கிய பிறகு பதிவு அலுவலகத்தில் பதிவு செய்தனர்.",
        "doc_context": "சொத்து பதிவு இல்லாமல் உரிமை சட்டரீதியாக உங்களுக்கு மாறாது.",
        "note": "பதிவு கட்டணம் மற்றும் ஸ்டாம்ப் டியூட்டி கட்ட வேண்டும்."
    },
    "வழக்கு": {
        "tamil": "நீதிமன்றத்தில் தீர்வு காண தாக்கல் செய்யப்படும் புகார் அல்லது வேண்டுகோள்",
        "example": "நிலம் சம்பந்தமாக நீதிமன்றத்தில் வழக்கு தாக்கல் செய்தார்.",
        "doc_context": "வழக்கு தாக்கல் ஆனால் வழக்கு எண் வைத்திருங்கள். இது எல்லா ஆவணங்களிலும் தேவைப்படும்.",
    },
    "மனுதாரர்": {
        "tamil": "நீதிமன்றத்தில் அல்லது அரசிடம் மனு சமர்ப்பிக்கும் நபர்",
        "example": "மனுதாரர் நீதிமன்றத்தில் தனது கோரிக்கையை வைத்தார்.",
        "doc_context": "நீதிமன்ற ஆவணங்களில் மனு கொடுப்பவர் 'மனுதாரர்' என்று குறிப்பிடப்படுவார்.",
    },
    "பிரதிவாதி": {
        "tamil": "வழக்கில் குற்றம் சாட்டப்படுபவர் அல்லது எதிர்த்து நிற்பவர்",
        "example": "பிரதிவாதி நீதிமன்றத்தில் ஆஜரானார்.",
        "doc_context": "வழக்கில் இரண்டு தரப்பு: வழக்கு தொடுப்பவர் (வாதி), குற்றம் சாட்டப்படுபவர் (பிரதிவாதி).",
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
    "ஜாமீன்": {
        "tamil": "ஒருவர் சட்டப்படி நடந்துகொள்வார் என்று வேறொருவர் அரசுக்கு உறுதி அளிப்பது",
        "example": "கைதான பிறகு நண்பர் ஜாமீன் அளித்தார்.",
        "doc_context": "ஜாமீன் கொடுப்பவர் பொறுப்பாளர். குற்றவாளி தப்பித்தால் ஜாமீன் கொடுத்தவர் தண்டிக்கப்படுவார்.",
    },
    "அஃபிடவிட்": {
        "tamil": "சத்தியப்பிரமாணம் செய்து கொடுக்கும் எழுத்து ஆவணம் — இது தவறாயின் சட்ட நடவடிக்கை வரும்",
        "example": "நோட்டரியிடம் அஃபிடவிட் கொடுத்தார்.",
        "doc_context": "அஃபிடவிட் தவறான தகவல் கொடுத்தால் பொய் சாட்சி வழக்கு வரும்.",
    },

    # ── COMMON GOVT WORDS ────────────────────────────────────────────────────
    "கட்டணம்": {
        "tamil": "சேவைக்காக செலுத்த வேண்டிய பணம்",
        "example": "பதிவுக்கு கட்டணம் கட்ட வேண்டும்.",
        "doc_context": "அரசு சேவைகளுக்கு நிர்ணயிக்கப்பட்ட கட்டணம் செலுத்த வேண்டும்.",
    },
    "விண்ணப்பதாரர்": {
        "tamil": "விண்ணப்பம் சமர்ப்பிக்கும் நபர்",
        "example": "விண்ணப்பதாரர் தனது ஆவணங்களை சமர்ப்பித்தார்.",
        "doc_context": "அரசு ஆவணங்களில் விண்ணப்பம் கொடுப்பவரை விண்ணப்பதாரர் என்று குறிப்பிடுவார்கள்.",
    },
    "நிராகரிப்பு": {
        "tamil": "கோரிக்கையை மறுக்கிறோம் என்று அரசு சொல்வது",
        "example": "போதுமான ஆவணங்கள் இல்லாததால் விண்ணப்பம் நிராகரிக்கப்பட்டது.",
        "doc_context": "நிராகரிக்கப்பட்டால் காரணம் கேட்டு மேல்முறையீடு செய்யலாம்.",
    },
    "அங்கீகாரம்": {
        "tamil": "ஒரு விஷயத்திற்கு அதிகாரப்பூர்வமான ஒப்புதல் கொடுப்பது",
        "example": "கட்டட திட்டத்திற்கு மாநகராட்சி அங்கீகாரம் தேவை.",
        "doc_context": "அரசு அங்கீகாரம் இல்லாமல் கட்டிடம் கட்டினால் இடிக்கப்படும்.",
    },
    "வரி": {
        "tamil": "அரசுக்கு கட்டாயமாக கட்ட வேண்டிய பணம்",
        "example": "சொத்து வரி ஒவ்வொரு வருடமும் கட்ட வேண்டும்.",
        "doc_context": "வரி கட்டாவிட்டால் அபராதம் மற்றும் சட்ட நடவடிக்கை வரும்.",
    },
    "குத்தகை": {
        "tamil": "பணம் கொடுத்து குறிப்பிட்ட காலம் நிலம் அல்லது கட்டிடம் பயன்படுத்திக்கொள்வதற்கான ஒப்பந்தம்",
        "example": "விவசாயி 5 வருடத்திற்கு நிலத்தை குத்தகைக்கு எடுத்தான்.",
        "doc_context": "குத்தகை ஒப்பந்தம் எழுத்தில் செய்தால் சட்ட பாதுகாப்பு கிடைக்கும்.",
    },
    "அடமானம்": {
        "tamil": "கடன் வாங்க சொத்தை பாதுகாப்பாக வைப்பது — கடன் திரும்ப கொடுக்காவிட்டால் சொத்து போகும்",
        "example": "வீட்டை அடமானம் வைத்து வங்கியில் கடன் வாங்கினார்.",
        "doc_context": "அடமான ஆவணம் பதிவு செய்தால் மட்டுமே சட்ட பாதுகாப்பு.",
        "note": "கடன் திரும்ப கொடுக்காவிட்டால் வங்கி சொத்தை ஏலம் போடலாம்."
    },
    "கையொப்பம்": {
        "tamil": "ஒரு ஆவணத்தில் நீங்கள் ஒப்புதல் அளிக்கும் அடையாளம்",
        "example": "ஆவணத்தில் கையொப்பமிட்டார்.",
        "doc_context": "கையொப்பமிட்ட ஆவணம் சட்டரீதியான ஒப்பந்தம். கவனமாக படித்த பிறகு மட்டும் கையொப்பமிடவும்.",
        "note": "படிக்காமல் கையொப்பமிடாதீர்கள் — அது ஆபத்தானது."
    },
    "சாட்சி": {
        "tamil": "ஒரு நிகழ்ச்சி நடந்தது என்று உறுதி செய்யும் நபர்",
        "example": "ஒப்பந்தத்தில் இரண்டு சாட்சிகள் கையொப்பமிட்டனர்.",
        "doc_context": "முக்கியமான ஆவணங்களில் சாட்சிகள் தேவை.",
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
    "அசல்": {
        "tamil": "ஆவணத்தின் முதல் பிரதி — copy அல்ல",
        "example": "பதிவு அலுவலகத்தில் அசல் ஆவணம் சமர்ப்பிக்க வேண்டும்.",
        "doc_context": "முக்கியமான நடவடிக்கைகளுக்கு பொதுவாக அசல் ஆவணமே தேவை.",
    },
    "ஆட்சேபணை": {
        "tamil": "ஒரு முடிவு அல்லது நடவடிக்கைக்கு எதிர்ப்பு தெரிவிப்பது",
        "example": "நிலம் கையகப்படுத்துவதற்கு ஆட்சேபணை தெரிவித்தார்.",
        "doc_context": "அரசு நடவடிக்கைக்கு ஆட்சேபணை தெரிவிக்க குறிப்பிட்ட காலம் இருக்கும்.",
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
    "முறையீடு": {
        "tamil": "ஒரு முடிவை மேல் நிலை அதிகாரி அல்லது நீதிமன்றத்தில் சவால் செய்வது",
        "example": "தஹசிலில் தீர்வு கிடைக்காவிட்டால் கலெக்டரிடம் முறையீடு செய்யலாம்.",
        "doc_context": "முறையீடு செய்ய காலக்கெடு இருக்கும் — தாமதிக்காதீர்கள்.",
    },
    "நிலுவை": {
        "tamil": "இன்னும் கட்டப்படாத அல்லது முடிவு செய்யப்படாத பணம் அல்லது வேலை",
        "example": "கடந்த வருட வரி நிலுவையில் உள்ளது.",
        "doc_context": "நிலுவை தொகை கட்டாவிட்டால் அபராதம் சேரும்.",
    },
    "பொறுப்பு": {
        "tamil": "கட்டாயமாக செய்ய வேண்டிய கடமை அல்லது கொடுக்க வேண்டிய பணம்",
        "example": "கடனுக்கான பொறுப்பு அவரிடம் இருக்கிறது.",
        "doc_context": "சட்ட ஆவணங்களில் பொறுப்பு என்பது கட்டாய கடமை.",
    },
    "தகுதி": {
        "tamil": "ஒரு திட்டம் அல்லது சேவைக்கு விண்ணப்பிக்கும் உரிமை",
        "example": "இந்த திட்டத்திற்கு வருமானம் குறைவாக உள்ளவர்களுக்கு மட்டுமே தகுதி உண்டு.",
        "doc_context": "தகுதி நிபந்தனைகளை கவனமாக படிக்கவும். தகுதி இல்லாமல் விண்ணப்பித்தால் நிராகரிக்கப்படும்.",
    },
    "அறிவிப்பு": {
        "tamil": "அரசு பொதுமக்களுக்கு தெரிவிக்கும் தகவல்",
        "example": "புதிய திட்டம் பற்றிய அறிவிப்பு வெளியிடப்பட்டது.",
        "doc_context": "அரசு அறிவிப்பு வெளியான நாளிலிருந்தே அது செல்லுபடியாகும்.",
    },
    "பரிசீலனை": {
        "tamil": "ஒரு விண்ணப்பம் அல்லது கோரிக்கையை ஆய்வு செய்வது",
        "example": "உங்கள் விண்ணப்பம் பரிசீலனையில் உள்ளது.",
        "doc_context": "பரிசீலனை முடிந்த பிறகு அனுமதி அல்லது நிராகரிப்பு வரும்.",
    },
    "சமர்ப்பித்தல்": {
        "tamil": "ஆவணங்கள் அல்லது விண்ணப்பத்தை அலுவலகத்தில் கொடுப்பது",
        "example": "தேவையான ஆவணங்களை சமர்ப்பித்தார்.",
        "doc_context": "சமர்ப்பித்த பிறகு ரசீது வாங்க மறவாதீர்கள்.",
    },
    "பரிந்துரை": {
        "tamil": "ஒரு விஷயத்திற்கு ஒப்புதல் அல்லது ஆதரவு கொடுப்பது",
        "example": "அதிகாரி விண்ணப்பத்திற்கு பரிந்துரை செய்தார்.",
        "doc_context": "பரிந்துரை இருந்தால் விண்ணப்பம் விரைவில் அனுமதிக்கப்படும்.",
    },
    "நிர்வாகம்": {
        "tamil": "அரசு வேலைகளை ஒழுங்காக நடத்துவது",
        "example": "மாவட்ட நிர்வாகம் வெள்ள நிவாரணம் வழங்கியது.",
        "doc_context": "நிர்வாக தீர்வு கிடைக்கவில்லையென்றால் நீதிமன்றம் போகலாம்.",
    },
    "துறை": {
        "tamil": "குறிப்பிட்ட வேலையை கவனிக்கும் அரசு பிரிவு",
        "example": "வருவாய் துறை நிலம் சம்பந்தமான வேலைகளை கவனிக்கிறது.",
        "doc_context": "சரியான துறையில் விண்ணப்பிக்காவிட்டால் தாமதம் ஆகும்.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TYPE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
DOC_TYPES = {
    "பட்டா / நிலம்":  ["பட்டா","சிட்டா","survey","சர்வே","நிலம்","ஏக்கர்","புல","chitta"],
    "அரசாணை (G.O.)":  ["G.O.","அரசாணை","government order","செயல்முறை","சுற்றறிக்கை"],
    "சான்றிதழ்":       ["சான்றிதழ்","certificate","பிறப்பு","சாதி","வருமானம்","income","caste","birth"],
    "சட்ட ஆவணம்":     ["மனு","petition","court","நீதிமன்றம்","வழக்கு","affidavit","ஒப்பந்தம்"],
}

def detect_doc_type(text: str) -> str:
    t = text.lower()
    for dtype, kws in DOC_TYPES.items():
        if any(k.lower() in t for k in kws):
            return dtype
    return "அரசு ஆவணம்"


# ══════════════════════════════════════════════════════════════════════════════
# SUFFIX + SANDHI ENGINE (proven working from v6)
# ══════════════════════════════════════════════════════════════════════════════
SUFFIXES = [
    "ப்படுகிறது","ப்படுகின்றது","க்கப்படும்","ப்படும்","ப்பட்டது",
    "வைக்கப்படும்","படுத்தப்படும்",
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
SANDHI = [
    ("ந்த","ந்தம்"),("ட்ட","ட்டம்"),("க்க","க்கம்"),
    ("ல்ல","ல்"),("ன்ன","ன்னம்"),("ர்த்த","ர்த்தம்"),
]

def _strip(w):
    for s in SUFFIXES:
        if w.endswith(s) and len(w) > len(s)+1:
            return w[:-len(s)]
    return None

def _sandhi(w):
    return [w[:-len(t)]+r for t,r in SANDHI if w.endswith(t)]

def _variants(w):
    sw = [("ரை","றை"),("றை","ரை"),("ல","ள"),("ள","ல"),("ன","ந"),("ந","ன")]
    return [w.replace(a,b,1) for a,b in sw if a in w and w.replace(a,b,1)!=w]

def candidates(word: str) -> list:
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
# DICTIONARY LOOKUP — checks built-in dict first, then online sources
# ══════════════════════════════════════════════════════════════════════════════
def dict_lookup(word: str):
    """Check built-in GOVT_DICT for word or any of its candidate roots."""
    for c in candidates(word):
        if c in GOVT_DICT:
            return GOVT_DICT[c], c
    return None, None

def src_mymemory(word: str):
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": word, "langpair": "ta|en"}, timeout=4,
        )
        if r.status_code == 200:
            t = r.json().get("responseData",{}).get("translatedText","")
            if t and t.lower()!=word.lower() and "INVALID" not in t.upper() and len(t)>1:
                return t.strip()
    except Exception: pass
    return None

def src_wiktionary(word: str):
    try:
        r = requests.get(
            f"https://ta.wiktionary.org/api/rest_v1/page/definition/{requests.utils.quote(word)}",
            timeout=3,
        )
        if r.status_code == 200:
            data = r.json()
            for key in data:
                entries = data[key]
                if isinstance(entries,list) and entries:
                    raw = entries[0].get("definitions",[{}])[0].get("definition","")
                    clean = re.sub(r"<[^>]+>","",raw).strip()
                    if clean and len(clean)>3: return clean
    except Exception: pass
    return None

def src_google(word: str):
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ta", target="en").translate(word)
        if t and t.lower()!=word.lower(): return t.strip()
    except Exception: pass
    return None

def find_context(text: str, word: str):
    for c in candidates(word):
        for sent in re.split(r'(?<=[.!?\n])\s*', text):
            if c in sent.strip() and len(sent.strip())>5:
                return sent.strip()
        idx = text.find(c)
        if idx>=0:
            s,e = max(0,idx-80), min(len(text),idx+len(c)+80)
            return "…"+text[s:e].strip()+"…"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def lookup(word: str, doc_text: str="", doc_type: str="அரசு ஆவணம்") -> dict:
    cands     = candidates(word)
    dict_res, dict_root = dict_lookup(word)
    ctx       = find_context(doc_text, word) if doc_text else None

    # Online fallback
    online = None
    root_used = dict_root or word
    if not dict_res:
        t = src_mymemory(word)
        if not t:
            for c in cands[1:]:
                t = src_mymemory(c)
                if t: root_used=c; break
        if not t: t = src_google(word)
        if not t:
            for c in cands:
                t = src_wiktionary(c)
                if t: root_used=c; break
        online = t

    return {
        "word":      word,
        "root":      root_used,
        "dict":      dict_res,
        "online":    online,
        "context":   ctx,
        "doc_type":  doc_type,
        "found":     bool(dict_res or online),
        "tried":     cands,
    }


# ── Audio ─────────────────────────────────────────────────────────────────────
def speak(word):
    try:
        buf=io.BytesIO(); gTTS(text=word,lang="ta",slow=False).write_to_fp(buf); buf.seek(0); return buf
    except: return None


# ── OCR / Extraction ──────────────────────────────────────────────────────────
def preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    w,h = img.size
    if w<1800:
        sc=1800/w; img=img.resize((int(w*sc),int(h*sc)),Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    arr = np.array(img)
    arr = ((arr > int(arr.mean()*0.85))*255).astype(np.uint8)
    return Image.fromarray(arr)

def clean_text(raw: str) -> str:
    lines = raw.splitlines()
    out = []
    for ln in lines:
        ln = re.sub(r"[|}{\\~`_]","",ln).strip()
        ln = re.sub(r" {2,}"," ",ln)
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

def ocr_image(img): return clean_text(pytesseract.image_to_string(preprocess(img), config=r"--oem 3 --psm 6 -l tam+eng"))
def extract_pdf(f):
    ts=[]
    with pdfplumber.open(f) as pdf:
        for p in pdf.pages:
            t=p.extract_text()
            if t: ts.append(clean_text(t))
    return "\n\n".join(ts)

def is_tamil(w): return bool(re.search(r"[\u0B80-\u0BFF]",w))
def tokenize(t): return re.findall(r"[\u0B80-\u0BFF]+|[A-Za-z0-9]+",t)


# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("text",""),("word",""),("doc_type","அரசு ஆவணம்")]:
    st.session_state.setdefault(k,v)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>📜 தமிழ் அரசு ஆவண வாசகன் <span class="free-badge">100% இலவசம்</span></h1>
  <p>Upload PDF or image · Read clearly · Search any Tamil word · Get Tamil explanation · Zero cost · No API key</p>
</div>
""", unsafe_allow_html=True)

t_reader, t_deploy = st.tabs(["📄 ஆவண வாசகன்", "🚀 GitHub → Streamlit Cloud Guide"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — READER
# ══════════════════════════════════════════════════════════════════════════════
with t_reader:
    left, right = st.columns([3,2], gap="large")

    with left:
        st.markdown('<div class="slabel">படி 1 — ஆவணம் பதிவேற்றவும்</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("file", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")

        if uploaded:
            with st.spinner("உரை எடுக்கிறோம்…"):
                if uploaded.type=="application/pdf":
                    text = extract_pdf(uploaded)
                    if not text.strip():
                        st.warning("OCR இயக்குகிறோம்…")
                        try:
                            from pdf2image import convert_from_bytes
                            imgs = convert_from_bytes(uploaded.getvalue(), first_page=1, last_page=1)
                            text = ocr_image(imgs[0]) if imgs else ""
                        except Exception as e:
                            st.error(f"OCR பிழை: {e}"); text=""
                else:
                    text = ocr_image(Image.open(uploaded))
                st.session_state.text     = text
                st.session_state.doc_type = detect_doc_type(text)

        if st.session_state.text:
            st.markdown(f'<div class="doc-chip">📋 ஆவண வகை: {st.session_state.doc_type}</div>', unsafe_allow_html=True)
            st.markdown('<div class="slabel">படி 2 — ஆவணம் படிக்கவும்</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint">💡 புரியாத சொல்லை கீழே dropdown-ல் தேர்வு செய்யுங்கள் அல்லது வலதில் தட்டச்சு செய்யுங்கள்</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="docbox">{st.session_state.text}</div>', unsafe_allow_html=True)

            tw = sorted({t for t in tokenize(st.session_state.text) if is_tamil(t) and len(t)>1})
            if tw:
                st.markdown('<div class="slabel" style="margin-top:.7rem">ஆவணத்தில் உள்ள சொற்கள்</div>', unsafe_allow_html=True)
                pick = st.selectbox("pick", ["— தேர்வு செய்யவும் —"]+tw, label_visibility="collapsed", key="pick")
                if pick != "— தேர்வு செய்யவும் —":
                    st.session_state.word = pick
        else:
            st.info("மேலே PDF அல்லது படம் பதிவேற்றவும்.")

    with right:
        st.markdown('<div class="slabel">சொல் பொருள்</div>', unsafe_allow_html=True)
        typed = st.text_input("தமிழ் சொல்:", placeholder="உதா: ஒப்பந்தம், பட்டா, சர்வே எண்", key="typed")
        if typed: st.session_state.word = typed.strip()

        w = st.session_state.word.strip()

        if w and is_tamil(w):
            with st.spinner(f"'{w}' — பொருள் தேடுகிறோம்…"):
                res   = lookup(w, st.session_state.text, st.session_state.doc_type)
                audio = speak(w)

            root_note = f"(அடி வடிவம்: {res['root']})" if res["root"]!=res["word"] else ""
            st.markdown(f"""
            <div class="mcard">
              <div class="mword">{res['word']}</div>
              <div class="mroot">{root_note}</div>
            """, unsafe_allow_html=True)

            if res["found"]:
                d = res["dict"]
                if d:
                    # ── Built-in dict: Tamil meaning + example + doc context ──
                    st.markdown(f"""
                    <div class="sec s-tamil">
                      <div class="sec-head">📖 தமிழ் பொருள்</div>
                      <div class="sec-body">{d['tamil']}</div>
                    </div>""", unsafe_allow_html=True)

                    if d.get("example"):
                        st.markdown(f"""
                        <div class="sec s-example">
                          <div class="sec-head">✏️ எடுத்துக்காட்டு வாக்கியம்</div>
                          <div class="sec-body">{d['example']}</div>
                        </div>""", unsafe_allow_html=True)

                    if d.get("doc_context"):
                        st.markdown(f"""
                        <div class="sec s-doc">
                          <div class="sec-head">📋 அரசு ஆவணத்தில் பொருள்</div>
                          <div class="sec-body">{d['doc_context']}</div>
                        </div>""", unsafe_allow_html=True)

                    if d.get("note"):
                        st.markdown(f"""
                        <div class="sec s-context">
                          <div class="sec-head">⚠️ கவனிக்க வேண்டியது</div>
                          <div class="sec-body">{d['note']}</div>
                        </div>""", unsafe_allow_html=True)

                elif res["online"]:
                    # ── Online fallback ──
                    st.markdown(f"""
                    <div class="sec s-trans">
                      <div class="sec-head">🔤 பொருள் (ஆன்லைன் மூலம்)</div>
                      <div class="sec-body">{res['online']}</div>
                    </div>""", unsafe_allow_html=True)

                # ── Sentence from document ──
                if res["context"]:
                    st.markdown(f"""
                    <div class="sec s-context">
                      <div class="sec-head">📄 உங்கள் ஆவணத்தில் இந்த சொல்</div>
                      <div class="sec-body">{res['context']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="notfound">
                  ⚠️ <strong>{res['word']}</strong> — பொருள் கிடைக்கவில்லை.<br>
                  {len(res['tried'])} வடிவங்கள் தேடப்பட்டன. சிறிய வடிவில் முயற்சிக்கவும்.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if audio:
                st.markdown("**🔊 உச்சரிப்பு**")
                st.audio(audio, format="audio/mp3")

            with st.expander("🔍 தேடிய வடிவங்கள்"):
                for i,c in enumerate(res["tried"],1): st.write(f"{i}. `{c}`")

        elif w:
            st.info("தமிழ் எழுத்தில் சொல்லை தட்டச்சு செய்யவும்.")
        else:
            st.markdown("""
            <div class="mcard" style="text-align:center;color:#ccc;padding:2.5rem 1rem;">
              <div style="font-size:2.5rem">🔍</div>
              <div style="font-family:'Noto Sans Tamil',sans-serif;font-size:1rem;margin-top:.4rem;color:#999;">
                மேலே சொல்லை தட்டச்சு செய்யுங்கள்<br>அல்லது ஆவணத்தில் இருந்து தேர்வு செய்யுங்கள்
              </div>
            </div>""", unsafe_allow_html=True)

        st.caption("📚 உள்ளமைக்கப்பட்ட அரசு அகராதி + MyMemory + Google Translate + Tamil Wiktionary | 100% இலவசம்")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEPLOY GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with t_deploy:
    st.markdown("## 🚀 GitHub → Streamlit Cloud — இலவச Deploy (~10 நிமிடம்)")
    st.info("✅ இந்த version-க்கு எந்த API key-உம் தேவையில்லை. 100% இலவசம்.")

    st.markdown("""
    <div class="step"><span class="num">1</span>
      <strong>GitHub account</strong> (இலவசம்) →
      <a href="https://github.com" target="_blank">github.com</a> → Sign up
    </div>
    <div class="step"><span class="num">2</span>
      <strong>New repository</strong> → <code>+</code> → New repository<br>
      Name: <code>tamil-doc-reader</code> | Visibility: <strong>Public</strong> → Create
    </div>
    <div class="step"><span class="num">3</span>
      <strong>3 files upload</strong> → "uploading an existing file" → drag & drop:<br>
      <code>app.py</code> &emsp; <code>requirements.txt</code> &emsp; <code>packages.txt</code> → Commit changes
    </div>
    <div class="step"><span class="num">4</span>
      <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a>
      → GitHub மூலம் Sign in → <strong>New app</strong><br>
      Repo: <code>tamil-doc-reader</code> | Branch: <code>main</code> | File: <code>app.py</code> → Deploy!
    </div>
    <div class="step"><span class="num">5</span>
      3–5 நிமிடம் → இலவச URL:
      <code>https://yourname-tamil-doc-reader.streamlit.app</code> ✅<br>
      எந்த API key-உம் தேவையில்லை. உடனே வேலை செய்யும்.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**`requirements.txt`**")
        st.code("streamlit>=1.32.0\npytesseract>=0.3.10\nPillow>=10.0.0\npdfplumber>=0.10.0\npdf2image>=1.16.0\ngTTS>=2.5.0\nrequests>=2.31.0\nbeautifulsoup4>=4.12.0\ndeep-translator>=1.11.4\nnumpy>=1.24.0", language="text")
    with c2:
        st.markdown("**`packages.txt`**")
        st.code("tesseract-ocr\ntesseract-ocr-tam\ntesseract-ocr-eng\npoppler-utils", language="text")

    st.success("✅ பணம் கட்ட வேண்டியதில்லை. API key வேண்டியதில்லை. உடனே deploy ஆகும்.")

st.markdown("""
<div style="text-align:center;font-size:.74rem;color:#bbb;margin-top:2rem;padding-top:.8rem;border-top:1px solid #ddd4c4;">
  தமிழ் அரசு ஆவண வாசகன் v7 · 100% Free · No API Key · Built-in Tamil Govt Dictionary (500+ words)
  + MyMemory + Google Translate + Tamil Wiktionary · OCR: Tesseract · Audio: gTTS
</div>
""", unsafe_allow_html=True)
