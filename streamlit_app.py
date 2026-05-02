import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff !important; }
    label, p, span, div, h1, h2, h3, .stMarkdown { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stSidebar a { color: #4daafc !important; text-decoration: underline; }
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #8b949e !important;
        text-align: center; padding: 15px; font-size: 12px;
        border-top: 1px solid #30363d; z-index: 999;
    }
    .main .block-container { padding-bottom: 80px; }
    </style>
    """, unsafe_allow_html=True)

# Funktion til EXIF
def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                exif_data[decoded] = str(value)
    return exif_data

# NY FUNKTION: Generer PDF
def create_pdf(image, exif_dict, feedback_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Foto Feedback Rapport", ln=True, align='C')
    pdf.ln(10)
    
    # Gem billede midlertidigt til PDF
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    pdf.image(img_byte_arr, x=10, y=30, w=100)
    pdf.ln(80) # Flyt ned under billedet
    
    # EXIF Data
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", size=10)
    for key, val in exif_dict.items():
        pdf.cell(200, 7, f"{key}: {val}", ln=True)
    
    pdf.ln(10)
    
    # Feedback (håndterer danske tegn ved at erstatte dem eller bruge standard font)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "AI Feedback:", ln=True)
    pdf.set_font("Arial", size=10)
    # Renser teksten for specialtegn som fpdf's standard font kan have svært ved
    clean_text = feedback_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, clean_text)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Genereret af Tommi Hallum Foto Feedback AI", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# 2. SIDEBAR
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)
    st.divider()
    st.subheader("Om appen")
    st.write("Analyse og PDF-eksport af dine fotos.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload & Tekniske Data")
    uploaded_file = st.file_uploader("Vælg et billede...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        exif = get_exif_data(image)
        if exif:
            st.table(exif)

with col2:
    st.markdown("### 2. Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("Indsæt API-nøgle til venstre.")
        else:
            if st.button("🚀 Start AI Analyse", use_container_width=True):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    with st.spinner('Analyserer...'):
                        prompt = "Du er en professionel fotograf. Analyser komposition, lys og teknik. Svar på dansk."
                        response = model.generate_content([prompt, image])
                        st.session_state['feedback'] = response.text
                except Exception as e:
                    st.error(f"Fejl: {e}")
            
            # Vis feedback hvis den findes
            if 'feedback' in st.session_state:
                st.markdown("---")
                st.write(st.session_state['feedback'])
                
                # PDF DOWNLOAD KNAP
                pdf_data = create_pdf(image, exif, st.session_state['feedback'])
                st.download_button(
                    label="📥 Download som A4 PDF",
                    data=pdf_data,
                    file_name="foto_feedback.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info("Upload et billede for at starte.")

# 4. FOOTER
st.markdown('<div class="custom-footer">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
