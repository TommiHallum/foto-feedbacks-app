import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import os
import re

# 1. SIDE KONFIGURATION
st.set_page_config(page_title="Foto Feedback", layout="wide")

# 2. CSS - KONSISTENT DESIGN
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Upload-felt styling */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px solid #4F46E5 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] p {
        display: none !important;
    }
    
    [data-testid="stFileUploader"] section::before {
        content: "UPLOAD BILLEDE";
        display: block;
        color: #4F46E5 !important;
        font-weight: bold;
        text-align: center;
        padding-top: 10px;
    }
    [data-testid="stFileUploader"] section::after {
        content: "JPG, PNG (Max 20MB)";
        display: block;
        color: #666666 !important;
        font-size: 12px;
        text-align: center;
        padding-bottom: 10px;
    }

    /* Knap styling */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        width: 100% !important;
        border: none !important;
        text-transform: uppercase;
    }
    
    div.stButton > button:disabled {
        background-color: #262730 !important;
        color: #555555 !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HJÆLPEFUNKTIONER
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

def create_pdf(img, exif, intro, s1, s2, s3, s4):
    pdf = FPDF()
    pdf.add_page()
    
    blue_info_bg = (231, 243, 255)
    gray_section_bg = (240, 242, 246)
    brand_blue = (79, 70, 229)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*brand_blue)
    pdf.cell(190, 15, "FOTO FEEDBACK RAPPORT", ln=True, align='C')
    pdf.ln(5)
    
    img.convert("RGB").save("temp_report_img.jpg", "JPEG")
    w_px, h_px = img.size
    img_w_pdf = 85
    img_h_pdf = (h_px / w_px) * img_w_pdf
    pdf.image("temp_report_img.jpg", x=10, y=35, w=img_w_pdf)
    
    pdf.set_xy(105, 35)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(249, 250, 251)
    pdf.cell(90, 8, " Tekniske Data (EXIF):", ln=True, fill=True, border=1)
    pdf.set_font("Arial", '', 9)
    if exif:
        for k, v in exif.items():
            pdf.set_x(105)
            pdf.cell(90, 6, f" {k}: {v}", ln=True, border='LR')
    else:
        pdf.set_x(105)
        pdf.cell(90, 6, " Ingen EXIF data fundet", ln=True, border='LR')
    pdf.set_x(105)
    pdf.cell(90, 1, "", ln=True, border='B')

    current_y = max(35 + img_h_pdf, pdf.get_y()) + 10
    pdf.set_y(current_y)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(*blue_info_bg) 
    pdf.cell(190, 8, " Samlet Vurdering", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(190, 6, intro.encode('latin-1', 'replace').decode('latin-1'), border=1)
    pdf.ln(8)
    
    sections = [("1. Komposition", s1), ("2. Lys & Teknik", s2), ("3. Historie & Stemning", s3), ("Professionelle Tips", s4)]
    for title, content in sections:
        if pdf.get_y() > 240: pdf.add_page()
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(*gray_section_bg)
        pdf.cell(190, 8, f" {title}", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(190, 5, content.encode('latin-1', 'replace').decode('latin-1'), border=1)
        pdf.ln(5)
        
    # FOOTER I PDF
    pdf.set_y(-30)
    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(190, 5, "AI DREVET FOTO ANALYSE © 2026", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(*brand_blue)
    pdf.cell(190, 7, "  * * * ", ln=True, align='C')
    
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(190, 5, "hallum.dk - dinfotomand.dk - fotoliv.dk", ln=True, align='C')
        
    if os.path.exists("temp_report_img.jpg"): os.remove("temp_report_img.jpg")
    return pdf.output(dest='S').encode('latin-1')

# 4. SIDEBAR
st.title("FOTO FEEDBACK")

with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Gemini API Nøgle:", type="password")
    st.divider()
    st.markdown('**Mangler du en nøgle?**')
    st.markdown('[Få din Gemini API-nøgle her](https://aistudio.google.com/app/apikey)', unsafe_allow_html=True)
    st.divider()
    
    st.write("### Om appen")
    # Den blå boks med Om appen tekst og copyright
    st.info("""Professionel fotoanalyse drevet af AI. Upload et billede og få feedback på teknik.
    \n\nUdarbejdet og udviklet af Tommi Hallum © 2026""")
    
    st.divider()
    
    # Trin: Privatlivslink opdateret jf. ønske
    st.markdown('**Gemini er AI og kan begå fejl**')
    st.markdown('[Dit privatliv, data og Gemini](https://support.google.com/gemini/answer/13594961)', unsafe_allow_html=True)

# 5. HOVEDLAYOUT
col_u, col_a, col_p = st.columns([2, 1, 1])
with col_u:
    uploaded = st.file_uploader("", type=["jpg", "png"])
with col_a:
    analyze_btn = st.button("🚀 Analyser", use_container_width=True)
with col_p:
    if 'intro' in st.session_state:
        pdf_data = create_pdf(st.session_state['img'], st.session_state['exif'], 
                              st.session_state['intro'], st.session_state['s1'], 
                              st.session_state['s2'], st.session_state['s3'], 
                              st.session_state['s4'])
        st.download_button("📥 Hent PDF", data=pdf_data, file_name="foto-feedback.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("📥 Hent PDF", disabled=True, use_container_width=True)

status_placeholder = st.container()

# 6. LOGIK
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
            with status_placeholder: st.warning("⚠️ Indtast venligst din API-nøgle.")
        else:
            with status_placeholder:
                with st.status("AI analyserer billedet...", expanded=True) as status:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-flash-latest')
                        prompt = "Analyser dette billede som en professionel fotograf. Start med en generel indledning. Brug overskrifter: INDLEDNING:, SEKTION1:, SEKTION2:, SEKTION3:, SEKTION4:. Giv dybdegående feedback på dansk."
                        res = model.generate_content([prompt, img])
                        text = res.text
                        parts = re.split(r'(INDLEDNING:|SEKTION1:|SEKTION2:|SEKTION3:|SEKTION4:)', text)
                        def get_content(label):
                            try: return parts[parts.index(label)+1].strip()
                            except: return ""
                        st.session_state['intro'], st.session_state['s1'], st.session_state['s2'] = get_content('INDLEDNING:'), get_content('SEKTION1:'), get_content('SEKTION2:')
                        st.session_state['s3'], st.session_state['s4'] = get_content('SEKTION3:'), get_content('SEKTION4:')
                        st.session_state['img'], st.session_state['exif'] = img, exif_data
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

# 7. GRAFISK FOOTER
st.markdown("""
    <div style="text-align:center; padding:40px 20px; color:#888; font-size:13px; margin-top:50px; border-top:1px solid #333;">
        <div style="font-weight:bold; color:#555; margin-bottom:5px;">AI DREVET FOTO ANALYSE © 2026</div>
        <div style="font-size:22px; color:#4F46E5; margin-bottom:15px; display: flex; justify-content: center; gap: 40px;">
            <span>✨</span><span>✨</span><span>✨</span>
        </div>
        <div style="letter-spacing:1px; margin-top: 10px;">hallum.dk • dinfotomand.dk • fotoliv.dk</div>
    </div>
""", unsafe_allow_html=True)
