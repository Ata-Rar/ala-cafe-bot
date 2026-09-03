# -*- coding: utf-8 -*-
import sqlite3
import os
import time
import math

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cafe.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def init_db():
    conn = get_connection()
    c = conn.cursor()
    # 1. VIP Üyeler
    c.execute("""
        CREATE TABLE IF NOT EXISTS vip_members (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            title TEXT,
            notes TEXT,
            added_at TEXT
        )
    """)
    # 2. Sunucu Ayarları
    c.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            welcome_channel_id INTEGER,
            auto_role_id INTEGER,
            log_channel_id INTEGER,
            ticket_category_id INTEGER,
            table_creator_channel_id INTEGER,
            kozcu_role_id INTEGER
        )
    """)
    # 3. Destek Talepleri
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER UNIQUE,
            user_id INTEGER,
            guild_id INTEGER,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    """)
    # 4. Bot Özelleştirmeleri
    c.execute("""
        CREATE TABLE IF NOT EXISTS bot_customizations (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # 5. Sanal Kafe Masaları (Geçici Ses Odaları)
    c.execute("""
        CREATE TABLE IF NOT EXISTS temp_tables (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            owner_id INTEGER,
            is_locked INTEGER DEFAULT 0,
            user_limit INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    # 6. Müdavim Seviye ve XP Sistemi
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_levels (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_msg_xp REAL DEFAULT 0,
            voice_joined_at REAL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    conn.commit()
    conn.close()

# --- Özelleştirme Metotları ---
def get_customization(key, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM bot_customizations WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

async def get_customizations():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM bot_customizations")
    rows = c.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def set_customization(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO bot_customizations (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?", (key, str(value), str(value)))
    conn.commit()
    conn.close()

# --- Sanal Masa Metotları ---
def add_temp_table(channel_id, guild_id, owner_id):
    conn = get_connection()
    c = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO temp_tables (channel_id, guild_id, owner_id, created_at) VALUES (?, ?, ?, ?)", (channel_id, guild_id, owner_id, now))
    conn.commit()
    conn.close()

def remove_temp_table(channel_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM temp_tables WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_temp_table(channel_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM temp_tables WHERE channel_id = ?", (channel_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# --- Seviye ve XP Metotları ---
def get_xp_for_level(level):
    return level * level * 100

def get_level_from_xp(xp):
    return max(1, int(math.sqrt(xp / 100)))

def get_user_level_data(user_id, guild_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM user_levels WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"user_id": user_id, "guild_id": guild_id, "xp": 0, "level": 1, "last_msg_xp": 0, "voice_joined_at": 0}

def add_user_xp(user_id, guild_id, xp_gain):
    conn = get_connection()
    c = conn.cursor()
    data = get_user_level_data(user_id, guild_id)
    new_xp = data["xp"] + xp_gain
    new_level = get_level_from_xp(new_xp)
    old_level = data["level"]
    now = time.time()

    c.execute("""
        INSERT INTO user_levels (user_id, guild_id, xp, level, last_msg_xp)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, guild_id) DO UPDATE SET
            xp = excluded.xp,
            level = excluded.level,
            last_msg_xp = excluded.last_msg_xp
    """, (user_id, guild_id, new_xp, new_level, now))
    conn.commit()
    conn.close()
    return old_level, new_level, new_xp

def get_top_leaderboard(guild_id, limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, xp, level FROM user_levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?", (guild_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
