import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fpdf import FPDF
import os
import re

# 1. SIDE KONFIGURATION
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - SIDEBAR, FLUGTNING OG KOMPAKTHED
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* SIDEBAR: Maksimalt komprimeret */
    [data-testid="stSidebar"] { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] h1 { font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }
    [data-testid="stSidebar"] h4 { margin: 0.2rem 0 0.1rem 0 !important; padding: 0 !important; }
    [data-testid="stSidebar"] .stInfo { padding: 0.5rem !important; margin: 0.2rem 0 !important; }
    [data-testid="stSidebar"] .stMarkdown p { margin-bottom: 0.1rem !important; line-height: 1.2 !important; }
    [data-testid="stSidebar"] hr { margin: 5px 0 !important; }

    /* HOVEDLAYOUT: Flugtning i bunden */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }

    /* Upload-felt styling */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px solid #4F46E5 !important;
        border-radius: 8px !important;
        padding: 5px !important;
        margin-bottom: 0px !important;
    }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p { display: none !important; }
    [data-testid="stFileUploader"] section::before { content: "UPLOAD BILLEDE"; display: block; color: #4F46E5 !important; font-weight: bold; text-align: center; padding-top: 5px; }
    [data-testid="stFileUploader"] section::after { content: "JPG, PNG (Max 20MB)"; display: block; color: #666666 !important; font-size: 10px; text-align: center; padding-bottom: 5px; }

    /* Knap styling */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3.85em !important;
        width: 100% !important;
        border: none !important;
        text-transform: uppercase;
        margin-bottom: 0px !important;
    }
    
    .stElementContainer { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# 3. HJÆLPEFUNKTIONER
class PDF(FPDF):
    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", '', 8); self.set_text_color(150, 150, 150)
        self.cell(0, 5, "AI DREVET FOTO ANALYSE © 2026", ln=True, align='C')
        self.set_font("Arial", 'B', 10); self.set_text_color(79, 70, 229)
        self.cell(0, 5, "✨ ✨ ✨", ln=True, align='C')
        self.set_font("Arial", '', 8); self.set_text_color(100, 100, 100)
        self.cell(0, 5, "hallum.dk - dinfotomand.dk - fotoliv.dk", ln=True, align='C')

def clean_text(text):
    """Sikrer at tekst kan kodes i latin-1 til PDF"""
    if not text: return ""
    text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u201d', '"').replace('\u201c', '"')
    return text.encode('latin-1', 'ignore').decode('latin-1')

def get_exif(image):
    exif = {}
    try:
        info = image._getexif()
        if info:
            for tag, val in info.items():
                name = TAGS.get(tag, tag)
                if name in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength', 'DateTimeOriginal', 'LensModel', 'Software']:
                    if name == 'ExposureTime': exif['Lukketid'] = f"{val} sek"
                    elif name == 'FNumber': exif['Blænde'] = f"f/{val}"
                    elif name == 'FocalLength': exif['Brændvidde'] = f"{val}mm"
                    elif name == 'ISOSpeedRatings': exif['ISO'] = val
                    elif name == 'LensModel': exif['Objektiv'] = val
                    else: exif[name] = str(val)
                if name == "GPSInfo":
                    gps = {}
                    for t in val: gps[GPSTAGS.get(t, t)] = val[t]
                    if 'GPSLatitude' in gps and 'GPSLongitude' in gps:
                        exif['GPS'] = f"{float(gps['GPSLatitude'][0])}°N, {float(gps['GPSLongitude'][0])}°E"
    except: pass
    return exif

def create_pdf(img, exif, intro, s1, s2, s3, s4):
    pdf = PDF()
    pdf.add_page()
    blue_info_bg, gray_section_bg, brand_blue = (231, 243, 255), (240, 242, 246), (79, 70, 229)
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*brand_blue); pdf.cell(190, 15, "FOTO FEEDBACK RAPPORT", ln=True, align='C')
    img.convert("RGB").save("temp_report_img.jpg", "JPEG")
    pdf.image("temp_report_img.jpg", x=10, y=35, w=70)
    pdf.set_xy(90, 35); pdf.set_font("Arial", 'B', 11); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(249, 250, 251)
    pdf.cell(110, 8, " Tekniske Data (EXIF):", ln=True, fill=True, border=1)
    pdf.set_font("Arial", '', 9)
    if exif:
        for k, v in exif.items(): 
            pdf.set_x(90); pdf.cell(110, 6, clean_text(f" {k}: {v}"), ln=True, border='LR')
    else: 
        pdf.set_x(90); pdf.cell(110, 6, " Ingen EXIF data fundet", ln=True, border='LR')
    pdf.set_x(90); pdf.cell(110, 1, "", ln=True, border='B')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(*blue_info_bg); pdf.cell(190, 8, " Samlet Vurdering", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, clean_text(intro), border=1)
    for title, content in [("1. Komposition", s1), ("2. Lys & Teknik", s2), ("3. Historie & Stemning", s3), ("Professionelle Tips", s4)]:
        if pdf.get_y() > 220: pdf.add_page()
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(*gray_section_bg); pdf.cell(190, 8, clean_text(f" {title}"), ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(190, 5, clean_text(content), border=1)
    if os.path.exists("temp_report_img.jpg"): os.remove("temp_report_img.jpg")
    return pdf.output(dest='S')

# 4. SIDEBAR
st.title("FOTO FEEDBACK")
with st.sidebar:
    st.markdown("#### Indstillinger")
    api_key = st.text_input("Gemini API Nøgle:", type="password")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**Mangler du en nøgle?**")
    st.markdown("[Få din Gemini API-nøgle her](https://aistudio.google.com/app/apikey)")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### Om appen")
    st.info("Professionel fotoanalyse drevet af AI. Upload et billede og få feedback på teknik.\n\nUdarbejdet af Tommi Hallum © 2026")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**Gemini er AI og kan begå fejl**")
    st.markdown("[Dit privatliv og Gemini](https://support.google.com/gemini/answer/13594961)")

# 5. HOVEDLAYOUT
col_u, col_a, col_p = st.columns([1.5, 1, 1])
with col_u: uploaded = st.file_uploader("", type=["jpg", "png"])
with col_a: analyze_btn = st.button("🚀 Analyser", use_container_width=True)
with col_p:
    if 'intro' in st.session_state:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], st.session_state['intro'], st.session_state['s1'], st.session_state['s2'], st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf_data, file_name="foto-feedback.pdf", mime="application/pdf", use_container_width=True)
    else: st.button("📥 Hent PDF", disabled=True, use_container_width=True)

status_placeholder = st.container()

# 6. LOGIK
if uploaded:
    img = Image.open(uploaded)
    exif_data = get_exif(img)
    c1, c2 = st.columns([1.5, 1])
    with c1: st.image(img, use_container_width
