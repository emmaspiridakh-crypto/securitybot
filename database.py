import aiosqlite
import json
import time

DB_PATH = "security.db"

class Database:

    @classmethod
    async def init(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS server_owners (
                    user_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS whitelist_users (
                    user_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS whitelist_bots (
                    bot_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS whitelist_channels (
                    channel_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS disabled_modules (
                    module_name TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS config (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    type      TEXT    NOT NULL,
                    data      TEXT,
                    timestamp INTEGER NOT NULL
                );
            """)

            defaults = {
                "alt_age_days":       "30",
                "alt_action":         "kick",
                "spam_threshold":     "5",
                "spam_window_secs":   "5",
                "spam_timeout_mins":  "10",
                "link_timeout_mins":  "60",
                "mass_action_limit":  "3",
                "mass_action_window": "10",
            }
            for k, v in defaults.items():
                await db.execute(
                    "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v)
                )
            await db.commit()

    # ── Server Owners ─────────────────────────────────────
    @classmethod
    async def add_server_owner(cls, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO server_owners VALUES (?)", (user_id,))
            await db.commit()

    @classmethod
    async def remove_server_owner(cls, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM server_owners WHERE user_id=?", (user_id,))
            await db.commit()

    @classmethod
    async def is_server_owner(cls, user_id: str, installer_id: str = None) -> bool:
        if installer_id and str(user_id) == str(installer_id):
            return True
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM server_owners WHERE user_id=?", (str(user_id),)
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_server_owners(cls) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM server_owners") as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Users ───────────────────────────────────
    @classmethod
    async def add_whitelist_user(cls, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO whitelist_users VALUES (?)", (user_id,))
            await db.commit()

    @classmethod
    async def remove_whitelist_user(cls, user_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM whitelist_users WHERE user_id=?", (user_id,))
            await db.commit()

    @classmethod
    async def is_whitelist_user(cls, user_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_users WHERE user_id=?", (str(user_id),)
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_users(cls) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM whitelist_users") as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Bots ────────────────────────────────────
    @classmethod
    async def add_whitelist_bot(cls, bot_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO whitelist_bots VALUES (?)", (bot_id,))
            await db.commit()

    @classmethod
    async def remove_whitelist_bot(cls, bot_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM whitelist_bots WHERE bot_id=?", (bot_id,))
            await db.commit()

    @classmethod
    async def is_whitelist_bot(cls, bot_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_bots WHERE bot_id=?", (str(bot_id),)
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_bots(cls) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT bot_id FROM whitelist_bots") as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Whitelist Channels ────────────────────────────────
    @classmethod
    async def add_whitelist_channel(cls, channel_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO whitelist_channels VALUES (?)", (channel_id,))
            await db.commit()

    @classmethod
    async def remove_whitelist_channel(cls, channel_id: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM whitelist_channels WHERE channel_id=?", (channel_id,))
            await db.commit()

    @classmethod
    async def is_whitelist_channel(cls, channel_id: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM whitelist_channels WHERE channel_id=?", (str(channel_id),)
            ) as cur:
                return await cur.fetchone() is not None

    @classmethod
    async def get_whitelist_channels(cls) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT channel_id FROM whitelist_channels") as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Modules ───────────────────────────────────────────
    @classmethod
    async def disable_module(cls, name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO disabled_modules VALUES (?)", (name,))
            await db.commit()

    @classmethod
    async def enable_module(cls, name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM disabled_modules WHERE module_name=?", (name,))
            await db.commit()

    @classmethod
    async def is_module_enabled(cls, name: str) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM disabled_modules WHERE module_name=?", (name,)
            ) as cur:
                return await cur.fetchone() is None

    @classmethod
    async def get_disabled_modules(cls) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT module_name FROM disabled_modules") as cur:
                return [r[0] for r in await cur.fetchall()]

    # ── Config ────────────────────────────────────────────
    @classmethod
    async def get_config(cls, key: str, default=None) -> str:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM config WHERE key=?", (key,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else default

    @classmethod
    async def set_config(cls, key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
            )
            await db.commit()

    @classmethod
    async def get_all_config(cls) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT key, value FROM config") as cur:
                return {r[0]: r[1] for r in await cur.fetchall()}

    # ── Settings ──────────────────────────────────────────
    @classmethod
    async def get_setting(cls, key: str, default=None) -> str:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else default

    @classmethod
    async def set_setting(cls, key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
            await db.commit()

    # ── Events ────────────────────────────────────────────
    @classmethod
    async def log_event(cls, event_type: str, data: dict):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO events (type, data, timestamp) VALUES (?, ?, ?)",
                (event_type, json.dumps(data), int(time.time() * 1000))
            )
            await db.execute("""
                DELETE FROM events WHERE id NOT IN (
                    SELECT id FROM events ORDER BY id DESC LIMIT 500
                )
            """)
            await db.commit()

    @classmethod
    async def get_recent_events(cls, limit: int = 10) -> list:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT type, data, timestamp FROM events ORDER BY id DESC LIMIT ?",
                (limit,)
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {"type": r[0], "data": json.loads(r[1]) if r[1] else {}, "timestamp": r[2]}
                    for r in rows
                ]
