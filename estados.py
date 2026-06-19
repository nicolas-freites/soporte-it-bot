# Manejo de estados de la conversacion del bot
# Cada usuario tiene un estado que indica en que paso del proceso esta

from enum import Enum


class Estado(Enum):
    # Estos estados representan los pasos del diagrama BPMN (to-be)
    INICIO = "inicio"
    ESPERANDO_CATEGORIA = "esperando_categoria"
    ESPERANDO_URGENCIA = "esperando_urgencia"
    ESPERANDO_DIAGNOSTICO = "esperando_diagnostico"
    RESUELTO = "resuelto"
    ESCALADO = "escalado"


# Opciones validas que puede elegir el usuario
CATEGORIAS_VALIDAS = ["Hardware", "Software", "Redes", "Accesos"]
URGENCIAS_VALIDAS = ["Baja", "Media", "Alta"]


# Guarda el estado actual de cada usuario mientras el bot esta corriendo
# La clave es el chat_id de Telegram de cada usuario
sesiones_usuarios = {}


def obtener_sesion(chat_id: int) -> dict:
    # Si el usuario no tiene sesion todavia, se la creo en estado inicial
    if chat_id not in sesiones_usuarios:
        sesiones_usuarios[chat_id] = {
            "estado": Estado.INICIO,
            "datos": {}
        }
    return sesiones_usuarios[chat_id]


def actualizar_estado(chat_id: int, nuevo_estado: Estado) -> None:
    sesion = obtener_sesion(chat_id)
    sesion["estado"] = nuevo_estado


def guardar_dato(chat_id: int, clave: str, valor) -> None:
    # Guardo datos temporales mientras dura la conversacion (categoria, urgencia, etc)
    sesion = obtener_sesion(chat_id)
    sesion["datos"][clave] = valor


def reiniciar_sesion(chat_id: int) -> None:
    # Se usa cuando el usuario manda /start o /cancelar
    sesiones_usuarios[chat_id] = {
        "estado": Estado.INICIO,
        "datos": {}
    }