# -*- coding: utf-8 -*-
import os
import aiosqlite
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cafe.db")

DEFAULT_WELCOME_TITLE = "☕ Ala Lounge'a Hoş Geldiniz!"
DEFAULT_WELCOME_MSG = "Aramıza hoş geldin {kullanici}! Boş masalara geçebilir, sıcak muhabbetimize katılabilirsin. Sunucumuz seninle beraber {uye_sayisi} kişi oldu! 💨"
DEFAULT_ACTIVITY = "Ala Lounge & Nargile Masalarını 💨 | /oynat"

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        # VIP & Yönetim Kadrosu
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vip_members (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                title TEXT,
                notes TEXT,
                added_at TEXT
            )
        """)
        # Sunucu Ayarları
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                auto_role_id INTEGER,
                log_channel_id INTEGER,
                ticket_category_id INTEGER
            )
        """)
        # Ceza / Uyarı Kayıtları
        await db.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                mod_id INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        """)
        # Dinamik Bot Özelleştirmeleri (Panelden Yönetilen)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_customizations (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Varsayılan özelleştirmeleri yükle
        defaults = [
            ("welcome_title", DEFAULT_WELCOME_TITLE),
            ("welcome_message", DEFAULT_WELCOME_MSG),
            ("bot_activity", DEFAULT_ACTIVITY),
            ("default_volume", "80")
        ]
        for k, v in defaults:
            await db.execute("INSERT OR IGNORE INTO bot_customizations (key, value) VALUES (?, ?)", (k, v))

        await db.commit()

# --- Özelleştirme Fonksiyonları ---
async def get_customizations():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT key, value FROM bot_customizations") as cursor:
            rows = await cursor.fetchall()
            data = {r["key"]: r["value"] for r in rows}
            return {
                "welcome_title": data.get("welcome_title", DEFAULT_WELCOME_TITLE),
                "welcome_message": data.get("welcome_message", DEFAULT_WELCOME_MSG),
                "bot_activity": data.get("bot_activity", DEFAULT_ACTIVITY),
                "default_volume": int(data.get("default_volume", 80))
            }

async def set_customization(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO bot_customizations (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        await db.commit()

# --- VIP & Yönetim İşlemleri ---
async def add_vip(user_id: int, name: str, title: str, notes: str = ""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO vip_members (user_id, name, title, notes, added_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                title = excluded.title,
                notes = excluded.notes
        """, (user_id, name, title, notes, now))
        await db.commit()

async def remove_vip(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM vip_members WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_vips():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM vip_members ORDER BY added_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def is_vip(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM vip_members WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

# --- Sunucu Ayarları & Moderasyon ---
ALLOWED_SETTINGS_COLUMNS = {"welcome_channel_id", "auto_role_id", "log_channel_id", "ticket_category_id"}

async def set_guild_setting(guild_id: int, column: str, value: int):
    if column not in ALLOWED_SETTINGS_COLUMNS:
        raise ValueError(f"Geçersiz ayar sütunu: {column}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            INSERT INTO guild_settings (guild_id, {column})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {column} = excluded.{column}
        """, (guild_id, value))
        await db.commit()

async def get_guild_settings(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}

async def add_warn(user_id: int, guild_id: int, mod_id: int, reason: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO warns (user_id, guild_id, mod_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, mod_id, reason, now))
        await db.commit()

async def get_warns(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM warns WHERE user_id = ? AND guild_id = ? ORDER BY id DESC",
            (user_id, guild_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
