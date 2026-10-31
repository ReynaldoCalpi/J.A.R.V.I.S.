import os
import time
import streamlit as st
from google import genai
from google.genai import types

# Configuración de interfaz estilo J.A.R.V.I.S.
st.set_page_config(page_title="J.A.R.V.I.S. AI System", page_icon="🤖", layout="centered")

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

# Inicializar cliente oficial de Google GenAI
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error al inicializar cliente: {e}")
    st.stop()

# Consulta en tiempo real de modelos activos habilitados en la API Key
@st.cache_data(ttl=600)
def obtener_modelos_cuenta(_api_key):
    try:
        temp_client = genai.Client(api_key=_api_key)
        modelos_disponibles = []
        for m in temp_client.models.list():
            nombre = m.name.replace("models/", "") if hasattr(m, "name") and m.name else ""
            if nombre and not any(x in nombre for x in ["embedding", "imagen", "tts", "stt", "bison"]):
                modelos_disponibles.append(nombre)
        if modelos_disponibles:
            modelos_disponibles.sort(key=lambda x: (0 if 'flash' in x else 1, x))
            return modelos_disponibles
    except Exception:
        pass
    # Respaldo actualizado según la recomendación del servidor
    return ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]

lista_modelos = obtener_modelos_cuenta(api_key)

with st.sidebar:
    st.markdown("---")
    st.subheader("🧠 Núcleo de IA")
    modelo_preferido = st.selectbox(
        "Modelo principal:",
        options=lista_modelos,
        index=0,
        help="Sincronizado dinámicamente con tu cuenta de Google AI Studio."
    )

# Historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Desplegar conversación guardada
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Captura de entrada del usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])]
        )
        for m in st.session_state.messages
    ]

    configuracion_jarvis = types.GenerateContentConfig(
        system_instruction=(
            "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
            "Responde siempre en español con elegancia, alta precisión, brevedad y un trato refinado hacia el usuario, a quien te diriges como 'señor'."
        ),
        temperature=0.7
    )

    # Orden de prueba: Modelo elegido -> Resto de la lista de modelos activos
    modelos_a_intentar = [modelo_preferido] + [m for m in lista_modelos if m != modelo_preferido]

    with st.chat_message("assistant", avatar="🤖"):
        contenedor_respuesta = st.empty()
        texto_acumulado = ""
        exito = False

        for mod in modelos_a_intentar:
            try:
                response_stream = client.models.generate_content_stream(
                    model=mod,
                    contents=contents,
                    config=configuracion_jarvis
                )

                for chunk in response_stream:
                    if chunk.text:
                        texto_acumulado += chunk.text
                        contenedor_respuesta.markdown(texto_acumulado + "▌")

                contenedor_respuesta.markdown(texto_acumulado)
                exito = True
                break  # Éxito: sale del bucle sin mostrar errores

            except Exception as e:
                err_msg = str(e)
                # Captura de 404, 503, 429 y conmuta silenciosamente al siguiente modelo
                if any(k in err_msg for k in ["404", "NOT_FOUND", "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    st.toast(f"⚙️ Conmutando nodo `{mod}` -> probando alternativa...", icon="🔄")
                    time.sleep(0.3)
                    continue
                else:
                    st.error(f"❌ Error en subsistema `{mod}`: {e}")
                    break

        if exito and texto_acumulado:
            st.session_state.messages.append({"role": "assistant", "content": texto_acumulado})
        elif not exito:
            st.error("❌ No se pudo conectar con ningún modelo activo en tu API Key. Verifica tus credenciales.")
