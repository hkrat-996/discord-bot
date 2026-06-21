import discord

import os

from discord.ext import commands, tasks

from mcstatus import JavaServer



# 🔐 IMPORTANTE: usa token nuevo (NO el filtrado)

TOKEN = os.getenv("DISCORD_TOKEN")


SERVER_IP = "Rainbowmoods.aternos.me"

SERVER_PORT = 53581



intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)



channel_name = "estado-servidor"



channel_global = None

rol_jugadores = None



estado_anterior = "UNKNOWN"

fallos_consecutivos = 0

MAX_FALLOS = 3





# 📌 Crear rol decorativo

async def crear_rol(guild):

    global rol_jugadores



    rol = discord.utils.get(guild.roles, name="jugadores")



    if rol is None:

        rol = await guild.create_role(

            name="jugadores",

            mentionable=True,

            hoist=False

        )



    rol_jugadores = rol





# 📌 Crear canal de estado

async def crear_canal(guild):

    global channel_global



    existing = discord.utils.get(guild.text_channels, name=channel_name)



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





# 📡 Checar servidor

def checar_servidor():

    try:

        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")

        server.status()

        return "ON"

    except Exception:

        return "OFF"





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





# 🔁 LOOP PRINCIPAL (sin spam por cambios)

@tasks.loop(seconds=30)

async def monitoreo():

    global estado_anterior, fallos_consecutivos, channel_global



    if channel_global is None:

        return



    resultado = checar_servidor()



    # 🟢 ON

    if resultado == "ON":

        fallos_consecutivos = 0



        if estado_anterior != "ON":

            await channel_global.send("🟢 El servidor está ENCENDIDO")

            estado_anterior = "ON"



        return



    # 🔴 OFF

    if resultado == "OFF":

        fallos_consecutivos = 0



        if estado_anterior != "OFF":

            await channel_global.send("🔴 El servidor está APAGADO")

            estado_anterior = "OFF"



        return



    # ⚠️ ERROR (solo si falla varias veces seguidas)

    fallos_consecutivos += 1



    if fallos_consecutivos >= MAX_FALLOS:

        if estado_anterior != "ERROR":

            await channel_global.send(

                "⚠️ Error al verificar el servidor (timeout o fallo de conexión)"

            )

            estado_anterior = "ERROR"





bot.run(TOKEN)