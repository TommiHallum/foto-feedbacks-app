import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Konfiguration af siden (Moderne layout)
st.set_page_config(page_title="AI Foto Feedback", page_icon="📸", layout="wide")

# Custom CSS for at give det AI Studio look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #4F46E5;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        color: white;
    }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar til API Nøgle
with st.sidebar:
    st.title("⚙️ Indstillinger")
    api_key = st.text_input("Indsæt din Gemini API Key her:", type="password")
    st.info("Din nøgle bruges kun til denne session.")
    st.divider()
    st.markdown("### Om appen")
    st.write("Denne app bruger Google Gemini til at analysere dine fotos som en professionel kritiker.")

# Overskrift
st.title("📸 Din Personlige AI Fotokritiker")
st.write("Få professionel feedback på din komposition, teknik og historie.")
st.divider()

# 3. Hovedindhold i to kolonner
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') # Opdateret til nyeste stabile version

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.subheader("1. Upload dit billede")
            uploaded_file = st.file_uploader("Vælg et billede (JPG, PNG)...", type=["jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption='Dit uploadede billede', use_container_width=True)
                
                # Analyse-knappen ligger under billedet
                analyze_button = st.button('🚀 Analyser mit billede')

        with col2:
            st.subheader("2. AI Feedback")
            if uploaded_file is not None:
                if analyze_button:
                    with st.spinner('Gemini analyserer billedet grundigt...'):
                        # Din originale Prompt (bevaret 100%)
                        prompt = """
                        Du er en ekspert-fotograf og underviser. 
                        Analyser dette billede grundigt og giv feedback på:
                        1. Komposition og beskæring.
                        2. Lys, farver og teknik.
                        3. Den visuelle historie (hvad fortæller billedet?).
                        4. List også EXIF data fra billedet i en lysgrå boks. Boksen skal være før feedback med data på hver linje.
                        
                        Vær konstruktiv, venlig og giv ét konkret råd til forbedring.
                        Svar på dansk i et letforståeligt sprog.
                        """
                        
                        response = model.generate_content([prompt, image])
                        
                        # Vis feedback i en pæn boks
                        st.markdown("---")
                        st.markdown(response.text)
                else:
                    st.info("Tryk på knappen 'Analyser mit billede' for at starte.")
            else:
                st.light_box = st.info("Ventet på billede...")

    except Exception as e:
        st.error(f"Der opstod en fejl: {e}")
else:
    # Besked hvis API nøgle mangler
    st.warning("👈 Venligst indsæt din Gemini API-nøgle i menuen til venstre for at starte.")
    st.image("https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
