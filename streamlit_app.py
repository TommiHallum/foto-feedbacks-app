import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. DESIGN & LAYOUT KONFIGURATION (AI STUDIO STIL)
st.set_page_config(page_title="Foto Feedback - AI Analyse", layout="wide")

# Her indsætter vi "Custom CSS" for at ramme det mørke AI Studio design
st.markdown("""
    <style>
    /* Baggrund og tekstfarve */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* Gør sidebar mørkere */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Overskrift styling */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    /* Footer styling */
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
    /* Justering så indhold ikke gemmes bag footer */
    .main .block-container {
        padding-bottom: 80px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SIDEBAR (API NØGLE & OM APPEN)
with st.sidebar:
    st.title("Indstillinger")
    # Bevarer muligheden for selv at indsætte API-nøgle
    api_key = st.text_input("Indsæt din Gemini API-nøgle her:", type="password")
    
    st.markdown("---")
    st.subheader("Om appen")
    st.write("""
    Denne app bruger Googles Gemini AI til at give dig professionel feedback på dine billeder.
    
    **Sådan gør du:**
    1. Indsæt din API-nøgle ovenfor.
    2. Upload et billede i hovedvinduet.
    3. Tryk på 'Start AI Analyse'.
    """)
    st.info("Du kan hente en gratis API-nøgle hos Google AI Studio.")

# 3. HOVEDINDHOLD
st.title("FOTO FEEDBACK")
st.subheader("AI ANALYSE")

# Layout opdeling i to kolonner
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload")
    # RETTELSE: Her stod før file_input, som gav fejlen. Nu rettet til file_uploader.
    uploaded_file = st.file_uploader("Vælg et billede (JPG, PNG)...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Dit valgte billede")

with col2:
    st.markdown("### 2. Feedback")
    if uploaded_file is not None:
        if not api_key:
            st.warning("⚠️ Venligst indsæt din API-nøgle i sidemenuen til venstre.")
        else:
            if st.button("🚀 Start AI Analyse", use_container_width=True):
                try:
                    # Konfigurer Gemini
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    with st.spinner('Analyserer billedet...'):
                        # AI Prompt
                        prompt = "Du er en professionel fotograf. Analyser dette billede og giv konstruktiv feedback på komposition, lys, farver og motiv. Giv også ét konkret råd til forbedring."
                        response = model.generate_content([prompt, image])
                        
                        st.markdown("---")
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Der skete en fejl: {str(e)}")
    else:
        st.info("Upload et billede til venstre for at se analysen her.")

# 4. FOOTER (Som ønsket i designrettelsen)
st.markdown(f"""
    <div class="custom-footer">
        FOTO FEEDBACK BY TOMMI HALLUM © 2026
    </div>
    """, unsafe_allow_html=True)
