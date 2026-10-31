import os
import streamlit as st
from google import genai
from google.genai import types

# Configuración de interfaz estilo J.A.R.V.I.S.
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

# Estilos CSS estilo J.A.R.V.I.S.
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #00d2ff; }
    .stChatMessage { background-color: #121824; border-radius: 10px; border: 1px solid #1e293b; }
    h1 { color: #00d2ff !important; font-family: 'Courier New', monospace; text-shadow: 0 0 8px #00d2ff55; }
    .stSidebar { background-color: #080a0f; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. Cloud Interface")

# Lectura de la API Key
api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Protocolos del Sistema")
    if not api_key:
        api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    else:
        st.success("✅ API Key autenticada")

if not api_key:
    st.warning("⚠️ Clave de acceso requerida para inicializar los subsistemas de J.A.R.V.I.S.")
    st.stop()

# Conectar cliente oficial de Google GenAI
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error al inicializar cliente: {e}")
    st.stop()

# Consulta en tiempo real de los modelos habilitados para tu API Key
@st.cache_data(ttl=3600)
def obtener_modelos_disponibles(_api_key):
    try:
        temp_client = genai.Client(api_key=_api_key)
        modelos_validos = []
        for m in temp_client.models.list():
            actions = getattr(m, 'supported_actions', []) or getattr(m, 'supported_generation_methods', [])
            # Filtrar solo modelos aptos para chat/texto (generateContent)
            if not actions or 'generateContent' in str(actions):
                nombre_limpio = m.name.replace('models/', '') if m.name else ""
                if nombre_limpio and not any(x in nombre_limpio for x in ["embedding", "imagen", "tts", "stt"]):
                    modelos_validos.append(nombre_limpio)
        
        if modelos_validos:
            # Priorizar modelos "flash" por velocidad
            modelos_validos.sort(key=lambda x: (0 if 'flash' in x else 1, x))
            return modelos_validos
    except Exception:
        pass
    
    # Respaldo seguro en caso de fallo de red
    return ["gemini-2.0-flash", "gemini-1.5-flash"]

lista_modelos = obtener_modelos_disponibles(api_key)

with st.sidebar:
    st.markdown("---")
    st.subheader("🧠 Núcleo de IA")
    modelo_activo = st.selectbox(
        "Modelo asignado dinámicamente:",
        options=lista_modelos,
        index=0,
        help="Lista obtenida en tiempo real desde tu cuenta de Google AI Studio."
    )

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
        # Formato de historial para API de Google GenAI
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])]
            )
            for m in st.session_state.messages
        ]

        # Configuración del sistema J.A.R.V.I.S.
        configuracion_jarvis = types.GenerateContentConfig(
            system_instruction=(
                "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
                "Responde siempre en español con elegancia, alta precisión, brevedad y un trato refinado hacia el usuario, a quien te diriges como 'señor'."
            ),
            temperature=0.7
        )

        # Respuesta en Streaming para experiencia en tiempo real
        with st.chat_message("assistant", avatar="🤖"):
            contenedor_respuesta = st.empty()
            texto_acumulado = ""

            response_stream = client.models.generate_content_stream(
                model=modelo_activo,
                contents=contents,
                config=configuracion_jarvis
            )

            for chunk in response_stream:
                if chunk.text:
                    texto_acumulado += chunk.text
                    contenedor_respuesta.markdown(texto_acumulado + "▌")

            contenedor_respuesta.markdown(texto_acumulado)

        st.session_state.messages.append({"role": "assistant", "content": texto_acumulado})

    except Exception as e:
        st.error(f"❌ Error procesando solicitud con el modelo `{modelo_activo}`: {e}")
