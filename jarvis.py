import os
import streamlit as st
import google.generativeai as genai

# Configuración inicial de interfaz
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #00d2ff; }
    .stChatMessage { background-color: #121824; border-radius: 10px; border: 1px solid #1e293b; }
    h1 { color: #00d2ff !important; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

# Lectura de clave de API
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

# Configurar API
genai.configure(api_key=api_key)

# Detección dinámica del modelo activo sin error 404
@st.cache_resource
def obtener_modelo_activo():
    modelos_candidatos = [
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-pro"
    ]
    for nombre in modelos_candidatos:
        try:
            m = genai.GenerativeModel(nombre)
            # Prueba ligera de generación de 1 token para validar disponibilidad
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return nombre
        except Exception:
            continue
    return "gemini-2.0-flash"

nombre_modelo_valido = obtener_modelo_activo()

with st.sidebar:
    st.info(f"Modelo activo: `{nombre_modelo_valido}`")

# Inicialización de Gemini con personalidad de JARVIS
model = genai.GenerativeModel(
    model_name=nombre_modelo_valido,
    system_instruction=(
        "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
        "Responde en español con elegancia, brevedad y eficiencia."
    )
)

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Mostrar conversación en pantalla
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
