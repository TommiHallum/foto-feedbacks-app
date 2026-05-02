import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io
import os

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# EKSTRA KRAFTIG CSS for at løse læsbarhedsproblemet
st.markdown("""
    <style>
    /* Grundlæggende mørkt tema */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* TVINGER tekst i upload-feltet til at være mørk, da boksen er lys */
    [data-testid="stFileUploader"] {
        background-color: #e0e4e9 !important;
        padding: 10px !important;
        border-radius: 10px !important;
        border: 2px dashed #4F46E5 !important;
    }
    
    /* Målretter specifikt teksten "Drag and drop file here", "Browse files" og filstørrelse */
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] section, 
    [data-testid="stFileUploader"] p, 
    [data-testid="stFileUploader"] span,
    [data-testid="stText"] {
        color: #161b22 !important;
    }

    /* Skjul standard 200MB og indsæt 20MB manuelt */
    [data-testid="stFileUploader"] small { visibility: hidden !important; height: 0px; }
    [data-testid="stFileUploader"] section::after {
        content: "Max 20MB per fil • JPG, PNG";
        visibility: visible;
        display: block;
        color: #161b22 !important;
        font-size: 12px;
        margin-top: 5px;
    }

    /* Knap styling */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3.5em !important;
        margin-top: 28px !important;
    }

    /* Sidebar og link */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stSidebar a { color: #4daafc !important; text-decoration: underline !important; font-weight: bold; }
    
    /* Tabel tekst */
    .stTable td, .stTable th { color: white !important; }
    
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #8b949e !important;
        text-align: center; padding: 15px; font-size: 12px;
        border-top: 1px solid #30363d; z-index: 999;
    }
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
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "FOTO FEEDBACK RAPPORT", ln=True, align='C')
    pdf.ln(5)
    
    temp_path = "temp_print.jpg"
    image.convert("RGB").save(temp_path, "JPEG")
    
    # Side-om-side layout i PDF (Billede venstre, EXIF højre)
    pdf.image(temp_path, x=10, y=25, w=110)
    pdf.set_xy(125, 25)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(65, 8, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", '', 10)
    if exif_dict:
        for k, v in exif_dict.items():
            pdf.set_x(125)
            pdf.cell(65, 6, f"{k}: {v}", ln=True)
    
    # Feedback sektioner
    pdf.set_y(120)
    sections = [("1. Komposition", s1), ("2. Lys", s2), ("3. Historie", s3), ("Professionelle tips", s4)]
    
    # Lav 2 kolonner til feedbacken
    col_width = 90
    for i in range(0, len(sections), 2):
        y_before = pdf.get_y()
        # Venstre kolonne
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width, 8, sections[i][0], ln=False)
        # Højre kolonne
        pdf.set_x(110)
        pdf.cell(col_width, 8, sections[i+1][0], ln=True)
        
        pdf.set_font("Arial", '', 9)
        y_text = pdf.get_y()
        
        # Venstre tekst
        pdf.set_xy(10, y_text)
        pdf.multi_cell(col_width, 5, sections[i][1].encode('latin-1', 'replace').decode('latin-1'))
        y_left = pdf.get_y()
        
        # Højre tekst
        pdf.set_xy(110, y_text)
        pdf.multi_cell(col_width, 5, sections[i+1][1].encode('latin-1', 'replace').decode('latin-1'))
        y_right = pdf.get_y()
        
        pdf.set_y(max(y_left, y_right) + 5)

    if os.path.exists(temp_path): os.remove(temp_path)
    return pdf.output(dest='S').encode('latin-1')

# SIDEBAR
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)

# HOVEDINDHOLD
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
        st.download_button("📥 Download A4 PDF", data=pdf_data, file_name="foto_feedback.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("📥 Download PDF", disabled=True)

if uploaded_file:
    image = Image.open(uploaded_file)
    exif = get_exif_data(image)
    
    t1, t2 = st.columns([2, 1])
    with t1: st.image(image, use_container_width=True)
    with t2: 
        st.markdown("#### Tekniske EXIF-data")
        st.table(exif) if exif else st.info("Ingen EXIF data")

    if analyze_clicked and api_key:
        with st.spinner("AI'en arbejder..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            prompt = "Analyser billedet. Svar i 4 sektioner: [S1] Komposition, [S2] Lys, [S3] Historie, [S4] Tips. Svar på dansk."
            res = model.generate_content([prompt, image])
            txt = res.text
            try:
                st.session_state['s1'] = txt.split("[S2]")[0].replace("[S1]", "").strip()
                st.session_state['s2'] = txt.split("[S2]")[1].split("[S3]")[0].strip()
                st.session_state['s3'] = txt.split("[S3]")[1].split("[S4]")[0].strip()
                st.session_state['s4'] = txt.split("[S4]")[1].strip()
                st.session_state['img'], st.session_state['exif'] = image, exif
                st.rerun()
            except: st.error("Kunne ikke opdele AI svaret. Prøv igen.")

    if 's1' in st.session_state:
        st.divider()
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("### 1. Komposition og beskæring")
            st.write(st.session_state['s1'])
        with c2: 
            st.markdown("### 2.
