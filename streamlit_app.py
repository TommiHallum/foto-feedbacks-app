import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io
import os

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# CSS: Tvinger designet på plads og retter 200MB -> 20MB visuelt
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3, h4, p, span { color: #ffffff !important; }
    
    /* Upload felt styling */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6;
        padding: 5px;
        border-radius: 10px;
    }
    [data-testid="stFileUploader"] section { color: #0e1117 !important; padding: 0px; }
    [data-testid="stFileUploader"] label { color: #0e1117 !important; }
    
    /* Tvinger 20MB tekst frem */
    [data-testid="stFileUploader"] small { visibility: hidden; }
    [data-testid="stFileUploader"] small::before {
        content: "Max 20MB per fil • JPG, PNG";
        visibility: visible;
        display: block;
        color: #0e1117 !important;
    }

    /* Knap styling */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        height: 3em;
        margin-top: 28px;
    }
    
    /* Sidebar og Footer */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stSidebar a { color: #4daafc !important; text-decoration: underline !important; }
    
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #8b949e !important;
        text-align: center; padding: 15px; font-size: 12px;
        border-top: 1px solid #30363d; z-index: 999;
    }
    .main .block-container { padding-bottom: 100px; }
    .stTable td, .stTable th { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def get_exif_data(image):
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                    exif_data[decoded] = str(value)
    except: pass
    return exif_data

def create_pdf(image, exif_dict, s1, s2, s3, s4):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Foto Feedback Rapport", ln=True, align='C')
    
    temp_path = "temp_pdf_img.jpg"
    image.convert("RGB").save(temp_path, "JPEG")
    pdf.image(temp_path, x=10, y=30, w=80)
    pdf.ln(90)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", size=10)
    if exif_dict:
        for k, v in exif_dict.items():
            pdf.cell(200, 7, f"{k}: {v}", ln=True)
    
    pdf.ln(5)
    sections = [("Komposition", s1), ("Lys", s2), ("Historie", s3), ("Tips", s4)]
    for title, text in sections:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 8, title + ":", ln=True)
        pdf.set_font("Arial", size=10)
        clean = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean)
        pdf.ln(2)

    os.remove(temp_path)
    return pdf.output(dest='S').encode('latin-1')

# 2. SIDEBAR
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)
    st.divider()
    st.write("Om appen: Professionel fotoanalyse drevet af AI.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")

# Knapperække
btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

with btn_col1:
    uploaded_file = st.file_uploader("Upload billede", type=["jpg", "jpeg", "png"])

with btn_col2:
    analyze_clicked = st.button("🚀 Start AI Analyse", use_container_width=True)

with btn_col3:
    if 's1' in st.session_state:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], 
                              st.session_state['s1'], st.session_state['s2'], 
                              st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Download PDF", data=pdf_data, file_name="foto_feedback.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("📥 Download PDF", disabled=True)

if uploaded_file:
    image = Image.open(uploaded_file)
    exif = get_exif_data(image)
    
    # Vis billede og EXIF side om side
    top1, top2 = st.columns([2, 1])
    with top1: st.image(image, use_container_width=True)
    with top2: 
        st.markdown("#### Tekniske EXIF-data")
        if exif:
            st.table(exif)
        else:
            st.info("Ingen EXIF fundet.")

    if analyze_clicked:
        if not api_key:
            st.error("Indsæt venligst API-nøgle i sidemenuen.")
        else:
            with st.spinner("AI'en analyserer dit billede..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest')
                # Vi beder AI svare helt uden markdown-tabel format
                prompt = "Analyser billedet. Svar på dansk i 4 sektioner: [S1] Komposition, [S2] Lys, [S3] Historie, [S4] Tips. Undgå at bruge tabeller i dit svar."
                response = model.generate_content([prompt, image])
                txt = response.text
                
                # Split-logik der er mere robust overfor formatering
                try:
                    st.session_state['s1'] = txt.split("[S2]")[0].replace("[S1]", "").strip()
                    st.session_state['s2'] = txt.split("[S2]")[1].split("[S3]")[0].strip()
                    st.session_state['s3'] = txt.split("[S3]")[1].split("[S4]")[0].strip()
                    st.session_state['s4'] = txt.split("[S4]")[1].strip()
                    st.session_state['img'] = image
                    st.session_state['exif'] = exif
                    st.rerun()
                except:
                    st.error("AI'en gav et svar der ikke kunne deles op. Prøv igen.")

    # Visning af analysen
    if 's1' in st.session_state:
        st.divider()
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1: 
            st.markdown("### 1. Komposition og beskæring")
            st.write(st.session_state['s1'])
        with r1_c2: 
            st.markdown("### 2. Lys og eksponering")
            st.write(st.session_state['s2'])
        
        st.divider()
        r2_c1, r2_c2 = st.columns(2)
        with r2_c1: 
            st.markdown("### 3. Historie og stemning")
            st.write(st.session_state['s3'])
        with r2_c2: 
            st.markdown("### Professionelle tips til forbedring")
            st.success(st.session_state['s4'])

# 4. FOOTER
st.markdown('<div class="custom-footer">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
