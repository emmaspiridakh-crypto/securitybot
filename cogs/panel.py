import discord
from discord.ext import commands
from discord import app_commands
from database import Database
from utils.cv2_helper import respond_cv2, update_cv2, send_cv2, no_access


# ── Component builders ─────────────────────────────────────────────────────────

def _on(key, disabled):  return key not in disabled
def _icon(key, disabled): return "✅" if _on(key, disabled) else "❌"
def _style(key, disabled): return 3 if _on(key, disabled) else 4  # green / red


def build_panel(cfg: dict, disabled: list, guild_icon: str | None) -> list:
    alt_action  = cfg.get("alt_action",         "kick")
    alt_days    = cfg.get("alt_age_days",        "30")
    spam_thr    = cfg.get("spam_threshold",      "5")
    spam_win    = cfg.get("spam_window_secs",    "5")
    spam_to     = cfg.get("spam_timeout_mins",   "10")
    link_to     = cfg.get("link_timeout_mins",   "60")
    mass_lim    = cfg.get("mass_action_limit",   "3")
    mass_win    = cfg.get("mass_action_window",  "10")

    header_section = {
        "type": 9,
        "components": [
            {"type": 10, "content": "# Security Control Panel."}
        ],
    }
    if guild_icon:
        header_section["accessory"] = {"type": 11, "media": {"url": guild_icon}}

    return [
        {
            "type": 17,
            "accent_color": 0x8B0000,
            "components": [
                header_section,
                {"type": 14},

                # ALT
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('alt', disabled)} **🛡️ ALT Detection**\n"
                        f"Threshold: **{alt_days} days** | Action: **{alt_action.capitalize()}**"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle ALT",
                        "style": _style("alt", disabled), "custom_id": "sec_toggle_alt"
                    }
                },

                # LINKS
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('link', disabled)} **🔗 Link Filter**\n"
                        f"Timeout: **{link_to} min**"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle Links",
                        "style": _style("link", disabled), "custom_id": "sec_toggle_link"
                    }
                },

                # TOKENS
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('token', disabled)} **🔑 Token Filter**\n"
                        f"Auto-delete Discord tokens"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle Tokens",
                        "style": _style("token", disabled), "custom_id": "sec_toggle_token"
                    }
                },

                # SPAM
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('spam', disabled)} **🚫 Spam Filter**\n"
                        f"{spam_thr} msgs / {spam_win}s → **{spam_to} min timeout**"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle Spam",
                        "style": _style("spam", disabled), "custom_id": "sec_toggle_spam"
                    }
                },

                # MASS ACTION
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('mass_action', disabled)} **⚡ Mass Action Guard**\n"
                        f"{mass_lim} actions / {mass_win}s → auto-lockdown"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle Mass Action",
                        "style": _style("mass_action", disabled), "custom_id": "sec_toggle_mass"
                    }
                },

                # BOT VERIFY
                {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"{_icon('bot_verify', disabled)} **🤖 Bot Verification**\n"
                        f"Zero permissions until accept"
                    )}],
                    "accessory": {
                        "type": 2, "label": "Toggle Bot Verify",
                        "style": _style("bot_verify", disabled), "custom_id": "sec_toggle_botverify"
                    }
                },

                {"type": 14},

                # Bottom action row
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": f"ALT Action: {alt_action.capitalize()}",
                            "style": 3 if alt_action == "kick" else 2,
                            "custom_id": "sec_toggle_altkick"
                        },
                        {"type": 2, "label": "📊 Status",       "style": 1, "custom_id": "sec_status"},
                        {"type": 2, "label": "📋 Recent Logs",  "style": 2, "custom_id": "sec_logs_btn"}
                    ]
                }
            ]
        }
    ]


def build_status(cfg: dict, disabled: list, wl_u: int, wl_b: int, wl_c: int, guild_icon: str | None) -> list:
    def ic(k): return "✅" if k not in disabled else "❌"

    header = {
        "type": 9,
        "components": [{"type": 10, "content": "## 📊 Security Status"}],
    }
    if guild_icon:
        header["accessory"] = {"type": 11, "media": {"url": guild_icon}}

    return [
        {
            "type": 17,
            "accent_color": 0x5865F2,
            "components": [
                header,
                {"type": 14},
                {"type": 10, "content": (
                    f"{ic('alt')} **ALT** · {ic('link')} **Links** · "
                    f"{ic('token')} **Tokens** · {ic('spam')} **Spam** · "
                    f"{ic('mass_action')} **Mass Action** · {ic('bot_verify')} **Bot Verify**"
                )},
                {"type": 14},
                {"type": 10, "content": (
                    f"**📅 Alt threshold:** {cfg.get('alt_age_days','30')} days | "
                    f"**Action:** {cfg.get('alt_action','kick').capitalize()}\n"
                    f"**🚫 Spam:** {cfg.get('spam_threshold','5')} msgs / "
                    f"{cfg.get('spam_window_secs','5')}s → "
                    f"{cfg.get('spam_timeout_mins','10')} min timeout\n"
                    f"**🔗 Link timeout:** {cfg.get('link_timeout_mins','60')} min\n"
                    f"**⚡ Mass action:** {cfg.get('mass_action_limit','3')} actions / "
                    f"{cfg.get('mass_action_window','10')}s\n"
                    f"**👥 WL Users:** {wl_u} · **🤖 WL Bots:** {wl_b} · **📢 WL Channels:** {wl_c}"
                )}
            ]
        }
    ]


def build_logs(events: list, guild_icon: str | None) -> list:
    EMOJI = {
        "token_detected":  "🔑",
        "link_detected":   "🔗",
        "spam_detected":   "🚫",
        "alt_detected":    "🚨",
        "bot_join":        "🤖",
        "mass_action":     "⚡",
        "channel_delete":  "🗑️",
        "lockdown":        "🔒",
    }

    if not events:
        body = "*Δεν υπάρχουν security events ακόμα.*"
    else:
        lines = []
        for e in events:
            who = e["data"].get("user") or e["data"].get("bot") or "?"
            ts  = e["timestamp"] // 1000
            lines.append(
                f"{EMOJI.get(e['type'], '📌')} **{e['type']}** — `{who}` <t:{ts}:R>"
            )
        body = "\n".join(lines)

    header = {
        "type": 9,
        "components": [{"type": 10, "content": "## 📋 Recent Security Events"}],
    }
    if guild_icon:
        header["accessory"] = {"type": 11, "media": {"url": guild_icon}}

    return [
        {
            "type": 17,
            "accent_color": 0x8B0000,
            "components": [header, {"type": 14}, {"type": 10, "content": body}]
        }
    ]


def build_help(is_owner: bool) -> list:
    sections = [{"type": 10, "content": "# 🔒 Security Bot — Help"}, {"type": 14}]

    if is_owner:
        sections.append({
            "type": 9,
            "components": [{"type": 10, "content": (
                "**👑 Owner Commands**\n"
                "`/addserverowner <id>` — Προσθήκη Server Owner\n"
                "`/removeserverowner <id>` — Αφαίρεση Server Owner\n"
                "`/add user @user` — Προσθήκη whitelist user\n"
                "`/remove user @user` — Αφαίρεση whitelist user"
            )}]
        })
        sections.append({"type": 14})

    sections += [
        {
            "type": 9,
            "components": [{"type": 10, "content": (
                "**⚙️ Config** *(Owner only)*\n"
                "`/config` — Όλες οι ρυθμίσεις\n"
                "`/config <key> <value>` — Αλλαγή ρύθμισης"
            )}]
        },
        {"type": 14},
        {
            "type": 9,
            "components": [{"type": 10, "content": (
                "**🔗 Whitelist** *(Owner only)*\n"
                "`/whitelist channel #ch` — Whitelist channel για links\n"
                "`/whitelist bot <id>` — Skip verification για bot\n"
                "`/whitelist list` — Λίστα όλων\n"
                "`/unwhitelist channel #ch` — Αφαίρεση channel\n"
                "`/unwhitelist bot <id>` — Αφαίρεση bot"
            )}]
        },
        {"type": 14},
        {
            "type": 9,
            "components": [{"type": 10, "content": (
                "**📊 Panel & Logs** *(Owner only)*\n"
                "`/panel` — Security Control Panel\n"
                "`/status` — Γρήγορη επισκόπηση\n"
                "`/logs [amount]` — Τελευταία events\n"
                "`/setlogchannel #channel` — Ορισμός log channel\n"
                "`/sechelp` — Αυτό το μήνυμα"
            )}]
        }
    ]

    return [{"type": 17, "accent_color": 0x5865F2, "components": sections}]


# ── Cog ────────────────────────────────────────────────────────────────────────

class Panel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_owner(self, user_id: int) -> bool:
        return await Database.is_server_owner(str(user_id), self.bot.installer_id)

    def _guild_icon(self, guild: discord.Guild) -> str | None:
        return str(guild.icon.url) if guild and guild.icon else None

    # ── /panel ────────────────────────────────────────────
    @app_commands.command(name="panel", description="Security Control Panel")
    async def panel(self, interaction: discord.Interaction):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        cfg      = await Database.get_all_config()
        disabled = await Database.get_disabled_modules()
        icon     = self._guild_icon(interaction.guild)
        components = build_panel(cfg, disabled, icon)

        await respond_cv2(interaction, components, ephemeral=False)

    # ── /status ───────────────────────────────────────────
    @app_commands.command(name="status", description="Security status overview")
    async def status(self, interaction: discord.Interaction):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        cfg      = await Database.get_all_config()
        disabled = await Database.get_disabled_modules()
        icon     = self._guild_icon(interaction.guild)
        wl_u     = len(await Database.get_whitelist_users())
        wl_b     = len(await Database.get_whitelist_bots())
        wl_c     = len(await Database.get_whitelist_channels())
        await respond_cv2(interaction, build_status(cfg, disabled, wl_u, wl_b, wl_c, icon), ephemeral=True)

    # ── /logs ─────────────────────────────────────────────
    @app_commands.command(name="logs", description="Recent security events")
    @app_commands.describe(amount="Number of events (1-20, default 10)")
    async def logs(self, interaction: discord.Interaction, amount: int = 10):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        amount = min(max(amount, 1), 20)
        events = await Database.get_recent_events(amount)
        icon   = self._guild_icon(interaction.guild)
        await respond_cv2(interaction, build_logs(events, icon), ephemeral=True)

    # ── /sechelp ──────────────────────────────────────────
    @app_commands.command(name="sechelp", description="Όλες οι εντολές του security bot")
    async def sechelp(self, interaction: discord.Interaction):
        is_owner = await self._is_owner(interaction.user.id)
        is_wl    = await Database.is_whitelist_user(str(interaction.user.id))
        if not is_owner and not is_wl:
            await no_access(interaction)
            return
        await respond_cv2(interaction, build_help(is_owner), ephemeral=True)

    # ── Button interactions ───────────────────────────────
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        cid = interaction.data.get("custom_id", "")

        # ── Bot Accept / Deny ──────────────────────────────
        if cid.startswith("bot_accept_") or cid.startswith("bot_deny_"):
            is_owner = await self._is_owner(interaction.user.id)
            is_admin = interaction.user.guild_permissions.administrator
            if not is_owner and not is_admin:
                await respond_cv2(interaction, [
                    {"type": 17, "accent_color": 0xED4245, "components": [
                        {"type": 10, "content": "🔒 **No Access** — Administrators only."}
                    ]}
                ], ephemeral=True)
                return

            bot_id     = cid.replace("bot_accept_", "").replace("bot_deny_", "")
            bot_member = interaction.guild.get_member(int(bot_id))

            if cid.startswith("bot_accept_"):
                # Remove zero-permission overwrites
                if bot_member:
                    import asyncio
                    tasks = [
                        ch.set_permissions(bot_member, overwrite=None, reason="Bot accepted")
                        for ch in interaction.guild.channels
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)

                name    = bot_member.name if bot_member else bot_id
                avatar  = str(bot_member.display_avatar.url) if bot_member else None
                section = {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"## ✅ Bot Accepted\n"
                        f"**{name}** γίνεται δεκτό.\n"
                        f"**Accepted by:** {interaction.user.mention}"
                    )}]
                }
                if avatar:
                    section["accessory"] = {"type": 11, "media": {"url": avatar}}

                await update_cv2(interaction, [
                    {"type": 17, "accent_color": 0x57F287, "components": [section]}
                ])

            else:  # deny
                kicked = False
                name   = bot_member.name if bot_member else bot_id
                avatar = str(bot_member.display_avatar.url) if bot_member else None
                if bot_member:
                    try:
                        await bot_member.kick(reason=f"Bot denied by {interaction.user}")
                        kicked = True
                    except Exception:
                        pass

                section = {
                    "type": 9,
                    "components": [{"type": 10, "content": (
                        f"## ❌ Bot Denied\n"
                        f"**{name}** απορρίφθηκε.\n"
                        f"**Denied by:** {interaction.user.mention}\n"
                        f"**Kicked:** {'✅' if kicked else '❌'}"
                    )}]
                }
                if avatar:
                    section["accessory"] = {"type": 11, "media": {"url": avatar}}

                await update_cv2(interaction, [
                    {"type": 17, "accent_color": 0xED4245, "components": [section]}
                ])
            return

        # ── Panel buttons — owner only ─────────────────────
        if not await self._is_owner(interaction.user.id):
            await respond_cv2(interaction, [
                {"type": 17, "accent_color": 0xED4245, "components": [
                    {"type": 10, "content": "🔒 **No Access** — Μόνο Server Owners μπορούν να χρησιμοποιήσουν τα κουμπιά."}
                ]}
            ], ephemeral=True)
            return

        TOGGLE_MAP = {
            "sec_toggle_alt":       "alt",
            "sec_toggle_link":      "link",
            "sec_toggle_token":     "token",
            "sec_toggle_spam":      "spam",
            "sec_toggle_mass":      "mass_action",
            "sec_toggle_botverify": "bot_verify",
        }

        if cid in TOGGLE_MAP:
            module  = TOGGLE_MAP[cid]
            enabled = await Database.is_module_enabled(module)
            if enabled:
                await Database.disable_module(module)
            else:
                await Database.enable_module(module)

            cfg      = await Database.get_all_config()
            disabled = await Database.get_disabled_modules()
            icon     = self._guild_icon(interaction.guild)
            await update_cv2(interaction, build_panel(cfg, disabled, icon))
            return

        if cid == "sec_toggle_altkick":
            current = await Database.get_config("alt_action", "kick")
            await Database.set_config("alt_action", "log" if current == "kick" else "kick")
            cfg      = await Database.get_all_config()
            disabled = await Database.get_disabled_modules()
            icon     = self._guild_icon(interaction.guild)
            await update_cv2(interaction, build_panel(cfg, disabled, icon))
            return

        if cid == "sec_status":
            cfg      = await Database.get_all_config()
            disabled = await Database.get_disabled_modules()
            icon     = self._guild_icon(interaction.guild)
            wl_u     = len(await Database.get_whitelist_users())
            wl_b     = len(await Database.get_whitelist_bots())
            wl_c     = len(await Database.get_whitelist_channels())
            await respond_cv2(interaction, build_status(cfg, disabled, wl_u, wl_b, wl_c, icon), ephemeral=True)
            return

        if cid == "sec_logs_btn":
            events = await Database.get_recent_events(10)
            icon   = self._guild_icon(interaction.guild)
            await respond_cv2(interaction, build_logs(events, icon), ephemeral=True)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(Panel(bot))
