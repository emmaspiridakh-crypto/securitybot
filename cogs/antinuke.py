import asyncio
import datetime

import discord
from discord.ext import commands

from database import Database
from utils.cv2_helper import send_cv2
from utils.tracker import ban_tracker, kick_tracker, channel_del_tracker


class AntiNuke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _log_channel_id(self) -> int | None:
        val = await Database.get_setting("log_channel_id")
        return int(val) if val else None

    async def _send_log(self, components: list):
        cid = await self._log_channel_id()
        if cid:
            await send_cv2(cid, components)

    # ── Punish + Lockdown ─────────────────────────────────
    async def _punish(self, guild: discord.Guild, moderator: discord.Member, reason: str):
        """Timeout the offender for 1 week + lockdown all channels."""

        # Skip whitelisted / server owners
        if await Database.is_server_owner(str(moderator.id), self.bot.installer_id):
            return

        # 1-week timeout
        try:
            await moderator.timeout(datetime.timedelta(weeks=1), reason=reason)
        except Exception as e:
            print(f"[AntiNuke] timeout failed: {e}")

        # Lockdown all channels concurrently
        tasks = []
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                ow = channel.overwrites_for(guild.default_role)
                ow.send_messages = False
                ow.connect       = False
                tasks.append(
                    channel.set_permissions(
                        guild.default_role, overwrite=ow,
                        reason="Anti-Nuke Auto-Lockdown"
                    )
                )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        locked  = sum(1 for r in results if not isinstance(r, Exception))

        await Database.log_event("mass_action", {
            "user":   str(moderator),
            "id":     str(moderator.id),
            "reason": reason,
            "locked": locked
        })

        await self._send_log([
            {
                "type": 17,
                "accent_color": 0x8B0000,
                "components": [
                    {
                        "type": 9,
                        "components": [
                            {"type": 10, "content": (
                                f"#  ANTI-NUKE TRIGGERED\n"
                                f"**> Moderator:** {moderator.mention} (`{moderator.id}`)\n"
                                f"**> Trigger:** {reason}\n"
                                f"**> Action:** 1 week timeout\n"
                                f"**> Lockdown:** {locked}/{len(tasks)} channels locked"
                            )}
                        ],
                        "accessory": {
                            "type": 11,
                            "media": {"url": str(moderator.display_avatar.url)}
                        }
                    }
                ]
            }
        ])

    # ── Mass Ban ──────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if not await Database.is_module_enabled("mass_action"):
            return

        await asyncio.sleep(0.5)

        try:
            entries = [e async for e in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )]
        except Exception:
            return

        if not entries:
            return

        moderator = entries[0].user
        if moderator.bot:
            return
        if await Database.is_server_owner(str(moderator.id), self.bot.installer_id):
            return

        limit  = int(await Database.get_config("mass_action_limit",  "3"))
        window = int(await Database.get_config("mass_action_window", "10"))
        key    = f"ban_{guild.id}_{moderator.id}"

        if ban_tracker.add_and_check(key, limit, window):
            ban_tracker.reset(key)
            member = guild.get_member(moderator.id)
            if member:
                await self._punish(guild, member, f"Mass Ban ({limit}/{window}s)")

    # ── Mass Kick ─────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not await Database.is_module_enabled("mass_action"):
            return

        guild = member.guild
        await asyncio.sleep(0.5)

        try:
            entries = [e async for e in guild.audit_logs(
                limit=3, action=discord.AuditLogAction.kick
            )]
        except Exception:
            return

        for entry in entries:
            if (
                entry.target
                and entry.target.id == member.id
                and (discord.utils.utcnow() - entry.created_at).total_seconds() < 5
            ):
                moderator = entry.user
                if moderator.bot:
                    return
                if await Database.is_server_owner(str(moderator.id), self.bot.installer_id):
                    return

                limit  = int(await Database.get_config("mass_action_limit",  "3"))
                window = int(await Database.get_config("mass_action_window", "10"))
                key    = f"kick_{guild.id}_{moderator.id}"

                if kick_tracker.add_and_check(key, limit, window):
                    kick_tracker.reset(key)
                    mod_member = guild.get_member(moderator.id)
                    if mod_member:
                        await self._punish(guild, mod_member, f"Mass Kick ({limit}/{window}s)")
                break

    # ── Mass Channel Delete ───────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if not await Database.is_module_enabled("mass_action"):
            return

        guild = channel.guild
        await asyncio.sleep(0.5)

        try:
            entries = [e async for e in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.channel_delete
            )]
        except Exception:
            return

        if not entries:
            return

        moderator = entries[0].user
        if moderator.bot:
            return
        if await Database.is_server_owner(str(moderator.id), self.bot.installer_id):
            return

        limit  = int(await Database.get_config("mass_action_limit",  "3"))
        window = int(await Database.get_config("mass_action_window", "10"))
        key    = f"ch_del_{guild.id}_{moderator.id}"

        if channel_del_tracker.add_and_check(key, limit, window):
            channel_del_tracker.reset(key)
            await Database.log_event("channel_delete", {
                "user":    str(moderator),
                "channel": channel.name
            })
            member = guild.get_member(moderator.id)
            if member:
                await self._punish(guild, member, f"Mass Channel Delete ({limit}/{window}s)")


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))
