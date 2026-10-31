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
    div[data-testid="stFileUploader"] { background-color: #121824; border: 1px dashed #00d2ff55; border-radius: 8px; padding: 10px; }
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

# Consulta en tiempo real de modelos multimodales activos
@st.cache_data(ttl=600)
def obtener_modelos_multimodales(_api_key):
    try:
        temp_client = genai.Client(api_key=_api_key)
        modelos_disponibles = []
        excluir = ["embedding", "imagen", "tts", "stt", "bison", "native-audio", "audio", "bidi", "live", "realtime"]
        for m in temp_client.models.list():
            nombre = m.name.replace("models/", "") if hasattr(m, "name") and m.name else ""
            if nombre and not any(x in nombre.lower() for x in excluir):
                modelos_disponibles.append(nombre)
                
        if modelos_disponibles:
            modelos_disponibles.sort(key=lambda x: (0 if 'flash' in x.lower() else 1, x))
            return modelos_disponibles
    except Exception:
        pass
    
    return ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

lista_modelos = obtener_modelos_multimodales(api_key)

with st.sidebar:
    st.markdown("---")
    st.subheader("🧠 Núcleo de IA")
    modelo_preferido = st.selectbox(
        "Modelo principal:",
        options=lista_modelos,
        index=0,
        help="Sincronizado dinámicamente con modelos multimodales activos."
    )

# Historial de conversación
if "messages" not in st.session_state:
    st.session_state.messages = []

# Desplegar conversación anterior (con renderizado de archivos adjuntos)
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("file_bytes") and msg.get("file_type"):
            if msg["file_type"].startswith("image/"):
                st.image(msg["file_bytes"], caption=f"📸 Archivo visual: {msg.get('file_name')}", use_container_width=True)
            else:
                st.info(f"📄 Documento adjunto cargado: `{msg.get('file_name')}`")
        if msg.get("content"):
            st.markdown(msg["content"])

# Módulo de carga de archivos / datos en la interfaz
with st.expander("📎 Adjuntar imagen o documento para análisis", expanded=False):
    archivo_adjunto = st.file_uploader(
        "Formatos soportados: Imágenes (PNG, JPG, WEBP), PDF, TXT, CSV, JSON",
        type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "csv", "json"],
        key="file_uploader"
    )

# Captura de orden del usuario
if prompt := st.chat_input("Aguardando sus órdenes, señor..."):
    partes_entrada = []
    bytes_archivo = None
    tipo_archivo = None
    nombre_archivo = None

    # Procesamiento del archivo adjunto si fue seleccionado
    if archivo_adjunto is not None:
        bytes_archivo = archivo_adjunto.getvalue()
        tipo_archivo = archivo_adjunto.type or "application/octet-stream"
        nombre_archivo = archivo_adjunto.name
        
        # Mapeo correcto de tipos MIME para archivos de texto plano/CSV/JSON si no se detectan automáticamente
        if nombre_archivo.endswith(".csv"):
            tipo_archivo = "text/csv"
        elif nombre_archivo.endswith(".json"):
            tipo_archivo = "application/json"
        elif nombre_archivo.endswith(".txt"):
            tipo_archivo = "text/plain"

        partes_entrada.append(types.Part.from_bytes(data=bytes_archivo, mime_type=tipo_archivo))

    if prompt:
        partes_entrada.append(types.Part.from_text(text=prompt))

    # Registrar mensaje en historial
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "file_bytes": bytes_archivo,
        "file_type": tipo_archivo,
        "file_name": nombre_archivo,
        "parts": partes_entrada
    })

    # Renderizar entrada actual en UI
    with st.chat_message("user", avatar="👤"):
        if bytes_archivo and tipo_archivo:
            if tipo_archivo.startswith("image/"):
                st.image(bytes_archivo, caption=f"📸 Archivo visual: {nombre_archivo}", use_container_width=True)
            else:
                st.info(f"📄 Documento adjunto cargado: `{nombre_archivo}`")
        if prompt:
            st.markdown(prompt)

    # Reconstrucción del historial completo para enviar a Gemini
    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        if m.get("parts"):
            contents.append(types.Content(role=role, parts=m["parts"]))
        else:
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    configuracion_jarvis = types.GenerateContentConfig(
        system_instruction=(
            "Eres J.A.R.V.I.S., la inteligencia artificial de Tony Stark. "
            "Responde siempre en español con elegancia, alta precisión, brevedad y un trato refinado hacia el usuario, a quien te diriges como 'señor'. "
            "Si el usuario adjunta una imagen o un documento (PDF, CSV, JSON, TXT), analízalo en detalle y extrae las conclusiones solicitadas."
        ),
        temperature=0.7
    )

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
                break

            except Exception as e:
                err_msg = str(e)
                if any(k in err_msg for k in ["400", "INVALID_ARGUMENT", "404", "NOT_FOUND", "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    st.toast(f"⚙️ Conmutando nodo `{mod}` por sobrecarga/incompatibilidad...", icon="🔄")
                    time.sleep(0.3)
                    continue
                else:
                    st.error(f"❌ Error en subsistema `{mod}`: {e}")
                    break

        if exito and texto_acumulado:
            st.session_state.messages.append({
                "role": "assistant",
                "content": texto_acumulado,
                "parts": [types.Part.from_text(text=texto_acumulado)]
            })
        elif not exito:
            st.error("❌ No se pudo procesar la solicitud en ninguno de los nodos activos.")
