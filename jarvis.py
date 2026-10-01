import os
import streamlit as st
from google import genai
from google.genai import types

# Configuración de interfaz
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

# Inicialización del cliente con la nueva API de Interactions
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error al conectar cliente: {e}")
    st.stop()

# Guardar historial de la conversación en Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# Desplegar historial en pantalla
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
        # Estructurar historial de mensajes para la nueva API
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])]
            )
            for m in st.session_state.messages
        ]

        # Generación de contenido con la API de Interactions
        response = client.models.generate_content(
            model="gemini-2.5-flash",
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
        # Reintento de respaldo con modelo gemini-1.5-flash
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="Eres J.A.R.V.I.S. Responde en español con elegancia y brevedad."
                )
            )
            respuesta_texto = response.text
            st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(respuesta_texto)
        except Exception as err_fallback:
            st.error(f"❌ Error procesando la solicitud: {err_fallback}")
