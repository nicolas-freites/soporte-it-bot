# Conexion y manejo de la base de datos SQLite
# Acá se guardan los tickets que va generando el bot

import sqlite3
from datetime import datetime

NOMBRE_DB = "soporte_it.db"


def conectar():
    return sqlite3.connect(NOMBRE_DB)


def inicializar_db():
    # Crea la tabla tickets si todavia no existe, se llama una vez al arrancar
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            categoria TEXT,
            urgencia TEXT,
            descripcion TEXT,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()


def crear_ticket(chat_id: int, categoria: str, urgencia: str, descripcion: str, estado: str) -> int:
    # Inserta un ticket nuevo y devuelve el id que le asigno la base
    conexion = conectar()
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO tickets (chat_id, categoria, urgencia, descripcion, estado, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (chat_id, categoria, urgencia, descripcion, estado, fecha_actual))
    conexion.commit()
    ticket_id = cursor.lastrowid
    conexion.close()
    return ticket_id


def actualizar_estado_ticket(ticket_id: int, nuevo_estado: str) -> None:
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE tickets SET estado = ? WHERE id = ?
    """, (nuevo_estado, ticket_id))
    conexion.commit()
    conexion.close()


def obtener_ultimo_ticket(chat_id: int):
    # Devuelve el ticket mas reciente de un usuario, para el comando /estado
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, categoria, urgencia, descripcion, estado, fecha_creacion
        FROM tickets
        WHERE chat_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (chat_id,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def obtener_todos_los_tickets():
    # Devuelve todos los tickets, sirve para revisar la base en las pruebas
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
    filas = cursor.fetchall()
    conexion.close()
    return filas