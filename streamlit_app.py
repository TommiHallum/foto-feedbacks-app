import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fpdf import FPDF
import os
import re

# 1. SIDE KONFIGURATION - Skal altid ligge øverst
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - Optimeret og samlet
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] h1 { font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }
    [data-testid="stSidebar"] h4 { margin: 0.2rem 0 !important; }
    [data-testid="stFileUploader"] { background-color: #ffffff !important; border: 2px solid #4F46E5 !important; border-radius: 8px !important; padding: 5px !important; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small { display: none !important; }
    [data-testid="stFileUploader"] section::before { content: "UPLOAD BILLEDE"; display: block; color: #4F46E5 !important; font-weight: bold; text-align: center; }
    div.stButton > button, div.stDownloadButton > button { background-color: #4F46E5 !important; color: white !important; border-radius: 8px !important; font-weight: bold !important; height: 3.85em !important; width: 100% !important; border: none !important; text-transform: uppercase; }
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
    if not text: return ""
    # Fjerner tegn der ikke understøttes i latin-1 (PDF standard)
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
    except: pass
    return exif

def create_pdf(img, exif, intro, s1, s2, s3, s4):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(79, 70, 229)
    pdf.cell(190, 15, "FOTO FEEDBACK RAPPORT", ln=True, align='C')
    img.convert("RGB").save("temp_rep.jpg", "JPEG")
    pdf.image("temp_rep.jpg", x=10, y=35, w=70)
    pdf.set_xy(90, 35); pdf.set_font("Arial", 'B', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(110, 8, " Tekniske Data (EXIF):", ln=True, fill=True, border=1)
    pdf.set_font("Arial", '', 9)
    for k, v in exif.items(): pdf.set_x(90); pdf.cell(110, 6, clean_text(f" {k}: {v}"), ln=True, border='LR')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12); pdf.cell(190, 8, " Samlet Vurdering", ln=True, border=1)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, clean_text(intro), border=1)
    for title, content in [("1. Komposition", s1), ("2. Lys & Teknik", s2), ("3. Historie & Stemning", s3), ("Professionelle Tips", s4)]:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, clean_text(f" {title}"), ln=True, border=1)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(190, 5, clean_text(content), border=1)
    if os.path.exists("temp_rep.jpg"): os.remove("temp_rep.jpg")
    return pdf.output(dest='S')

# 4. SIDEBAR
st.title("FOTO FEEDBACK")
with st.sidebar:
    st.markdown("#### Indstillinger")
    api_key = st.text_input("Gemini API Nøgle:", type="password")
    st.markdown("[Få din nøgle her](https://aistudio.google.com/app/apikey)")
    st.info("AI-drevet fotoanalyse. © 2026 Tommi Hallum")

# 5. HOVEDLOGIK
col_u, col_a, col_p = st.columns([1.5, 1, 1])
uploaded = col_u.file_uploader("", type=["jpg", "png"])
analyze_btn = col_a.button("🚀 Analyser", use_container_width=True)

status_placeholder = st.container()

if uploaded:
    img = Image.open(uploaded)
    exif_data = get_exif(img)
    col_img, col_data = st.columns([1.5, 1])
    col_img.image(img, use_container_width=True)
    col_data.write("### Tekniske Data")
    if exif_data: col_data.table(list(exif_data.items()))
    else: col_data.info("Ingen EXIF data fundet")

    if analyze_btn:
        if not api_key:
            status_placeholder.warning("⚠️ Indtast venligst din API-nøgle.")
        else:
            with status_placeholder:
                with st.status("AI analyserer billedet...", expanded=True) as status:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        res = model.generate_content(["Analyser dette billede som en professionel fotograf. Brug overskrifter: INDLEDNING:, SEKTION1:, SEKTION2:, SEKTION3:, SEKTION4:.", img])
                        parts = re.split(r'(INDLEDNING:|SEKTION1:|SEKTION2:|SEKTION3:|SEKTION4:)', res.text)
                        # Gem i session state
                        st.session_state.update({
                            'intro': parts[parts.index('INDLEDNING:')+1] if 'INDLEDNING:' in parts else "",
                            's1': parts[parts.index('SEKTION1:')+1] if 'SEKTION1:' in parts else "",
                            's2': parts[parts.index('SEKTION2:')+1] if 'SEKTION2:' in parts else "",
                            's3': parts[parts.index('SEKTION3:')+1] if 'SEKTION3:' in parts else "",
                            's4': parts[parts.index('SEKTION4:')+1] if 'SEKTION4:' in parts else "",
                            'img': img, 'exif': exif_data
                        })
                        status.update(label="Analyse færdig!", state="complete", expanded=False)
                        st.rerun()
                    except Exception as e:
                        status.update(label="Fejl", state="error")
                        st.error(f"Teknisk fejl: {e}")

# Vis resultater og PDF knap
if 'intro' in st.session_state:
    with col_p:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], st.session_state['intro'], st.session_state['s1'], st.session_state['s2'], st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf_data, file_name="foto-feedback.pdf", mime="application/pdf", use_container_width=True)
    
    st.divider()
    st.info(st.session_state['intro'])
    r1, r2 = st.columns(2)
    r1.subheader("✨ 1. Komposition"); r1.write(st.session_state['s1'])
    r2.subheader("✨ 2. Lys & Teknik"); r2.write(st.session_state['s2'])
    r3, r4 = st.columns(2)
    r3.subheader("✨ 3. Historie & Stemning"); r3.write(st.session_state['s3'])
    r4.subheader("✨ Professionelle Tips"); r4.success(st.session_state['s4'])
