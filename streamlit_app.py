import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS

# 1. DESIGN & LAYOUT KONFIGURATION (AI STUDIO STIL)
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Custom CSS: Tvinger alt tekst til hvid og styler linket
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff !important;
    }
    /* Tvinger alle labels og tekst til hvid */
    label, p, span, div, h1, h2, h3, .stMarkdown {
        color: #ffffff !important;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Styling af linket i sidemenuen */
    .stSidebar a {
        color: #4daafc !important;
        text-decoration: underline;
    }
    /* Footer styling */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #8b949e !important;
        text-align: center;
        padding: 15px;
        font-size: 12px;
        letter-spacing: 1px;
        border-top: 1px solid #30363d;
        z-index: 999;
    }
    .main .block-container {
        padding-bottom: 80px;
    }
    /* Tabel styling */
    table {
        color: white !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Funktion til at hente EXIF data
def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength', 'DateTimeDigitized']:
                exif_data[decoded] = value
    return exif_data

# 2. SIDEBAR (API NØGLE & OM APPEN)
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    
    # Link til Google AI Studio som ønsket
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Om appen")
    st.write("Denne app analyserer dine fotos og giver professionel feedback samt tekniske EXIF-data.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
st.subheader("AI ANALYSE")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload & Tekniske Data")
    uploaded_file = st.file_uploader("Vælg et billede...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Dit billede")
        
        # EXIF DATA TABEL
        exif = get_exif_data(image)
        if exif:
            st.markdown("#### Tekniske EXIF-data")
            st.table(exif)
        else:
            st.info("Ingen EXIF-data fundet i dette billede.")

with col2:
    st.markdown("### 2. Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("Indsæt venligst din API-nøgle i menuen til venstre.")
        else:
            if st.button("🚀 Start AI Analyse", use_container_width=True):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    
                    with st.spinner('Analyserer billedet...'):
                        prompt = "Du er en professionel fotograf. Analyser komposition, lys, teknik og motiv i dette billede. Giv konkrete råd til forbedring."
                        response = model.generate_content([prompt, image])
                        
                        st.markdown("---")
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Fejl: {str(e)}")
    else:
        st.info("Vent på upload...")

# 4. FOOTER
st.markdown("""
    <div class="custom-footer">
        FOTO FEEDBACK BY TOMMI HALLUM © 2026
    </div>
    """, unsafe_allow_html=True)
