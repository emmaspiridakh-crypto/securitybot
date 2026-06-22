import discord
from discord.ext import commands
from discord import app_commands
from database import Database
from utils.cv2_helper import respond_cv2, no_access

# key → (type_hint, description, default)
CONFIG_KEYS: dict[str, tuple[str, str, str]] = {
    "alt_age_days":       ("int",           "Ηλικία account (μέρες) για alt detection",         "30"),
    "alt_action":         ("choice:kick,log","Τι κάνει το bot στο alt (kick/log)",               "kick"),
    "spam_threshold":     ("int",           "Πόσα msgs για spam trigger",                        "5"),
    "spam_window_secs":   ("int",           "Χρονικό παράθυρο spam (δευτερόλεπτα)",              "5"),
    "spam_timeout_mins":  ("int",           "Timeout για spam (λεπτά)",                          "10"),
    "link_timeout_mins":  ("int",           "Timeout για links (λεπτά)",                         "60"),
    "mass_action_limit":  ("int",           "Αριθμός actions για anti-nuke trigger",             "3"),
    "mass_action_window": ("int",           "Χρονικό παράθυρο anti-nuke (δευτερόλεπτα)",        "10"),
}


class ConfigCmd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_owner(self, user_id: int) -> bool:
        return await Database.is_server_owner(str(user_id), self.bot.installer_id)

    @app_commands.command(name="config", description="Ρυθμίσεις security bot")
    @app_commands.describe(key="Το key (κενό = εμφάνιση όλων)", value="Η νέα τιμή")
    async def config(self, interaction: discord.Interaction,
                     key: str = None, value: str = None):
        if not await self._is_owner(interaction.user.id):
            await no_access(interaction)
            return

        # Show all
        if not key:
            cfg   = await Database.get_all_config()
            lines = []
            for k, (typ, desc, dflt) in CONFIG_KEYS.items():
                val = cfg.get(k, dflt)
                lines.append(f"**`{k}`** = `{val}`\n*{desc}*")

            await respond_cv2(interaction, [
                {"type": 17, "accent_color": 0x5865F2, "components": [
                    {"type": 10, "content": "## ⚙️ Security Config"},
                    {"type": 14},
                    {"type": 10, "content": "\n\n".join(lines)},
                    {"type": 14},
                    {"type": 10, "content": "Χρήση: `/config <key> <value>`"}
                ]}
            ], ephemeral=True)
            return

        # Unknown key
        if key not in CONFIG_KEYS:
            valid = ", ".join(f"`{k}`" for k in CONFIG_KEYS)
            await respond_cv2(interaction, [
                {"type": 17, "accent_color": 0xED4245, "components": [
                    {"type": 10, "content": f"❌ Unknown key: `{key}`\n\nValid: {valid}"}
                ]}
            ], ephemeral=True)
            return

        typ, desc, dflt = CONFIG_KEYS[key]

        # Show single key info
        if not value:
            current = await Database.get_config(key, dflt)
            await respond_cv2(interaction, [
                {"type": 17, "accent_color": 0x5865F2, "components": [
                    {"type": 10, "content": (
                        f"## ⚙️ `{key}`\n"
                        f"**Τιμή:** `{current}`\n"
                        f"**Περιγραφή:** {desc}\n"
                        f"**Τύπος:** `{typ}`\n"
                        f"**Default:** `{dflt}`"
                    )}
                ]}
            ], ephemeral=True)
            return

        # Validate
        if typ == "int":
            try:
                int(value)
            except ValueError:
                await respond_cv2(interaction, [
                    {"type": 17, "accent_color": 0xED4245, "components": [
                        {"type": 10, "content": f"❌ `{key}` πρέπει να είναι αριθμός."}
                    ]}
                ], ephemeral=True)
                return

        elif typ.startswith("choice:"):
            choices = typ.split(":")[1].split(",")
            if value not in choices:
                await respond_cv2(interaction, [
                    {"type": 17, "accent_color": 0xED4245, "components": [
                        {"type": 10, "content": f"❌ `{key}` πρέπει να είναι: {', '.join(f'`{c}`' for c in choices)}"}
                    ]}
                ], ephemeral=True)
                return

        await Database.set_config(key, value)
        await respond_cv2(interaction, [
            {"type": 17, "accent_color": 0x57F287, "components": [
                {"type": 10, "content": f"## ✅ Config Updated\n`{key}` → `{value}`"}
            ]}
        ], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCmd(bot))
