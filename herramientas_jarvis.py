import ctypes
import json
import os
import platform

TAREAS_FILE = "tareas.json"

# ==========================================
# 1. CONTROL DE VOLUMEN Y MULTIMEDIA (NATIVO)
# ==========================================

# Códigos Virtual Keys de Windows para Hardware / Teclas Multimedia
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

def _enviar_tecla(codigo_vk: int):
    """Genera el evento de pulsación de tecla virtual del sistema operativo."""
    if platform.system() == "Windows":
        ctypes.windll.user32.keybd_event(codigo_vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(codigo_vk, 0, 2, 0)

def controlar_volumen(accion: str, repeticiones: int = 5) -> str:
    """
    Controla el volumen del sistema operativo.
    :param accion: 'subir', 'bajar' o 'silenciar'/'mutear'.
    :param repeticiones: Número de saltos de volumen a aplicar (por defecto 5).
    """
    accion = accion.lower()
    if any(k in accion for k in ["subir", "mas", "aumentar"]):
        for _ in range(repeticiones):
            _enviar_tecla(VK_VOLUME_UP)
        return f"Volumen aumentado."
    elif any(k in accion for k in ["bajar", "menos", "reducir"]):
        for _ in range(repeticiones):
            _enviar_tecla(VK_VOLUME_DOWN)
        return f"Volumen reducido."
    elif any(k in accion for k in ["silenciar", "mutear", "mute", "silencio"]):
        _enviar_tecla(VK_VOLUME_MUTE)
        return "Volumen silenciado o restaurado."
    else:
        return "Acción de volumen no reconocida. Utiliza subir, bajar o silenciar."

def controlar_reproduccion(accion: str) -> str:
    """
    Controla la reproducción multimedia activa en el sistema (Spotify, YouTube, reproductores locales).
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
    else:
        return "Comando multimedia no reconocido."


# ==========================================
# 2. GESTOR PERSISTENTE DE TAREAS Y RECORDATORIOS
# ==========================================

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
    """
    Guarda una nueva tarea o recordatorio en la lista de pendientes de JARVIS.
    :param descripcion: El texto o detalle de la tarea a guardar.
    """
    tareas = _cargar_tareas()
    nueva_tarea = {
        "id": len(tareas) + 1,
        "descripcion": descripcion,
        "completada": False
    }
    tareas.append(nueva_tarea)
    _guardar_tareas(tareas)
    return f"Tarea agregada a la lista: '{descripcion}'."

def listar_tareas_pendientes() -> str:
    """
    Consulta y lista todas las tareas pendientes no completadas.
    """
    tareas = _cargar_tareas()
    pendientes = [t for t in tareas if not t.get("completada", False)]
    if not pendientes:
        return "No tiene tareas pendientes en este momento, señor."
    
    lineas = [f"Tarea {t['id']}: {t['descripcion']}" for t in pendientes]
    return "Sus tareas pendientes son:\n" + "\n".join(lineas)

def completar_tarea(numero_tarea: int) -> str:
    """
    Marca una tarea específica como realizada utilizando su número identificador.
    :param numero_tarea: Número identificador de la tarea a marcar como completada.
    """
    tareas = _cargar_tareas()
    for t in tareas:
        if t["id"] == numero_tarea:
            if t["completada"]:
                return f"La tarea número {numero_tarea} ya figuraba como realizada."
            t["completada"] = True
            _guardar_tareas(tareas)
            return f"Tarea {numero_tarea} ('{t['descripcion']}') marcada como realizada."
    return f"No se encontró la tarea con el id {numero_tarea}."