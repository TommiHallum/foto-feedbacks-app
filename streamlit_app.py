import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fpdf import FPDF
import os
import re

# 1. SIDE KONFIGURATION
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - OPTIMERET TIL KOMPAKT LAYOUT OG FEEDBACK
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { padding-top: 0.5rem !important; }
    
    /* Upload og Knapper */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px solid #4F46E5 !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p { display: none !important; }
    [data-testid="stFileUploader"] section::before { content: "UPLOAD BILLEDE"; display: block; color: #4F46E5 !important; font-weight: bold; text-align: center; padding-top: 5px; }
    [data-testid="stFileUploader"] section::after { content: "JPG, PNG (Max 20MB)"; display: block; color: #666666 !important; font-size: 10px; text-align: center; padding-bottom: 5px; }

    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3.8em !important;
        width: 100% !important;
        border: none !important;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HJÆLPEFUNKTIONER (PDF CLASS MED FOOTER)
class PDF(FPDF):
    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", '', 8); self.set_text_color(150, 150, 150)
        self.cell(0, 5, "AI DREVET FOTO ANALYSE © 2026", ln=True, align='C')
        self.set_font("Arial", 'B', 10); self.set_text_color(79, 70, 229)
        self.cell(0, 5, "✨ ✨ ✨", ln=True, align='C')
        self.set_font("Arial", '', 8); self.set_text_color(100, 100, 100)
        self.cell(0, 5, "hallum.dk - dinfotomand.dk - fotoliv.dk", ln=True, align='C')

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
                    elif name == 'DateTimeOriginal': exif['Dato/Tid'] = val
                    elif name == 'Make': exif['Mærke'] = val
                    elif name == 'Model': exif['Kamera'] = val
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
        for k, v in exif.items(): pdf.set_x(90); pdf.cell(110, 6, f" {k}: {v}", ln=True, border='LR')
    else: pdf.set_x(90); pdf.cell(110, 6, " Ingen EXIF data fundet", ln=True, border='LR')
    pdf.set_x(90); pdf.cell(110, 1, "", ln=True, border='B')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(*blue_info_bg); pdf.cell(190, 8, " Samlet Vurdering", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, intro.encode('latin-1', 'replace').decode('latin-1'), border=1)
    for title, content in [("1. Komposition", s1), ("2. Lys & Teknik", s2), ("3. Historie & Stemning", s3), ("Professionelle Tips", s4)]:
        if pdf.get_y() > 220: pdf.add_page()
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(*gray_section_bg); pdf.cell(190, 8, f" {title}", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(190, 5, content.encode('latin-1', 'replace').decode('latin-1'), border=1)
    if os.path.exists("temp_report_img.jpg"): os.remove("temp_report_img.jpg")
    return pdf.output(dest='S').encode('latin-1')

# 4. SIDEBAR
st.title("FOTO FEEDBACK")
with st.sidebar:
    api_key = st.text_input("Gemini API Nøgle:", type="password")
    st.info("Professionel fotoanalyse drevet af AI. Udarbejdet af Tommi Hallum © 2026")

# 5. HOVEDLAYOUT
col_u, col_a, col_p = st.columns([1.5, 1, 1])
with col_u: uploaded = st.file_uploader("", type=["jpg", "png"])
with col_a: analyze_btn = st.button("🚀 Analyser", use_container_width=True)
with col_p:
    if 'intro' in st.session_state:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], st.session_state['intro'], st.session_state['s1'], st.session_state['s2'], st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf_data, file_name="foto-feedback.pdf", mime="application/pdf", use_container_width=True)
    else: st.button("📥 Hent PDF", disabled=True, use_container_width=True)

# 6. FEEDBACK CONTAINER (Flyttet ud, så den altid er synlig)
status_placeholder = st.container()

# 7. LOGIK
if uploaded:
    img = Image.open(uploaded)
    exif_data = get_exif(img)
    c1, c2 = st.columns([1.5, 1])
    with c1: st.image(img, use_container_width=True)
    with c2: 
        st.write("### Tekniske Data")
        if exif_data: st.table(list(exif_data.items()))
        else: st.info("Ingen EXIF data fundet")

    if analyze_btn:
        if not api_key:
            status_placeholder.warning("⚠️ Indtast venligst din API-nøgle.")
        else:
            with status_placeholder:
                with st.status("AI analyserer billedet...", expanded=True) as status:
                    try:
                        genai.configure(api_key=api_key)
                        res = genai.GenerativeModel('gemini-flash-latest').generate_content(["Analyser dette billede som en professionel fotograf. Brug overskrifter: INDLEDNING:, SEKTION1:, SEKTION2:, SEKTION3:, SEKTION4:. Giv dybdegående feedback på dansk.", img])
                        parts = re.split(r'(INDLEDNING:|SEKTION1:|SEKTION2:|SEKTION3:|SEKTION4:)', res.text)
                        st.session_state.update({
                            'intro': parts[parts.index('INDLEDNING:')+1].strip() if 'INDLEDNING:' in parts else "", 
                            's1': parts[parts.index('SEKTION1:')+1].strip() if 'SEKTION1:' in parts else "", 
                            's2': parts[parts.index('SEKTION2:')+1].strip() if 'SEKTION2:' in parts else "", 
                            's3': parts[parts.index('SEKTION3:')+1].strip() if 'SEKTION3:' in parts else "", 
                            's4': parts[parts.index('SEKTION4:')+1].strip() if 'SEKTION4:' in parts else "", 
                            'img': img, 'exif': exif_data
                        })
                        status.update(label="Analyse færdig!", state="complete", expanded=False)
                        st.rerun()
                    except Exception as e:
                        status.update(label="Fejl", state="error")
                        st.error(f"Fejl: {e}")

    if 'intro' in st.session_state:
        st.divider()
        st.write("### ✨ Samlet Vurdering")
        st.info(st.session_state['intro'])
        r1, r2 = st.columns(2)
        with r1: st.subheader("✨ 1. Komposition"); st.write(st.session_state['s1'])
        with r2: st.subheader("✨ 2. Lys & Teknik"); st.write(st.session_state['s2'])
        r3, r4 = st.columns(2)
        with r3: st.subheader("✨ 3. Historie & Stemning"); st.write(st.session_state['s3'])
        with r4: st.subheader("✨ Professionelle Tips"); st.success(st.session_state['s4'])
