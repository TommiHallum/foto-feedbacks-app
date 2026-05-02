import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import os

# 1. SIDE CONFIG
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS (NU MED "NUCLEAR" SELECTOR DER TVINGER TEKST TIL AT VÆRE SORT)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Tvinger ALT indeni upload-feltet til at være sort tekst */
    [data-testid="stFileUploader"] * {
        color: #000000 !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6 !important;
        border: 2px dashed #4F46E5 !important;
        border-radius: 10px !important;
    }
    
    /* Skjul den standard-tekst der driller, og indsæt ny */
    [data-testid="stFileUploader"] small { display: none !important; }
    [data-testid="stFileUploader"] section::after {
        content: "Max 20MB per fil • JPG, PNG";
        display: block;
        color: #000000 !important;
        font-size: 14px;
        margin-top: 5px;
    }

    /* Knapper */
    div.stButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3em !important;
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
    
    # Gem billede
    img.convert("RGB").save("temp.jpg", "JPEG")
    pdf.image("temp.jpg", x=10, y=30, w=90)
    
    # EXIF
    pdf.set_xy(110, 30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 8, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", '', 10)
    for k, v in exif.items():
        pdf.set_x(110)
        pdf.cell(90, 6, f"{k}: {v}", ln=True)
    
    # Feedback
    pdf.set_y(120)
    txts = [("1. Komposition", s1), ("2. Lys", s2), ("3. Historie", s3), ("Tips", s4)]
    for title, content in txts:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, title, ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(190, 5, content.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2)
        
    os.remove("temp.jpg")
    return pdf.output(dest='S').encode('latin-1')

# 4. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
api_key = st.sidebar.text_input("Gemini API Nøgle:", type="password")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    uploaded = st.file_uploader("Upload", type=["jpg", "png"])
with col2:
    analyze = st.button("🚀 Analyser")
with col3:
    if 's1' in st.session_state:
        pdf = create_pdf(st.session_state['img'], st.session_state['exif'], st.session_state['s1'], st.session_state['s2'], st.session_state['s3'], st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf, file_name="feedback.pdf", mime="application/pdf")

if uploaded:
    img = Image.open(uploaded)
    exif = get_exif(img)
    
    # Layout
    c1, c2 = st.columns([2, 1])
    with c1: st.image(img, use_container_width=True)
    with c2: st.table(exif) if exif else st.write("Ingen data")

    if analyze and api_key:
        with st.spinner("Analyserer..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            res = model.generate_content(["Analyser billede i 4 sektioner: [S1] Komp, [S2] Lys, [S3] Hist, [S4] Tips", img])
            txt = res.text
            try:
                st.session_state['s1'] = txt.split("[S2]")[0].replace("[S1]", "").strip()
                st.session_state['s2'] = txt.split("[S2]")[1].split("[S3]")[0].strip()
                st.session_state['s3'] = txt.split("[S3]")[1].split("[S4]")[0].strip()
                st.session_state['s4'] = txt.split("[S4]")[1].strip()
                st.session_state['img'], st.session_state['exif'] = img, exif
                st.rerun()
            except: st.error("Fejl i format.")

    if 's1' in st.session_state:
        r1, r2 = st.columns(2)
        with r1: st.subheader("1. Komposition"); st.write(st.session_state['s1'])
        with r2: st.subheader("2. Lys"); st.write(st.session_state['s2'])
        r3, r4 = st.columns(2)
        with r3: st.subheader("3. Historie"); st.write(st.session_state['s3'])
        with r4: st.subheader("Tips"); st.success(st.session_state['s4'])
