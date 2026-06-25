import os
from threading import Thread

import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from flask import Flask

# =====================================
# WEB SERVER PARA RENDER
# =====================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot funcionando correctamente"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

# =====================================
# CONFIGURACIÓN
# =====================================

TOKEN = os.getenv("DISCORD_TOKEN")

SERVER_IP = "Rainbowmoods.aternos.me"
SERVER_PORT = 53581

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

channel_name = "estado-servidor"

channel_global = None
rol_jugadores = None

estado_anterior = "UNKNOWN"

# =====================================
# CREAR ROL
# =====================================

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

# =====================================
# CREAR CANAL
# =====================================

async def crear_canal(guild):
    global channel_global

    canal = discord.utils.get(
        guild.text_channels,
        name=channel_name
    )

    if canal:
        channel_global = canal
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

# =====================================
# COMPROBAR SERVIDOR
# =====================================

def checar_servidor():
    try:
        server = JavaServer.lookup(
            f"{SERVER_IP}:{SERVER_PORT}"
        )

        server.status()

        return "ON"

    except Exception:
        return "OFF"

# =====================================
# BOT LISTO
# =====================================

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

# =====================================
# MONITOREO
# =====================================

@tasks.loop(seconds=30)
async def monitoreo():
    global estado_anterior
    global channel_global
    global rol_jugadores

    if channel_global is None:
        return

    resultado = checar_servidor()

    # SERVIDOR ENCENDIDO
    if resultado == "ON":

        if estado_anterior != "ON":

            await channel_global.send(
                "🟢 El servidor está ENCENDIDO"
            )

            estado_anterior = "ON"

        return

    # SERVIDOR APAGADO
    if resultado == "OFF":

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

# =====================================
# INICIAR BOT
# =====================================

if TOKEN is None:
    raise ValueError(
        "No se encontró DISCORD_TOKEN en las variables de entorno."
    )

bot.run(TOKEN)
