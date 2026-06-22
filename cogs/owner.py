import discord
from discord.ext import commands
from discord import app_commands
from database import Database
from utils.cv2_helper import respond_cv2, no_access


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_owner(self, user_id: int) -> bool:
        return await Database.is_server_owner(str(user_id), self.bot.installer_id)

    # ── /addserverowner ───────────────────────────────────
    @app_commands.command(name="addserverowner", description="Προσθήκη Server Owner")
    @app_commands.describe(user_id="Discord User ID")
    async def addserverowner(self, interaction: discord.Interaction, user_id: str):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.add_server_owner(user_id)

        try:
            user   = await self.bot.fetch_user(int(user_id))
            name   = f"{user.mention} ({user.name})"
            avatar = str(user.display_avatar.url)
        except Exception:
            name   = f"`{user_id}`"
            avatar = None

        section = {
            "type": 9,
            "components": [{"type": 10, "content": (
                f"## 👑 Server Owner Added\n"
                f"**User:** {name}\n"
                f"**Added by:** {interaction.user.mention}"
            )}]
        }
        if avatar:
            section["accessory"] = {"type": 11, "media": {"url": avatar}}

        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [section]}
        ], ephemeral=True)

    # ── /removeserverowner ────────────────────────────────
    @app_commands.command(name="removeserverowner", description="Αφαίρεση Server Owner")
    @app_commands.describe(user_id="Discord User ID")
    async def removeserverowner(self, interaction: discord.Interaction, user_id: str):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        if str(user_id) == str(self.bot.installer_id):
            await respond_cv2(interaction, [
                {"type": 17, "accent_color": 0xED4245, "components": [
                    {"type": 10, "content": "❌ Δεν μπορείς να αφαιρέσεις τον bot installer."}
                ]}
            ], ephemeral=True)
            return

        await Database.remove_server_owner(user_id)
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0xFEE75C, "components": [
                {"type": 10, "content": (
                    f"## 👑 Server Owner Removed\n"
                    f"**ID:** `{user_id}`\n"
                    f"**Removed by:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)

    # ── /add user ─────────────────────────────────────────
    add_group = app_commands.Group(name="add", description="Προσθήκη σε λίστες")

    @add_group.command(name="user", description="Προσθήκη whitelist user (links σε whitelisted channels)")
    @app_commands.describe(member="Το μέλος")
    async def add_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.add_whitelist_user(str(member.id))

        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"## 🔗 Whitelist User Added\n"
                        f"**User:** {member.mention} ({member.name})\n"
                        f"**Added by:** {interaction.user.mention}\n\n"
                        f"⚠️ Μπορεί να στέλνει links σε whitelisted channels."
                    )}],
                    "accessory": {"type": 11, "media": {"url": str(member.display_avatar.url)}}
                }
            ]}
        ], ephemeral=True)

    # ── /remove user ──────────────────────────────────────
    remove_group = app_commands.Group(name="remove", description="Αφαίρεση από λίστες")

    @remove_group.command(name="user", description="Αφαίρεση whitelist user")
    @app_commands.describe(member="Το μέλος")
    async def remove_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.remove_whitelist_user(str(member.id))
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0xFEE75C, "components": [
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"## 🔗 Whitelist User Removed\n"
                        f"**User:** {member.mention}\n"
                        f"**Removed by:** {interaction.user.mention}"
                    )}],
                    "accessory": {"type": 11, "media": {"url": str(member.display_avatar.url)}}
                }
            ]}
        ], ephemeral=True)

    # ── /setlogchannel ────────────────────────────────────
    @app_commands.command(name="setlogchannel", description="Ορισμός channel για όλα τα logs")
    @app_commands.describe(channel="Το log channel")
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.set_setting("log_channel_id", str(channel.id))
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [
                {"type": 10, "content": (
                    f"## 📋 Log Channel Set\n"
                    f"Όλα τα logs → {channel.mention}\n"
                    f"**Set by:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
