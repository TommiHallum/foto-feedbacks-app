import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. DESIGN & LAYOUT KONFIGURATION (AI STUDIO STIL)
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Her indsætter vi "Custom CSS" for at ramme designet fra AI Studio
st.markdown("""
    <style>
    /* Baggrund og tekstfarve */
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* Overskrift styling */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -1px;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #161b22;
    }
    /* Footer styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #666;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        letter-spacing: 1px;
        border-top: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SIDEBAR (API NØGLE & OM APPEN) - Bevarer din eksisterende funktion
with st.sidebar:
    st.title("Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    st.info("Du kan få en gratis nøgle hos Google AI Studio.")
    
    st.divider()
    st.subheader("Om appen")
    st.write("""
    Denne app analyserer dine fotos og giver professionel feedback. 
    Designet er inspireret af AI Studio, men funktionaliteten er din egen.
    """)

# 3. HOVEDINDHOLD (DESIGN FRA AI STUDIO)
st.title("FOTO FEEDBACK")
st.write("### AI ANALYSE")

# Layout opdeling (to kolonner som i AI Studio)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Upload dit billede")
    uploaded_file = st.file_input("Vælg et billede...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True, caption="Dit uploadede billede")

with col2:
    st.markdown("#### AI Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("Venligst indsæt din API-nøgle i sidemenuen for at starte analysen.")
        else:
            if st.button("Start AI Analyse"):
                try:
                    # Konfigurer Gemini
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    
                    with st.spinner('Analyserer billedet...'):
                        response = model.generate_content(["Analyser dette billede professionelt og giv konstruktiv feedback på komposition, lys og motiv.", image])
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Der skete en fejl: {e}")
    else:
        st.write("Vent på analyse... (Upload et billede først)")

# 4. FOOTER (SOM ANFØRT I DINE RETTELSER)
st.markdown(f"""
    <div class="footer">
        FOTO FEEDBACK BY TOMMI HALLUM © 2026
    </div>
    """, unsafe_allow_html=True)
