import os
import streamlit as st
import google.generativeai as genai

# Configuración inicial
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #00d2ff; }
    .stChatMessage { background-color: #121824; border-radius: 10px; border: 1px solid #1e293b; }
    h1 { color: #00d2ff !important; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

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

# Detección automática de modelos disponibles en tu cuenta
@st.cache_resource
def detectar_modelo_disponible():
    try:
        modelos_disponibles = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponibles.append(m.name)
        
        # Priorizar versiones Flash disponibles
        for m in modelos_disponibles:
            if '2.5-flash' in m or '1.5-flash' in m:
                return m
        
        if modelos_disponibles:
            return modelos_disponibles[0]
    except Exception:
        pass
    
    return "models/gemini-2.5-flash"

modelo_activo = detectar_modelo_disponible()

with st.sidebar:
    st.info(f"Modelo activo: `{modelo_activo}`")

model = genai.GenerativeModel(
    model_name=modelo_activo,
    system_instruction=(
        "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
        "Responde siempre en español con elegancia, brevedad, eficiencia y un trato refinado."
    )
)

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.parts[0].text)

if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"❌ Error procesando la solicitud: {e}")
