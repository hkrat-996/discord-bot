import os
from threading import Thread

import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from flask import Flask

# =========================
# WEB SERVER PARA RENDER
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de Discord funcionando"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

web_thread = Thread(target=run_web)
web_thread.daemon = True
web_thread.start()

# =========================
# CONFIGURACIÓN DEL BOT
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SERVER_IP = "Rainbowmoods.aternos.me"
SERVER_PORT = 53581

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

channel_name = "estado-servidor"

channel_global = None
rol_jugadores = None

estado_anterior = "UNKNOWN"

fallos_consecutivos = 0
MAX_FALLOS = 3

# =========================
# CREAR ROL
# =========================

async def crear_rol(guild):
    global rol_jugadores

    rol = discord.utils.get(
        guild.roles,
        name="jugadores"
    )

    if rol is None:
        rol = await guild.create_role(
            name="jugadores",
            mentionable=True,
            hoist=False
        )

    rol_jugadores = rol

# =========================
# CREAR CANAL
# =========================

async def crear_canal(guild):
    global channel_global

    existing = discord.utils.get(
        guild.text_channels,
        name=channel_name
    )

    if existing:
        channel_global = existing
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            send_messages=False,
            read_messages=True
        )
    }

    channel_global = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites
    )

# =========================
# COMPROBAR SERVIDOR
# =========================

def checar_servidor():
    try:
        server = JavaServer.lookup(
            f"{SERVER_IP}:{SERVER_PORT}"
        )

        server.status()

        return "ON"

    except TimeoutError:
        return "ERROR"

    except ConnectionError:
        return "ERROR"

    except Exception:
        return "OFF"

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    global estado_anterior

    print(f"Conectado como {bot.user}")

    for guild in bot.guilds:
        await crear_rol(guild)
        await crear_canal(guild)

    estado_anterior = "UNKNOWN"

    if not monitoreo.is_running():
        monitoreo.start()

# =========================
# MONITOREO
# =========================

@tasks.loop(seconds=30)
async def monitoreo():
    global (
        estado_anterior,
        fallos_consecutivos,
        channel_global,
        rol_jugadores
    )

    if channel_global is None:
        return

    resultado = checar_servidor()

    # =====================
    # ONLINE
    # =====================

    if resultado == "ON":

        fallos_consecutivos = 0

        if estado_anterior != "ON":

            await channel_global.send(
                "🟢 El servidor está ENCENDIDO"
            )

            estado_anterior = "ON"

        return

    # =====================
    # OFFLINE
    # =====================

    if resultado == "OFF":

        fallos_consecutivos = 0

        if estado_anterior != "OFF":

            if rol_jugadores:
                await channel_global.send(
                    f"{rol_jugadores.mention}\n🔴 El servidor está APAGADO"
                )
            else:
                await channel_global.send(
                    "🔴 El servidor está APAGADO"
                )

            estado_anterior = "OFF"

        return

    # =====================
    # ERROR
    # =====================

    if resultado == "ERROR":

        fallos_consecutivos += 1

        if fallos_consecutivos >= MAX_FALLOS:

            if estado_anterior != "ERROR":

                await channel_global.send(
                    "⚠️ Error al verificar el servidor (timeout o fallo de conexión)"
                )

                estado_anterior = "ERROR"

        return

# =========================
# INICIAR BOT
# =========================

bot.run(TOKEN)
