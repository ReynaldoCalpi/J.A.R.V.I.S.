import os
import streamlit as st
from google import genai
from google.genai import types

# Configuración de interfaz estilo J.A.R.V.I.S.
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #00d2ff; }
    .stChatMessage { background-color: #121824; border-radius: 10px; border: 1px solid #1e293b; }
    h1 { color: #00d2ff !important; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

# Lectura de la API Key
api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Configuración")
    if not api_key:
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    else:
        st.success("✅ API Key cargada correctamente")

if not api_key:
    st.warning("⚠️ Ingresa tu API Key de Google Gemini en la barra lateral para activar los sistemas.")
    st.stop()

# Conectar cliente oficial de Google GenAI
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error al inicializar cliente: {e}")
    st.stop()

# Detección automática del modelo activo en TU cuenta
@st.cache_resource
def detectar_modelo_real(_client_obj):
    try:
        # Pide a la API la lista exacta de modelos permitidos para tu API Key
        modelos = list(_client_obj.models.list())
        nombres = [m.name for m in modelos]
        
        # 1. Priorizar cualquier modelo disponible que contenga 'flash'
        for n in nombres:
            if 'flash' in n.lower():
                return n
        
        # 2. Si no hay 'flash', usar el primer modelo disponible de la lista
        if nombres:
            return nombres[0]
    except Exception:
        pass
    
    # Fallback directo en caso de fallo de lectura de lista
    return "gemini-2.5-flash"

modelo_activo = detectar_modelo_real(client)

with st.sidebar:
    st.info(f"Modelo asignado dinámicamente: `{modelo_activo}`")

# Estructura del historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Captura de entrada del usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        # Convertir historial al formato requerido por la API de Interactions
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])]
            )
            for m in st.session_state.messages
        ]

        # Llamada con el modelo detectado automáticamente
        response = client.models.generate_content(
            model=modelo_activo,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
                    "Responde siempre en español con elegancia, brevedad, eficiencia y un trato refinado."
                )
            )
        )

        respuesta_texto = response.text
        st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
        
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(respuesta_texto)

    except Exception as e:
        st.error(f"❌ Error procesando solicitud con el modelo `{modelo_activo}`: {e}")
