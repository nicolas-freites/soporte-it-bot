# Bot de Soporte Tecnico IT Nivel 1
# Usa python-telegram-bot para la conexion con la API de Telegram
# La logica de cada paso sigue el diagrama BPMN to-be armado para el TPI

import os
import logging
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import database
from estados import (
    Estado,
    CATEGORIAS_VALIDAS,
    URGENCIAS_VALIDAS,
    obtener_sesion,
    actualizar_estado,
    guardar_dato,
    reiniciar_sesion,
)

# Cargo el token desde el archivo .env, nunca queda escrito en el codigo
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Configuro logging basico para ver que pasa en la consola mientras corre el bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ---------- FAQ basica para autoresolucion (Gateway 2 del BPMN) ----------
FAQ_RESPUESTAS = {
    "Hardware": "Proba desconectar y reconectar el dispositivo, y reiniciar el equipo.",
    "Software": "Proba cerrar y volver a abrir el programa, y revisar si hay actualizaciones pendientes.",
    "Redes": "Proba reiniciar el router y verificar que el cable o el wifi esten conectados.",
    "Accesos": "Verifica que las mayusculas (Caps Lock) esten apagadas y que el usuario este escrito correctamente.",
}


# ---------- Comando /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reiniciar_sesion(chat_id)
    actualizar_estado(chat_id, Estado.ESPERANDO_CATEGORIA)

    teclado = ReplyKeyboardMarkup(
        [[c] for c in CATEGORIAS_VALIDAS],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Hola, soy el bot de Soporte Tecnico IT.\n"
        "Para empezar, contame en que categoria entra tu problema:",
        reply_markup=teclado
    )


# ---------- Comando /cancelar ----------
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reiniciar_sesion(chat_id)
    await update.message.reply_text(
        "Consulta cancelada. Cuando quieras empezar de nuevo, escribi /start.",
        reply_markup=ReplyKeyboardRemove()
    )


# ---------- Comando /estado ----------
async def consultar_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ticket = database.obtener_ultimo_ticket(chat_id)

    if ticket is None:
        await update.message.reply_text("Todavia no generaste ningun ticket. Escribi /start para iniciar una consulta.")
        return

    ticket_id, categoria, urgencia, descripcion, estado, fecha = ticket
    await update.message.reply_text(
        f"Tu ultimo ticket (#{ticket_id}):\n"
        f"Categoria: {categoria}\n"
        f"Urgencia: {urgencia}\n"
        f"Estado actual: {estado}\n"
        f"Fecha: {fecha}"
    )


# ---------- Manejo general de mensajes de texto ----------
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto = update.message.text.strip()
    sesion = obtener_sesion(chat_id)
    estado_actual = sesion["estado"]

    # --- Paso: esperando categoria ---
    if estado_actual == Estado.ESPERANDO_CATEGORIA:
        if texto not in CATEGORIAS_VALIDAS:
            # Camino infeliz: el usuario escribio algo que no es una opcion valida
            await update.message.reply_text(
                "No reconozco esa categoria. Por favor elegi una de las opciones del teclado."
            )
            return

        guardar_dato(chat_id, "categoria", texto)
        actualizar_estado(chat_id, Estado.ESPERANDO_URGENCIA)

        teclado = ReplyKeyboardMarkup(
            [[u] for u in URGENCIAS_VALIDAS],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Entendido. Ahora decime el nivel de urgencia:",
            reply_markup=teclado
        )
        return

    # --- Paso: esperando urgencia (Gateway 1) ---
    if estado_actual == Estado.ESPERANDO_URGENCIA:
        if texto not in URGENCIAS_VALIDAS:
            await update.message.reply_text(
                "Esa urgencia no es valida. Elegi Baja, Media o Alta del teclado."
            )
            return

        guardar_dato(chat_id, "urgencia", texto)

        # Gateway 1: si la urgencia es Alta, se escala directo sin pasar por diagnostico
        if texto == "Alta":
            categoria = sesion["datos"]["categoria"]
            ticket_id = database.crear_ticket(
                chat_id, categoria, texto, "Urgencia alta, escalado directo", "escalado"
            )
            actualizar_estado(chat_id, Estado.ESCALADO)
            await update.message.reply_text(
                f"Por tratarse de urgencia ALTA, tu caso (ticket #{ticket_id}) fue derivado "
                f"directamente a un tecnico humano. Te van a contactar a la brevedad.",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # Si la urgencia es Baja o Media, sigue el flujo normal de diagnostico
        actualizar_estado(chat_id, Estado.ESPERANDO_DIAGNOSTICO)
        await update.message.reply_text(
            "Contame brevemente que estuviste intentando para solucionarlo "
            "(por ejemplo: 'ya reinicie la maquina y sigue igual').",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # --- Paso: esperando diagnostico (Gateway 2) ---
    if estado_actual == Estado.ESPERANDO_DIAGNOSTICO:
        # Camino infeliz: descripcion vacia o demasiado corta
        if len(texto) < 3:
            await update.message.reply_text(
                "Necesito un poco mas de detalle para poder ayudarte. Contame que paso."
            )
            return

        guardar_dato(chat_id, "descripcion", texto)
        categoria = sesion["datos"]["categoria"]
        urgencia = sesion["datos"]["urgencia"]

        # Gateway 2: decide si se autoresuelve con la FAQ o se escala a un tecnico
        palabras_clave_sin_solucion = ["no funciono", "no funciona", "sigue igual", "no anda"]
        necesita_escalar = any(p in texto.lower() for p in palabras_clave_sin_solucion)

        if necesita_escalar:
            ticket_id = database.crear_ticket(chat_id, categoria, urgencia, texto, "escalado")
            actualizar_estado(chat_id, Estado.ESCALADO)
            await update.message.reply_text(
                f"Ya veo que probaste alternativas sin exito. Genere el ticket #{ticket_id} "
                f"y lo derive a un tecnico humano."
            )
        else:
            respuesta_faq = FAQ_RESPUESTAS.get(categoria, "Te recomiendo reiniciar el equipo y volver a intentar.")
            ticket_id = database.crear_ticket(chat_id, categoria, urgencia, texto, "resuelto")
            actualizar_estado(chat_id, Estado.RESUELTO)
            await update.message.reply_text(
                f"Proba esto: {respuesta_faq}\n\n"
                f"Quedo registrado como ticket #{ticket_id} resuelto automaticamente. "
                f"Si el problema continua, escribi /start para generar un nuevo ticket."
            )
        return

    # --- Si el usuario escribe algo sin haber iniciado con /start ---
    await update.message.reply_text(
        "No entendi tu mensaje. Escribi /start para iniciar una consulta de soporte."
    )


# ---------- Funcion principal ----------
def main():
    database.inicializar_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("estado", consultar_estado))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("Bot corriendo... (Ctrl+C para detener)")
    app.run_polling()


if __name__ == "__main__":
    main()