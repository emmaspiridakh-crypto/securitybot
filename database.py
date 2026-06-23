import aiosqlite
import json
import time

DB_PATH = "security.db"

CONFIG_DEFAULTS = {
    "alt_age_days":       "30",
    "alt_action":         "kick",
    "spam_threshold":     "5",
    "spam_window_secs":   "5",
    "spam_timeout_mins":  "10",
    "link_timeout_mins":  "60",
    "mass_action_limit":  "3",
    "mass_action_window": "10",
}


class Database:

    @classmethod
    async def init(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS server_owners (
                    guild_id TEXT NOT NULL,
                    user_id  TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS whitelist_users (
                    guild_id TEXT NOT NULL,
                    user_id  TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS whitelist_bots (
                    guild_id TEXT NOT NULL,
                    bot_id   TEXT NOT NULL,
                    PRIMARY KEY (guild_id, bot_id)
                );
                CREATE TABLE IF NOT EXISTS whitelist_channels (
                    guild_id   TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, channel_id)
                );
                CREATE TABLE IF NOT EXISTS disabled_modules (
                    guild_id    TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    PRIMARY KEY (guild_id, module_name)
                );
                CREATE TABLE IF NOT EXISTS config (
                    guild_id TEXT NOT NULL,
                    key      TEXT NOT NULL,
                    value    TEXT,
                    PRIMARY KEY (guild_id, key)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    guild_id TEXT NOT NULL,
                    key      TEXT NOT NULL,
                    value    TEXT,
                    PRIMARY KEY (guild_id, key)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id  TEXT    NOT NULL,
                    type      TEXT    NOT NULL,
                    data      TEXT,
                    timestamp INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_guild ON events (guild_id);
            """)
            await db.commit()

    # ── Server Owners ─────────────────────────────────────
    @classmethod
    async def add_server_owner(cls, guild_id: str, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO server_owners VALUES (?, ?)", (guild_id, user_id)
            )
            await db.commit()

    @classmethod
    async def remove_server_owner(cls, guild_id: str, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM server_owners WHERE guild_id=? AND user_id=?", (guild_id, user_id)
            )
            await db.commit()

    @classmethod
    async def is_server_owner(cls, guild_id: str, user_id: str, installer_id: str = None) -> bool:
        if installer_id and str(user_id) == str(installer_id):
            return True
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM server_owners WHERE guild_id=? AND user_id=?",
                (guild_id, str(user_id))
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_server_owners(cls, guild_id: str) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id FROM server_owners WHERE guild_id=?", (guild_id,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Users ───────────────────────────────────
    @classmethod
    async def add_whitelist_user(cls, guild_id: str, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO whitelist_users VALUES (?, ?)", (guild_id, user_id)
            )
            await db.commit()

    @classmethod
    async def remove_whitelist_user(cls, guild_id: str, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM whitelist_users WHERE guild_id=? AND user_id=?", (guild_id, user_id)
            )
            await db.commit()

    @classmethod
    async def is_whitelist_user(cls, guild_id: str, user_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_users WHERE guild_id=? AND user_id=?",
                (guild_id, str(user_id))
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_users(cls, guild_id: str) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id FROM whitelist_users WHERE guild_id=?", (guild_id,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Bots ────────────────────────────────────
    @classmethod
    async def add_whitelist_bot(cls, guild_id: str, bot_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO whitelist_bots VALUES (?, ?)", (guild_id, bot_id)
            )
            await db.commit()

    @classmethod
    async def remove_whitelist_bot(cls, guild_id: str, bot_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM whitelist_bots WHERE guild_id=? AND bot_id=?", (guild_id, bot_id)
            )
            await db.commit()

    @classmethod
    async def is_whitelist_bot(cls, guild_id: str, bot_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_bots WHERE guild_id=? AND bot_id=?",
                (guild_id, str(bot_id))
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_bots(cls, guild_id: str) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT bot_id FROM whitelist_bots WHERE guild_id=?", (guild_id,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Channels ────────────────────────────────
    @classmethod
    async def add_whitelist_channel(cls, guild_id: str, channel_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO whitelist_channels VALUES (?, ?)", (guild_id, channel_id)
            )
            await db.commit()

    @classmethod
    async def remove_whitelist_channel(cls, guild_id: str, channel_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM whitelist_channels WHERE guild_id=? AND channel_id=?",
                (guild_id, channel_id)
            )
            await db.commit()

    @classmethod
    async def is_whitelist_channel(cls, guild_id: str, channel_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_channels WHERE guild_id=? AND channel_id=?",
                (guild_id, str(channel_id))
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_channels(cls, guild_id: str) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT channel_id FROM whitelist_channels WHERE guild_id=?", (guild_id,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Modules ───────────────────────────────────────────
    @classmethod
    async def disable_module(cls, guild_id: str, name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO disabled_modules VALUES (?, ?)", (guild_id, name)
            )
            await db.commit()

    @classmethod
    async def enable_module(cls, guild_id: str, name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM disabled_modules WHERE guild_id=? AND module_name=?", (guild_id, name)
            )
            await db.commit()

    @classmethod
    async def is_module_enabled(cls, guild_id: str, name: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM disabled_modules WHERE guild_id=? AND module_name=?",
                (guild_id, name)
            ) as cur:
                return await cur.fetchone() is None

    @classmethod
    async def get_disabled_modules(cls, guild_id: str) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT module_name FROM disabled_modules WHERE guild_id=?", (guild_id,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Config ────────────────────────────────────────────
    @classmethod
    async def get_config(cls, guild_id: str, key: str, default=None) -> str:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT value FROM config WHERE guild_id=? AND key=?", (guild_id, key)
            ) as cur:
                row = await cur.fetchone()
                return row[0] if row else (default or CONFIG_DEFAULTS.get(key))

    @classmethod
    async def set_config(cls, guild_id: str, key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
                (guild_id, key, value)
            )
            await db.commit()

    @classmethod
    async def get_all_config(cls, guild_id: str) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT key, value FROM config WHERE guild_id=?", (guild_id,)
            ) as cur:
                stored = {r[0]: r[1] for r in await cur.fetchall()}
        result = dict(CONFIG_DEFAULTS)
        result.update(stored)
        return result

    # ── Settings ──────────────────────────────────────────
    @classmethod
    async def get_setting(cls, guild_id: str, key: str, default=None) -> str:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT value FROM settings WHERE guild_id=? AND key=?", (guild_id, key)
            ) as cur:
                row = await cur.fetchone()
                return row[0] if row else default

    @classmethod
    async def set_setting(cls, guild_id: str, key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (guild_id, key, value) VALUES (?, ?, ?)",
                (guild_id, key, value)
            )
            await db.commit()

    # ── Events ────────────────────────────────────────────
    @classmethod
    async def log_event(cls, guild_id: str, event_type: str, data: dict):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO events (guild_id, type, data, timestamp) VALUES (?, ?, ?, ?)",
                (guild_id, event_type, json.dumps(data), int(time.time() * 1000))
            )
            await db.execute("""
                DELETE FROM events WHERE guild_id=? AND id NOT IN (
                    SELECT id FROM events WHERE guild_id=? ORDER BY id DESC LIMIT 500
                )
            """, (guild_id, guild_id))
            await db.commit()

    @classmethod
    async def get_recent_events(cls, guild_id: str, limit: int = 10) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT type, data, timestamp FROM events WHERE guild_id=? ORDER BY id DESC LIMIT ?",
                (guild_id, limit)
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {"type": r[0], "data": json.loads(r[1]) if r[1] else {}, "timestamp": r[2]}
                    for r in rows
                ]
