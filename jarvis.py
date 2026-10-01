import os
import streamlit as st
import google.generativeai as genai

# Configuración inicial de la interfaz
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #00d2ff; }
    .stChatMessage { background-color: #121824; border-radius: 10px; border: 1px solid #1e293b; }
    h1 { color: #00d2ff !important; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

# Carga de la API Key
api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Configuración")
    if not api_key:
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    else:
        st.success("✅ API Key cargada")

if not api_key:
    st.warning("⚠️ Ingrese su API Key de Google Gemini en la barra lateral para continuar.")
    st.stop()

genai.configure(api_key=api_key)

# Detección dinámica y robusta de modelos disponibles
@st.cache_resource
def obtener_modelo_valido():
    try:
        modelos_disponibles = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponibles.append(m.name)
        
        # Priorizar modelos tipo 'flash'
        for m in modelos_disponibles:
            if 'flash' in m:
                return m
        
        # Si hay cualquier otro modelo activo en la cuenta, utilizar el primero
        if modelos_disponibles:
            return modelos_disponibles[0]
    except Exception:
        pass
    
    # Modelo predeterminado estándar en caso de error de lista
    return "models/gemini-1.5-flash"

modelo_activo = obtener_modelo_valido()

with st.sidebar:
    st.info(f"Modelo activo: `{modelo_activo}`")

# Inicialización del modelo de Gemini con personalidad J.A.R.V.I.S.
model = genai.GenerativeModel(
    model_name=modelo_activo,
    system_instruction=(
        "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
        "Responde siempre en español con elegancia, brevedad, eficiencia y un trato refinado."
    )
)

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Despliegue del historial de conversación
for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.parts[0].text)

# Entrada del usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"❌ Error procesando la solicitud: {e}")
