import streamlit as st
import google.generativeai as genai
from PIL import Image
from PIL.ExifTags import TAGS
from fpdf import FPDF
import io
import os

# 1. DESIGN & LAYOUT KONFIGURATION
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3, h4, p, span { color: #ffffff !important; }
    
    /* Upload felt styling */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 2px dashed #4F46E5;
    }
    [data-testid="stFileUploader"] section { color: #0e1117 !important; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small { color: #0e1117 !important; }

    /* Knap styling */
    div.stButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    
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

# 2. SIDEBAR
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    st.markdown('Få din nøgle hos <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>', unsafe_allow_html=True)
    st.divider()
    st.subheader("Om appen")
    st.write("Professionel fotoanalyse.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")

# Top sektion: Upload
st.markdown("### 1. Upload billede")
uploaded_file = st.file_uploader("Vælg et billede (Max 20MB):", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    exif = get_exif_data(image)

    # TRIN 1: Billede og EXIF side om side
    top_col1, top_col2 = st.columns([2, 1])
    with top_col1:
        st.image(image, use_container_width=True, caption="Dit billede")
    with top_col2:
        st.markdown("#### Tekniske EXIF-data")
        if exif:
            st.table(exif)
        else:
            st.info("Ingen EXIF data fundet.")

    # Analyse knap
    if api_key:
        if st.button("🚀 Start AI Analyse", use_container_width=True):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest')
                with st.spinner('Analyserer...'):
                    # Vi beder AI om at bruge faste overskrifter så vi kan dele teksten op
                    prompt = """
                    Du er en professionel fotograf. Analyser billedet og svar KUN i disse 4 sektioner:
                    [SEKTION1] Komposition og beskæring: (Skriv feedback her)
                    [SEKTION2] Lys og eksponering: (Skriv feedback her)
                    [SEKTION3] Historie og stemning: (Skriv feedback her)
                    [SEKTION4] Professionelle tips til forbedring: (Skriv feedback her)
                    Svar på dansk.
                    """
                    response = model.generate_content([prompt, image])
                    full_text = response.text
                    
                    # Split teksten op så vi kan placere den i de rigtige kolonner
                    st.session_state['s1'] = full_text.split("[SEKTION2]")[0].replace("[SEKTION1]", "").strip()
                    st.session_state['s2'] = full_text.split("[SEKTION2]")[1].split("[SEKTION3]")[0].strip()
                    st.session_state['s3'] = full_text.split("[SEKTION3]")[1].split("[SEKTION4]")[0].strip()
                    st.session_state['s4'] = full_text.split("[SEKTION4]")[1].strip()
            except Exception as e:
                st.error(f"Fejl: {e}")

    # TRIN 2, 3, 4, 5: Placering af analyse resultater
    if 's1' in st.session_state:
        st.divider()
        
        # Række 1: Analyse under billedet og Lys til højre
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("### 1. Komposition og beskæring")
            st.write(st.session_state['s1'])
        with row1_col2:
            st.markdown("### 2. Lys og eksponering")
            st.write(st.session_state['s2'])
            
        st.divider()
        
        # Række 2: Historie til venstre og Tips til højre
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("### 3. Historie og stemning")
            st.write(st.session_state['s3'])
        with row2_col2:
            st.markdown("### Professionelle tips til forbedring")
            st.success(st.session_state['s4'])

else:
    st.info("Upload et billede for at se analysen.")

# 4. FOOTER
st.markdown('<div class="custom-footer">FOTO FEEDBACK BY TOMMI HALLUM © 2026</div>', unsafe_allow_html=True)
