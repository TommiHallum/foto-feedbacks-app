import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import os
import re

# 1. SIDE KONFIGURATION
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - DESIGN OG LÆSBARHED
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Upload felt: Lys boks, mørk tekst */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6 !important;
        border: 2px dashed #4F46E5 !important;
        border-radius: 10px !important;
        padding: 20px !important;
    }

    /* Skjul Streamlits standard labels for at undgå overlap */
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        display: none !important;
    }

    /* Indsæt egen tekst i sort */
    [data-testid="stFileUploader"] section::before {
        content: "UPLOAD BILLEDE HER";
        display: block;
        color: #000000 !important;
        font-weight: bold;
        margin-bottom: 5px;
        text-align: center;
    }
    [data-testid="stFileUploader"] section::after {
        content: "Max 20MB per fil • JPG, PNG";
        display: block;
        color: #333333 !important;
        font-size: 13px;
        text-align: center;
    }

    /* Store lilla knapper */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
        border: none !important;
    }
    
    div.stButton > button:disabled {
        background-color: #262730 !important;
        color: #555555 !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. FUNKTIONER
def get_exif(image):
    exif = {}
    try:
        info = image._getexif()
        if info:
            for tag, val in info.items():
                name = TAGS.get(tag, tag)
                if name in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings']:
                    exif[name] = str(val)
    except: pass
    return exif

def create_pdf(img, exif, s1, s2, s3, s4):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "FOTO FEEDBACK RAPPORT", ln=True, align='C')
    
    img.convert("RGB").save("temp_p.jpg", "JPEG")
    pdf.image("temp_p.jpg", x=10, y=30, w=90)
    
    pdf.set_xy(110, 30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 8, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", '', 10)
    for k, v in exif.items():
        pdf.set_x(110)
        pdf.cell(90, 6, f"{k}: {v}", ln=True)
    
    pdf.set_y(120)
    sections = [("1. Komposition", s1), ("2. Lys", s2), ("3. Historie", s3), ("Tips", s4)]
    for title, content in sections:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, title, ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(190, 5, content.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2)
        
    os.remove("temp_p.jpg")
    return pdf.output(dest='S').encode('latin-1')

# 4. SIDEBAR & HOVEDLAYOUT
st.title("FOTO FEEDBACK")

with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Gemini API Nøgle:", type="password")
    st.divider()
    st.write("### Om appen")
    st.info("Professionel fotoanalyse drevet af AI. Upload et billede og få feedback på teknik og æstetik.")
    st.markdown('**Mangler du en nøgle?**')
    st.markdown('[Få din Gemini API-nøgle her](https://aistudio.google.com/app/apikey)', unsafe_allow_html=True)

# Knapperække
col_u, col_a, col_p = st.columns([2, 1, 1])

with col_u:
    uploaded = st.file_uploader("", type=["jpg", "png"])
with col_a:
    analyze_btn = st.button("🚀 Analyser", use_container_width=True)
with col_p:
    if 's1' in st.session_state:
        pdf_file = create_pdf(st.session_state['img'], st.session_state['exif'], 
                              st.session_state['s1'], st.session_state['s2'], 
                              st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf_file, file_name="feedback.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("📥 Hent PDF", disabled=True, use_container_width=True)

# Container til status/fejlbeskeder placeret under knapperne
status_placeholder = st.container()

# 5. LOGIK
if uploaded:
    img = Image.open(uploaded)
    exif_data = get_exif(img)
    
    c1, c2 = st.columns([2, 1])
    with c1: st.image(img, use_container_width=True)
    with c2: 
        st.write("### EXIF Data")
        if exif_data: st.table(exif_data)
        else: st.info("Ingen EXIF data fundet")

    if analyze_btn:
        if not api_key:
            with status_placeholder:
                st.warning("⚠️ Du skal indtaste en Gemini API-nøgle i menuen til venstre for at starte analysen.")
        else:
            with st.spinner("AI analyserer..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = """Analyser dette billede professionelt. 
                    Du SKAL starte hver sektion med præcis disse overskrifter:
                    SEKTION1:
                    SEKTION2:
                    SEKTION3:
                    SEKTION4:
                    Giv dybdegående feedback på dansk."""
                    
                    res = model.generate_content([prompt, img])
                    full_text = res.text
                    
                    parts = re.split(r'SEKTION\d:', full_text)
                    
                    if len(parts) >= 5:
                        st.session_state['s1'] = parts[1].strip()
                        st.session_state['s2'] = parts[2].strip()
                        st.session_state['s3'] = parts[3].strip()
                        st.session_state['s4'] =
