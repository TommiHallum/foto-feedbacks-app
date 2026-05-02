import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import os

# 1. SIDE KONFIGURATION
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - TOTAL RENSNING OG PDF KNAP STYLING
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Upload felt: Lys boks, mørk tekst */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6 !important;
        border: 2px dashed #4F46E5 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    /* Skjul Streamlits hvide labels og standard 200MB tekst */
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        display: none !important;
    }

    /* Indsæt vores egen tekst i sort */
    [data-testid="stFileUploader"] section::before {
        content: "UPLOAD BILLEDE HER";
        display: block;
        color: #000000 !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    [data-testid="stFileUploader"] section::after {
        content: "Max 20MB per fil • JPG, PNG";
        display: block;
        color: #333333 !important;
        font-size: 13px;
    }

    /* Store lilla knapper (Analyse & Download) */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
    }
    
    /* Gør deaktiveret knap tydelig */
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
    
    # Billede (venstre) og EXIF (højre) i PDF
    img.convert("RGB").save("temp_p.jpg", "JPEG")
    pdf.image("temp_p.jpg", x=10, y=30, w=90)
    
    pdf.set_xy(110, 30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 8, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", '', 10)
    for k, v in exif.items():
        pdf.set_x(110)
        pdf.cell(90, 6, f"{k}: {v}", ln=True)
    
    # Feedback sektioner
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

# 4. HOVEDLAYOUT
st.title("FOTO FEEDBACK")
api_key = st.sidebar.text_input("Gemini API Nøgle:", type="password")

# De tre knapper på stribe
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
        st.download_button("📥 Hent PDF", data=pdf_file, file_name="feedback.pdf", mime="application/pdf")
    else:
        st.button("📥 Hent PDF", disabled=True, help="Kør analysen først")

# 5. LOGIK NÅR BILLEDE ER UPLOADET
if uploaded:
    img = Image.open(uploaded)
    exif_data = get_exif(img)
    
    # Vis billede og data side om side
    c1, c2 = st.columns([2, 1])
    with c1: st.image(img, use_container_width=True)
    with c2: 
        st.write("### EXIF Data")
        if exif_data: st.table(exif_data)
        else: st.info("Ingen EXIF data fundet")

    if analyze_btn and api_key:
        with st.spinner("AI analyserer..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            res = model.generate_content(["Analyser billede i 4 sektioner: [S1] Komp, [S2] Lys, [S3] Hist, [S4] Tips", img])
            txt = res.text
            try:
                st.session_state['s1'] = txt.split("[S2]")[0].replace("[S1]", "").strip()
                st.session_state['s2'] = txt.split("[S2]")[1].split("[S3]")[0].strip()
                st.session_state['s3'] = txt.split("[S3]")[1].split("[S4]")[0].strip()
                st.session_state['s4'] = txt.split("[S4]")[1].strip()
                st.session_state['img'], st.session_state['exif'] = img, exif_data
                st.rerun()
            except: st.error("Fejl i AI-formatet. Prøv igen.")

    # Vis resultaterne
    if 's1' in st.session_state:
        st.divider()
        r1, r2 = st.columns(2)
        with r1: st.subheader("1. Komposition"); st.write(st.session_state['s1'])
        with r2: st.subheader("2. Lys"); st.write(st.session_state['s2'])
        r3, r4 = st.columns(2)
        with r3: st.subheader("3. Historie"); st.write(st.session_state['s3'])
        with r4: st.subheader("Professionelle Tips"); st.success(st.session_state['s4'])

st.markdown('<div style="text-align:center; padding:20px; color:#888;">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
