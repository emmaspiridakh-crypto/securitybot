import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from database import Database
from keep_alive import keep_alive

load_dotenv()

TOKEN        = os.getenv("TOKEN")
INSTALLER_ID = os.getenv("INSTALLER_ID")

if not TOKEN:
    print("❌ TOKEN missing from .env"); exit(1)
if not INSTALLER_ID:
    print("❌ INSTALLER_ID missing from .env"); exit(1)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="§", intents=intents)
bot.installer_id = INSTALLER_ID

COGS = [
    "cogs.panel",
    "cogs.owner",
    "cogs.whitelist_cmd",
    "cogs.config_cmd",
    "cogs.antinuke",
    "cogs.automod",
]

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🔒 Server Security"
        )
    )
    print(f"✅ {bot.user} online | Installer: {INSTALLER_ID}")

async def main():
    async with bot:
        await Database.init()
        for cog in COGS:
            await bot.load_extension(cog)
        keep_alive()
        await bot.start(TOKEN)

asyncio.run(main())
