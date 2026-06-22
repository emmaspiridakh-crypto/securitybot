import discord
from discord.ext import commands
from discord import app_commands
from database import Database
from utils.cv2_helper import respond_cv2, no_access


class WhitelistCmd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_owner(self, user_id: int) -> bool:
        return await Database.is_server_owner(str(user_id), self.bot.installer_id)

    # ── /whitelist ────────────────────────────────────────
    whitelist_group   = app_commands.Group(name="whitelist",   description="Whitelist management")
    unwhitelist_group = app_commands.Group(name="unwhitelist", description="Unwhitelist management")

    @whitelist_group.command(name="channel", description="Whitelist channel — links επιτρέπονται από WL users")
    @app_commands.describe(channel="Το channel")
    async def whitelist_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.add_whitelist_channel(str(channel.id))
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [
                {"type": 10, "content": (
                    f"## 📢 Channel Whitelisted\n"
                    f"{channel.mention} — Whitelist users μπορούν να στέλνουν links εδώ.\n"
                    f"**Set by:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)

    @whitelist_group.command(name="bot", description="Whitelist bot — skip verification")
    @app_commands.describe(bot_id="Bot ID")
    async def whitelist_bot(self, interaction: discord.Interaction, bot_id: str):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.add_whitelist_bot(bot_id)
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [
                {"type": 10, "content": (
                    f"## 🤖 Bot Whitelisted\n"
                    f"Bot `{bot_id}` δεν θα χρειαστεί verification.\n"
                    f"**Set by:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)

    @whitelist_group.command(name="list", description="Λίστα όλων των whitelisted")
    async def whitelist_list(self, interaction: discord.Interaction):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        owners   = await Database.get_server_owners()
        wl_users = await Database.get_whitelist_users()
        wl_bots  = await Database.get_whitelist_bots()
        wl_chs   = await Database.get_whitelist_channels()

        def fmt_users(ids):    return "\n".join(f"• <@{i}>" for i in ids)    or "*Κανένας*"
        def fmt_bots(ids):     return "\n".join(f"• `{i}`"  for i in ids)    or "*Κανένας*"
        def fmt_channels(ids): return "\n".join(f"• <#{i}>" for i in ids)    or "*Κανένα*"

        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x5865F2, "components": [
                {"type": 10, "content": "## 📋 Whitelist Overview"},
                {"type": 14},
                {"type": 9, "components": [{"type": 10, "content": f"**👑 Server Owners**\n{fmt_users(owners)}"}]},
                {"type": 14},
                {"type": 9, "components": [{"type": 10, "content": f"**🔗 Link Whitelist Users**\n{fmt_users(wl_users)}"}]},
                {"type": 14},
                {"type": 9, "components": [{"type": 10, "content": f"**📢 Whitelisted Channels**\n{fmt_channels(wl_chs)}"}]},
                {"type": 14},
                {"type": 9, "components": [{"type": 10, "content": f"**🤖 Whitelisted Bots**\n{fmt_bots(wl_bots)}"}]},
            ]}
        ], ephemeral=True)

    # ── /unwhitelist ──────────────────────────────────────
    @unwhitelist_group.command(name="channel", description="Αφαίρεση channel από whitelist")
    @app_commands.describe(channel="Το channel")
    async def unwhitelist_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.remove_whitelist_channel(str(channel.id))
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0xFEE75C, "components": [
                {"type": 10, "content": (
                    f"## 📢 Channel Removed\n"
                    f"{channel.mention} δεν επιτρέπει πλέον links.\n"
                    f"**By:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)

    @unwhitelist_group.command(name="bot", description="Αφαίρεση bot από whitelist")
    @app_commands.describe(bot_id="Bot ID")
    async def unwhitelist_bot(self, interaction: discord.Interaction, bot_id: str):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        await Database.remove_whitelist_bot(bot_id)
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0xFEE75C, "components": [
                {"type": 10, "content": (
                    f"## 🤖 Bot Removed\n"
                    f"Bot `{bot_id}` θα χρειάζεται verification.\n"
                    f"**By:** {interaction.user.mention}"
                )}
            ]}
        ], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(WhitelistCmd(bot))
