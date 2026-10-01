import ctypes
import json
import os
import platform
import subprocess
import sys
import time
import psutil
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai

# Intentar importar librerías opcionales para la detección de Wake Word
try:
    import numpy as np
    import pyaudio
    from openwakeword.model import Model as WakeModel
    HAS_OPENWAKEWORD = True
except ImportError:
    HAS_OPENWAKEWORD = False

if platform.system() == "Windows":
    import winsound

# Archivo local para almacenar las tareas
TAREAS_FILE = "tareas.json"


# ==========================================
# 1. HERRAMIENTAS DEL SISTEMA (FUNCTIONS)
# ==========================================

def obtener_estado_sistema() -> str:
    """Retorna información en tiempo real del uso de CPU, Memoria RAM y almacenamiento del sistema."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disco = psutil.disk_usage('/').percent
    return f"Estado del sistema: CPU al {cpu}%, Memoria RAM al {ram}%, Disco principal al {disco}%."

def abrir_aplicacion(nombre_app: str) -> str:
    """Abre una aplicación en el sistema operativo (ejemplo: chrome, notepad, calculadora, spotify)."""
    so = platform.system().lower()
    app = nombre_app.lower()
    try:
        if "windows" in so:
            mapeo_apps = {
                "chrome": "chrome",
                "navegador": "chrome",
                "bloc de notas": "notepad",
                "notepad": "notepad",
                "calculadora": "calc",
                "explorador": "explorer",
                "cmd": "cmd",
                "terminal": "wt"
            }
            ejecutable = mapeo_apps.get(app, app)
            subprocess.Popen(f"start {ejecutable}", shell=True)
            return f"Abriendo {nombre_app}."
        elif "darwin" in so:
            subprocess.Popen(["open", "-a", nombre_app])
            return f"Iniciando {nombre_app} en macOS."
        else:
            subprocess.Popen([app])
            return f"Ejecutando {nombre_app} en Linux."
    except Exception as e:
        return f"No se pudo abrir {nombre_app}: {str(e)}"

# Códigos Virtual Keys de Windows para Teclas Multimedia
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

def _enviar_tecla(codigo_vk: int):
    if platform.system() == "Windows":
        ctypes.windll.user32.keybd_event(codigo_vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(codigo_vk, 0, 2, 0)

def controlar_volumen(accion: str, repeticiones: int = 5) -> str:
    """
    Controla el volumen del sistema operativo.
    :param accion: 'subir', 'bajar' o 'silenciar'/'mutear'.
    :param repeticiones: Número de saltos de volumen a aplicar.
    """
    accion = accion.lower()
    if any(k in accion for k in ["subir", "mas", "aumentar"]):
        for _ in range(repeticiones):
            _enviar_tecla(VK_VOLUME_UP)
        return "Volumen aumentado."
    elif any(k in accion for k in ["bajar", "menos", "reducir"]):
        for _ in range(repeticiones):
            _enviar_tecla(VK_VOLUME_DOWN)
        return "Volumen reducido."
    elif any(k in accion for k in ["silenciar", "mutear", "mute", "silencio"]):
        _enviar_tecla(VK_VOLUME_MUTE)
        return "Estado del volumen alterado."
    return "Acción de volumen no reconocida."

def controlar_reproduccion(accion: str) -> str:
    """
    Controla la reproducción multimedia (Spotify, YouTube, reproductores).
    :param accion: 'reproducir'/'pausar', 'siguiente', 'anterior', 'detener'.
    """
    accion = accion.lower()
    if any(k in accion for k in ["play", "pausa", "reproducir", "pausar"]):
        _enviar_tecla(VK_MEDIA_PLAY_PAUSE)
        return "Reproducción alternada (Play/Pausa)."
    elif any(k in accion for k in ["siguiente", "avanzar", "pasa"]):
        _enviar_tecla(VK_MEDIA_NEXT_TRACK)
        return "Siguiente pista."
    elif any(k in accion for k in ["anterior", "atras", "retroceder"]):
        _enviar_tecla(VK_MEDIA_PREV_TRACK)
        return "Pista anterior."
    elif any(k in accion for k in ["detener", "parar", "stop"]):
        _enviar_tecla(VK_MEDIA_STOP)
        return "Reproducción detenida."
    return "Comando multimedia no reconocido."

def _cargar_tareas() -> list:
    if os.path.exists(TAREAS_FILE):
        try:
            with open(TAREAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _guardar_tareas(tareas: list):
    with open(TAREAS_FILE, "w", encoding="utf-8") as f:
        json.dump(tareas, f, ensure_ascii=False, indent=2)

def agregar_tarea(descripcion: str) -> str:
    """Guarda una nueva tarea en la lista de pendientes."""
    tareas = _cargar_tareas()
    nueva_tarea = {"id": len(tareas) + 1, "descripcion": descripcion, "completada": False}
    tareas.append(nueva_tarea)
    _guardar_tareas(tareas)
    return f"Tarea agregada: '{descripcion}'."

def listar_tareas_pendientes() -> str:
    """Consulta y lista todas las tareas pendientes."""
    tareas = _cargar_tareas()
    pendientes = [t for t in tareas if not t.get("completada", False)]
    if not pendientes:
        return "No tiene tareas pendientes en este momento."
    lineas = [f"Tarea {t['id']}: {t['descripcion']}" for t in pendientes]
    return "Sus tareas pendientes son:\n" + "\n".join(lineas)

def completar_tarea(numero_tarea: int) -> str:
    """Marca una tarea como realizada usando su número identificador."""
    tareas = _cargar_tareas()
    for t in tareas:
        if t["id"] == numero_tarea:
            t["completada"] = True
            _guardar_tareas(tareas)
            return f"Tarea {numero_tarea} marcada como realizada."
    return f"No se encontró la tarea número {numero_tarea}."


# ==========================================
# 2. CONSOLIDACIÓN DE HERRAMIENTAS
# ==========================================

herramientas = [
    obtener_estado_sistema,
    abrir_aplicacion,
    controlar_volumen,
    controlar_reproduccion,
    agregar_tarea,
    listar_tareas_pendientes,
    completar_tarea
]


# ==========================================
# 3. DETECTOR DE PALABRA CLAVE (WAKE WORD)
# ==========================================

class DetectorWakeWord:
    def __init__(self, modelo="hey_jarvis"):
        self.modelo_nombre = modelo
        if HAS_OPENWAKEWORD:
            self.model = WakeModel(wakeword_models=[modelo], inference_framework="onnx")
            self.chunk_size = 1280
            self.format = pyaudio.paInt16
            self.channels = 1
            self.rate = 16000

    def esperar_activacion(self, umbral=0.5) -> bool:
        if HAS_OPENWAKEWORD:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            print("\n[MODO REPOSO: Esperando 'Hey JARVIS'...]")
            try:
                while True:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    prediction = self.model.predict(audio_data)
                    for m, score in prediction.items():
                        if score >= umbral:
                            print("\n¡Palabra clave detectada!")
                            stream.stop_stream()
                            stream.close()
                            audio.terminate()
                            return True
            except KeyboardInterrupt:
                stream.stop_stream()
                stream.close()
                audio.terminate()
                return False
        else:
            # Modo fallback en caso de no tener openwakeword instalado
            print("\n[MODO REPOSO (Presiona Enter o habla para activar)...]")
            try:
                input(">>> Presiona ENTER para hablar con JARVIS <<<")
                return True
            except KeyboardInterrupt:
                return False


# ==========================================
# 4. CLASE ASISTENTE JARVIS (GEMINI + STT/TTS)
# ==========================================

class AsistenteJARVIS:
    def __init__(self, api_key: str):
        # Motor Text-To-Speech (Voz)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        voces = self.engine.getProperty('voices')
        for voz in voces:
            if "spanish" in voz.name.lower() or "es" in voz.id.lower():
                self.engine.setProperty('voice', voz.id)
                break

        # Reconocimiento de Voz
        self.reconocedor = sr.Recognizer()

        # Configuración Gemini API con herramientas
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=herramientas,
            system_instruction=(
                "Eres J.A.R.V.I.S., un asistente virtual de IA sofisticado. "
                "Responde siempre en español de forma concisa, directa y elegante. "
                "Haz uso de las herramientas del sistema cuando se soliciten acciones."
            )
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    def tono_activacion(self):
        if platform.system() == "Windows":
            winsound.Beep(1200, 120)
        else:
            print("\a", end="")

    def tono_reposo(self):
        if platform.system() == "Windows":
            winsound.Beep(600, 180)
        else:
            print("\a", end="")

    def hablar(self, texto: str):
        print(f"\nJ.A.R.V.I.S.: {texto}")
        self.engine.say(texto)
        self.engine.runAndWait()

    def escuchar(self, timeout_escucha: int = 10) -> str:
        with sr.Microphone() as fuente:
            print(f"  [Escuchando... Ventana de atención activa ({timeout_escucha}s)]")
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=0.3)
            try:
                audio = self.reconocedor.listen(fuente, timeout=timeout_escucha, phrase_time_limit=12)
                texto = self.reconocedor.recognize_google(audio, language="es-ES")
                print(f"Tú: {texto}")
                return texto
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return None
            except sr.RequestError as e:
                print(f"Error de conexión STT: {e}")
                return None


# ==========================================
# 5. BUCLE PRINCIPAL DE CONVERSACIÓN
# ==========================================

def ejecutar_jarvis(jarvis: AsistenteJARVIS, detector: DetectorWakeWord, ventana_atencion_seg: int = 10):
    jarvis.hablar("Sistemas en línea y listos.")

    while True:
        # FASE 1: Esperar activación (Wake Word)
        if not detector.esperar_activacion():
            break

        # FASE 2: Entrar en ventana de atención
        jarvis.tono_activacion()
        modo_activo = True

        while modo_activo:
            comando = jarvis.escuchar(timeout_escucha=ventana_atencion_seg)

            if comando:
                comando_lower = comando.lower()

                # Comandos de salida inmediata
                if any(p in comando_lower for p in ["apagar todo", "desconectar sistema", "salir del programa"]):
                    jarvis.hablar("Desconectando sistemas principales. Hasta pronto, señor.")
                    return

                if any(p in comando_lower for p in ["gracias", "es todo", "descansa", "silencio", "adiós"]):
                    jarvis.hablar("Entendido. Entrando en modo reposo.")
                    jarvis.tono_reposo()
                    modo_activo = False
                    break

                # Procesamiento mediante Gemini
                try:
                    respuesta = jarvis.chat.send_message(comando)
                    if respuesta.text:
                        jarvis.hablar(respuesta.text)
                except Exception as e:
                    print(f"Error procesando comando: {e}")
                    jarvis.hablar("Tuve un inconveniente procesando esa instrucción.")

            else:
                # Cierre por inactividad de 10 segundos
                print(f"\n[Fin de la ventana de atención ({ventana_atencion_seg}s sin respuesta). Volviendo a reposo...]")
                jarvis.tono_reposo()
                modo_activo = False


# ==========================================
# 6. PUNTO DE ENTRADA
# ==========================================

if __name__ == "__main__":
    # Asegúrate de haber configurado la variable de entorno GEMINI_API_KEY o colócala aquí directamente
    API_KEY = os.getenv("GEMINI_API_KEY", "ismaoran24")

    if API_KEY == "TU_GEMINI_API_KEY_AQUI":
        print("[Error]: Configura tu clave de API de Gemini en la variable API_KEY antes de ejecutar.")
        sys.exit(1)

    jarvis_app = AsistenteJARVIS(api_key=API_KEY)
    detector_app = DetectorWakeWord(modelo="hey_jarvis")

    ejecutar_jarvis(jarvis_app, detector_app, ventana_atencion_seg=10)
