import os
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="J.A.R.V.I.S. AI", page_icon="🤖", layout="centered")

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

# 1. Diagnóstico de API Key
api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Configuración")
    if not api_key:
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    else:
        st.success("✅ API Key detectada desde Secrets")

if not api_key:
    st.warning("⚠️ Ingresa tu API Key de Gemini en la barra lateral o en Secrets para continuar.")
    st.stop()

# 2. Configurar Gemini con manejo explícito de errores
try:
    genai.configure(api_key=api_key)
    # Probar modelo estándar
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"❌ Error al configurar la API de Gemini: {e}")
    st.stop()

# 3. Inicializar Chat
if "chat" not in st.session_state:
    try:
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"❌ Error al iniciar el chat: {e}")
        st.stop()

# 4. Mostrar historial
for message in st.session_state.chat.history:
    role = "user" if message.role == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.parts[0].text)

# 5. Capturar entrada de usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"❌ Error al generar respuesta: {e}")
