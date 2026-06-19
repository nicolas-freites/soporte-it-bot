# Bot de Soporte Tecnico IT - Nivel 1

Bot de Telegram que automatiza el proceso de soporte tecnico nivel 1, desarrollado como Trabajo Practico Integrador de la materia Organizacion Empresarial (TUPaD - UTN).

## Descripcion del proyecto

El bot simula la atencion de un area de soporte tecnico de IT, clasificando el problema del usuario por categoria y urgencia, intentando una autoresolucion mediante FAQ, y escalando a un tecnico humano cuando corresponde. La logica del bot esta basada en un diagrama BPMN 2.0 (ver carpeta de documentacion del TPI).

## Tecnologias utilizadas

- Python 3
- python-telegram-bot (API de Telegram)
- SQLite (persistencia de tickets)
- python-dotenv (manejo seguro del token)

## Estructura del proyecto

soporte-it-bot/
- bot.py: Logica principal y handlers de Telegram
- database.py: Conexion y operaciones sobre SQLite
- estados.py: Maquina de estados de la conversacion
- requirements.txt: Dependencias del proyecto
- .env.example: Ejemplo de archivo de configuracion (sin token real)
- .gitignore
- README.md

## Como desplegarlo

### 1. Clonar el repositorio

git clone URL-del-repositorio
cd soporte-it-bot

### 2. Crear y activar un entorno virtual

En Windows:
python -m venv venv
venv\Scripts\activate

### 3. Instalar dependencias

pip install -r requirements.txt

### 4. Configurar el token de Telegram

Crear un bot propio hablando con @BotFather en Telegram y obtener un token.

Crear un archivo .env en la raiz del proyecto (tomando como referencia .env.example) con el siguiente contenido:

TELEGRAM_TOKEN=tu_token_aqui

### 5. Ejecutar el bot

python bot.py

Si todo esta correcto, la consola va a mostrar el mensaje "Bot corriendo...". A partir de ahi, el bot queda activo y se puede interactuar con el desde Telegram.

## Comandos disponibles

| Comando | Funcion |
|---|---|
| /start | Inicia una nueva consulta de soporte |
| /estado | Consulta el estado del ultimo ticket generado |
| /cancelar | Cancela la consulta en curso |

## Maquina de estados

El bot mantiene en memoria el estado de cada usuario para saber en que paso de la conversacion se encuentra:

- INICIO
- ESPERANDO_CATEGORIA
- ESPERANDO_URGENCIA
- ESPERANDO_DIAGNOSTICO
- RESUELTO
- ESCALADO

## Persistencia

Los tickets generados se almacenan en una base de datos SQLite (soporte_it.db), que se crea automaticamente al ejecutar el bot por primera vez. Cada ticket guarda: categoria, urgencia, descripcion del problema, estado y fecha de creacion.

## Autores

- Nicolas Freites
- Santiago Torres

Tecnicatura Universitaria en Programacion a Distancia (TUPaD) - UTN