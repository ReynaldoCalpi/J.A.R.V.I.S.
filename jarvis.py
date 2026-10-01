import os
import streamlit as st
import google.generativeai as genai

# Configuración de página con interfaz estilo J.A.R.V.I.S.
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

# Estilos visuales oscuros con acentos cian/azul
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #00d2ff;
    }
    .stChatMessage {
        background-color: #121824;
        border-radius: 10px;
        border: 1px solid #1e293b;
    }
    h1 {
        color: #00d2ff !important;
        font-family: 'Courier New', monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")
st.caption("Sistema de Inteligencia Artificial desplegado en la nube")

# Gestión de la clave de API (Streamlit Secrets o entrada manual en barra lateral)
api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Configuración")
    if not api_key:
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    else:
        st.success("API Key cargada desde Secrets")
    
    st.markdown("---")
    st.markdown("### Estado del Sistema")
    st.markdown("🟢 **Servidor Cloud:** Activo")
    st.markdown("🟢 **Modelo:** Gemini 1.5 Flash")

if not api_key:
    st.warning("⚠️ Ingrese su API Key de Google Gemini en la barra lateral para activar los sistemas.")
    st.stop()

# Inicialización de la API de Gemini
genai.configure(api_key=api_key)

# Configurar el modelo con la personalidad de JARVIS
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=(
            "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
            "Responde siempre en español con elegancia, brevedad, eficiencia y un toque refinado. "
            "Estás interactuando a través de un panel web en la nube."
        )
    )
    st.session_state.chat = model.start_chat(history=[])

# Mostrar historial de conversación
for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.parts[0].text)

# Entrada de mensaje del usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"Error procesando la solicitud: {str(e)}")
