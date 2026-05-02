import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io
import os

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Forenklet og fejlsikret CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Upload felt: Lys baggrund med mørk tekst for læsbarhed */
    [data-testid="stFileUploader"] {
        background-color: #e0e4e9 !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] section, 
    [data-testid="stFileUploader"] p, 
    [data-testid="stFileUploader"] span {
        color: #161b22 !important;
    }

    /* Visuel rettelse af 200MB -> 20MB */
    [data-testid="stFileUploader"] small { display: none !important; }
    [data-testid="stFileUploader"] section::after {
        content: "Max 20MB per fil • JPG, PNG";
        display: block;
        color: #161b22 !important;
        font-size: 12px;
        margin-top: 5px;
    }

    /* Knapper */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3.5em !important;
        margin-top: 28px !important;
    }
    
    /* Footer */
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #8b949e !important;
        text-align: center; padding: 15px; border-top: 1px solid #30363d;
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
    
    temp_path = "temp_print.jpg"
    image.convert("RGB").save(temp_path, "JPEG")
    
    # Layout: Billede og EXIF
    pdf.image(temp_path, x=10, y=25, w=110)
    pdf.set_xy(125, 25)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(65, 8, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", '', 10)
    if exif_dict:
        for k, v in exif_dict.items():
            pdf.set_x(125)
            pdf.cell(65, 6, f"{k}: {v}", ln=True)
    
    # Feedback
    pdf.set_y(120)
    sections = [("1. Komposition", s1), ("2. Lys", s2), ("3. Historie", s3), ("Tips", s4)]
    for i in range(0, len(sections), 2):
        y = pdf.get_y()
        pdf.set_font("Arial", 'B', 11)
        pdf.set_xy(10, y); pdf.cell(90, 8, sections[i][0])
        pdf.set_xy(110, y); pdf.cell(90, 8, sections[i+1][0])
        
        pdf.set_font("Arial", '', 9)
        pdf.set_xy(10, y+8)
        pdf.multi_cell(90, 5, sections[i][1].encode('latin-1', 'replace').decode('latin-1'))
        y1 = pdf.get_y()
        
        pdf.set_xy(110, y+8)
        pdf.multi_cell(90, 5, sections[i+1][1].encode('latin-1', 'replace').decode('latin-1'))
        y2 = pdf.get_y()
        pdf.set_y(max(y1, y2) + 5)

    if os.path.exists(temp_path): os.remove(temp_path)
    return pdf.output(dest='S').encode('latin-1')

# --- HOVEDSIDE ---
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Gemini API-nøgle:", type="password")

st.title("FOTO FEEDBACK")

# Knapperække
col_up, col_an, col_pdf = st.columns([2, 1, 1])
with col_up:
    uploaded_file = st.file_uploader("Vælg billede", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
with col_an:
    analyze_clicked = st.button("🚀 Start AI Analyse")
with col_pdf:
    if 's1' in st.session_state:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], 
                              st.session_state['s1'], st.session_state['s2'], 
                              st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Download PDF", data=pdf_data, file_name="feedback.pdf", mime="application/pdf")
    else:
        st.button("📥 Download PDF", disabled=True)

if uploaded_file:
    img = Image.open(uploaded_file)
    exif = get_exif_data(img)
    
    t1, t2 = st.columns([2, 1])
    with t1: st.image(img, use_container_width=True)
    with t2: 
        st.markdown("### Tekniske Data")
        if exif: st.table(exif)
        else: st.info("Ingen EXIF fundet")

    if analyze_clicked and api_key:
        with st.spinner("Analyserer..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            prompt = "Analyser billedet. Svar på dansk i 4 korte sektioner: [S1] Komposition, [S2] Lys, [S3] Historie, [S4] Tips."
            res = model.generate_content([prompt, img])
            txt = res.text
            try:
                st.session_state['s1'] = txt.split("[S2]")[0].replace("[S1]", "").strip()
                st.session_state['s2'] = txt.split("[S2]")[1].split("[S3]")[0].strip()
                st.session_state['s3'] = txt.split("[S3]")[1].split("[S4]")[0].strip()
                st.session_state['s4'] = txt.split("[S4]")[1].strip()
                st.session_state['img'], st.session_state['exif'] = img, exif
                st.rerun()
            except: st.error("AI svaret kunne ikke behandles. Prøv igen.")

    if 's1' in st.session_state:
        st.divider()
        r1_1, r1_2 = st.columns(2)
        with r1_1:
            st.subheader("1. Komposition og beskæring")
            st.write(st.session_state['s1'])
        with r1_2:
            st.subheader("2. Lys og eksponering")
            st.write(st.session_state['s2'])
        st.divider()
        r2_1, r2_2 = st.columns(2)
        with r2_1:
            st.subheader("3. Historie og stemning")
            st.write(st.session_state['s3'])
        with r2_2:
            st.subheader("Professionelle tips")
            st.success(st.session_state['s4'])

st.markdown('<div class="custom-footer">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
