# -*- coding: utf-8 -*-
import os
import sys

# Windows konsol UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database as db

# Log yapılandırması
LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "bot.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("AlaCafeBot")

# Ortam değişkenlerini yükle
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "!")

intents = discord.Intents.all()

class AlaCafeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(DEFAULT_PREFIX),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Veritabanını başlat
        await db.init_db()
        logger.info("SQLite Veritabanı ve Özelleştirmeler hazırlandı.")

        # Modülleri yükle
        cogs = [
            "cogs.music",              # 🎵 Müzik İstasyonu
            "cogs.tables",             # 🚪 Sanal Kafe Masaları (Join to Create)
            "cogs.cafe_interactions",   # 💨 Köz İste & İkram
            "cogs.loyalty",            # 🏆 Müdavim Seviye & Sadakat
            "cogs.nargile",            # 💨 Meşhur Nargileler
            "cogs.transcriptor",       # 📜 Chat Metin Döküm Makinesi
            "cogs.management",         # 👑 Yönetim & VIP Kadrosu
            "cogs.moderation",         # 🛡️ Moderasyon
            "cogs.welcome",            # 👋 Dinamik Karşılama
            "cogs.utility",            # 📊 Sunucu Bilgi & Araçlar
            "cogs.tickets",            # 🎫 Destek Masası
            "cogs.giveaway",           # 🎉 Çekiliş Sistemi
            "cogs.game_invites",       # 🎮 Özel DM Oyun Davetleri
            "cogs.ziya_ai",            # ☕ Ziya Ortak AI (Yapay Zeka Danışmanı)
            "cogs.reporting"           # 📊 Master Rapor & Denetim Sistemi
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Modül yüklendi: {cog}")
            except Exception as e:
                logger.error(f"Modül yükleme hatası ({cog}): {e}")

    async def on_ready(self):
        banner = f"""
======================================================
  ☕ {self.user.name} v3.0 — Müzik & Master Engine!
  ID: {self.user.id}
  Sunucular: {len(self.guilds)} adet sunucuda aktif
======================================================
"""
        print(banner)
        logger.info("Bot v3.0 başarıyla ayağa kalktı!")

        # Tüm sunuculara anında Slash komut senkronizasyonu
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"✅ [{guild.name}] ({guild.id}) sunucusuna {len(synced)} adet Slash komutu ANINDA senkronize edildi!")
            except Exception as e:
                logger.error(f"❌ [{guild.name}] sunucusuna senkronizasyon hatası: {e}")

        # Durum mesajını veritabanından dinamik oku
        customs = await db.get_customizations()
        act_text = customs.get("bot_activity", "Ala Lounge & Nargile Masalarını 💨 | /oynat")
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=act_text
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Komut Hatası: {error}")

bot = AlaCafeBot()

if __name__ == "__main__":
    if not TOKEN:
        logger.critical("DISCORD_TOKEN bulunamadı! Lütfen .env dosyasını kontrol edin.")
        sys.exit(1)
    bot.run(TOKEN)
