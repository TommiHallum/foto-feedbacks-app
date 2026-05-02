import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. DESIGN & LAYOUT KONFIGURATION (AI STUDIO STIL)
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Custom CSS for at ramme AI Studio looket
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #8b949e;
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
    </style>
    """, unsafe_allow_html=True)

# 2. SIDEBAR (API NØGLE & OM APPEN)
with st.sidebar:
    st.title("Indstillinger")
    # Bevarer dit ønske om selv at kunne paste API-nøglen
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    
    st.markdown("---")
    st.subheader("Om appen")
    st.write("""
    Denne app analyserer dine fotos og giver professionel feedback. 
    Designet er opdateret til AI Studio-stilen.
    """)
    st.info("Få din nøgle hos Google AI Studio.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
st.subheader("AI ANALYSE")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload")
    uploaded_file = st.file_uploader("Vælg et billede...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Dit billede")

with col2:
    st.markdown("### 2. Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("Indsæt venligst din API-nøgle i menuen til venstre.")
        else:
            if st.button("🚀 Start AI Analyse", use_container_width=True):
                try:
                    # BRUGER GEMINI-FLASH-LATEST SOM DU BAD OM
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-flash-latest')[cite: 1]
                    
                    with st.spinner('Analyserer...'):
                        prompt = "Du er en professionel fotograf. Analyser komposition, lys og teknik i dette billede."
                        response = model.generate_content([prompt, image])
                        
                        st.markdown("---")
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Fejl: {str(e)}")
    else:
        st.info("Vent på upload...")

# 4. FOOTER (OPDATERET DESIGN)
st.markdown(f"""
    <div class="custom-footer">
        FOTO FEEDBACK BY TOMMI HALLUM © 2026
    </div>
    """, unsafe_allow_html=True)[cite: 1]
