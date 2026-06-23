import discord
from discord.ext import commands
import asyncio
import os
import traceback
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
            name="24/7 Astral Security • Server Protected"
        )
    )
    print(f"✅ {bot.user} online | Installer: {INSTALLER_ID}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    cmd_name = interaction.command.name if interaction.command else "unknown"
    print(f"[ERROR] /{cmd_name}: {error}")
    traceback.print_exc()
    try:
        from utils.cv2_helper import respond_cv2, followup_cv2
        msg = [{"type": 17, "accent_color": 0xED4245, "components": [
            {"type": 10, "content": f"❌ **Error:** `{error}`"}
        ]}]
        if not interaction.response.is_done():
            await respond_cv2(interaction, msg, ephemeral=True)
        else:
            await followup_cv2(interaction, msg, ephemeral=True)
    except Exception as e:
        print(f"[ERROR HANDLER FAILED] {e}")

async def main():
    async with bot:
        await Database.init()
        for cog in COGS:
            await bot.load_extension(cog)
        keep_alive()
        await bot.start(TOKEN)

asyncio.run(main())
