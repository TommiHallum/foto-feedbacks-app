import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Konfiguration af siden
st.set_page_config(page_title="AI Foto Feedback", page_icon="📸")
st.title("📸 Din Personlige AI Fotokritiker")
st.write("Upload et billede, og få professionel feedback på få sekunder.")

# 2. Håndtering af API Nøgle (Sikkerhed)
api_key = st.sidebar.text_input("Indsæt din Gemini API Key her:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # 3. Upload felt
        uploaded_file = st.file_uploader("Vælg et billede...", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption='Dit billede', use_container_width=True)
            
            if st.button('Analyser mit billede'):
                with st.spinner('Gemini kigger på dit billede...'):
                    # Her er din specifikke Prompt
                    prompt = """
                    Du er en ekspert-fotograf og underviser. 
                    Analyser dette billede grundigt og giv feedback på:
                    1. Komposition og beskæring.
                    2. Lys, farver og teknik.
                    3. Den visuelle historie (hvad fortæller billedet?).
                    
                    Vær konstruktiv, venlig og giv ét konkret råd til forbedring.
                    Svar på dansk i et letforståeligt sprog.
                    """
                    
                    response = model.generate_content([prompt, image])
                    st.subheader("Feedback:")
                    st.write(response.text)
    except Exception as e:
        st.error(f"Der opstod en fejl: {e}")
else:
    st.info("👈 Start med at indsætte din API-nøgle i menuen til venstre for at komme i gang.")
