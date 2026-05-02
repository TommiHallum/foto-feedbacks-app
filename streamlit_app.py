import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Custom CSS for optimeret læsbarhed og knapper
st.markdown("""
    <style>
    /* Baggrund */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Overskrifter og standard tekst */
    h1, h2, h3, h4, p, span { color: #ffffff !important; }
    
    /* Gør upload-feltet læsbart */
    [data-testid="stFileUploader"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
    }
    /* Tekst indeni upload-feltet (skal være mørk for at kunne læses) */
    [data-testid="stFileUploader"] section {
        color: #0e1117 !important;
    }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small {
        color: #0e1117 !important;
    }

    /* Styling af knapper (AI Analyse & Download) */
    div.stButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
        border: 1px solid #6366f1 !important;
    }
    div.stButton > button:hover {
        background-color: #4338CA !important;
        border-color: #ffffff !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stSidebar a { color: #4daafc !important; text-decoration: underline !important; }
    
    /* Footer */
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #8b949e !important;
        text-align: center; padding: 15px; font-size: 12px;
        border-top: 1px solid #30363d; z-index: 999;
    }
    .main .block-container { padding-bottom: 80px; }
    
    /* Tabel styling */
    .stTable td, .stTable th { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Funktion til EXIF
def get_exif_data(image):
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                    exif_data[decoded] = str(value)
    except:
        pass
    return exif_data

# Funktion: Generer PDF
def create_pdf(image, exif_dict, feedback_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Foto Feedback Rapport", ln=True, align='C')
    pdf.ln(10)
    
    img_byte_arr = io.BytesIO()
    image.convert("RGB").save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    pdf.image(img_byte_arr, x=10, y=30, w=90, type='JPEG')
    pdf.ln(100) 
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Tekniske Data:", ln=True)
    pdf.set_font("Arial", size=10)
    if exif_dict:
        for key, val in exif_dict.items():
            pdf.cell(200, 7, f"{key}: {val}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "AI Feedback:", ln=True)
    pdf.set_font("Arial", size=10)
    clean_text = feedback_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

# 2. SIDEBAR
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    # Link til API nøgle
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)
    st.divider()
    st.subheader("Om appen")
    st.write("Professionel fotoanalyse drevet af AI.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
st.subheader("AI ANALYSE")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload")
    # Her har jeg ændret teksten manuelt for at vise 20MB grænsen tydeligt
    st.write("Upload dit billede herunder (Max 20MB):")
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Dit uploadede billede")
        exif = get_exif_data(image)
        if exif:
            st.markdown("#### Tekniske Data")
            st.table(exif)

with col2:
    st.markdown("### 2. Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("⚠️ Venligst indsæt din API-nøgle i menuen til venstre for at starte.")
        else:
            # Knappen er nu altid stylet blå (via CSS'en ovenfor)
            if st.button("🚀 Start AI Analyse", use_container_width=True):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    with st.spinner('Analyserer...'):
                        prompt = "Du er en professionel fotograf. Analyser billedet grundigt (komposition, lys, historie) og giv feedback på dansk."
                        response = model.generate_content([prompt, image])
                        st.session_state['feedback'] = response.text
                        st.session_state['current_image'] = image
                        st.session_state['current_exif'] = exif
                except Exception as e:
                    st.error(f"Fejl: {e}")
            
            if 'feedback' in st.session_state:
                st.markdown("---")
                st.write(st.session_state['feedback'])
                
                pdf_output = create_pdf(
                    st.session_state['current_image'], 
                    st.session_state['current_exif'], 
                    st.session_state['feedback']
                )
                
                st.download_button(
                    label="📥 Download som A4 PDF",
                    data=pdf_output,
                    file_name="foto_feedback.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info("Upload et billede til venstre for at se analysen her.")

# 4. FOOTER
st.markdown('<div class="custom-footer">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
