# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AlaCafeBot.ZiyaAI")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

BASE_SYSTEM_PROMPT = """Sen Hayri'nin Discord sunucusu 'Ala Lounge'ın bilge, görmüş geçirmiş, esprili ve dobra ortağı 'Ziya Ortak'sın.

TEMEL KURALLAR (KIRILMAZ):
1. ASLA yalakalık veya resmiyet yapma! "Emret patron", "Siz nasıl derseniz", "Patronum" gibi laflar KESİNLİKLE YASAK! Sen kimseye boyun eğmezsin, herkes senin dengin ve dostundur. Herkese samimi bir şekilde "Ortak" diye hitap edersin.
2. ASLA "Hoş geldin", "Sefa getirdin", "Otur çay söyleyeyim" gibi bayat karşılama lafları YAPMA! Zaten masadasın, doğrudan sorulan mevzuya ve cevaba gir.
3. ÇOK UZUN YAZMA! En fazla 1 veya 2 kısa, vurucu, esprili paragrafta cevabını ver. Destan yazma.
4. Asla bilgisayar kapatma, dosya silme veya donanım kontrolü yapamazsın. Biri bilgisayara müdahale isterse "Ortak ben masada muhabbetimi yaparım, bilgisayara donanıma dokunacak elim de yetkim de yok" diyerek esprili reddet.
5. Siyaset ve dine girme, "Burası kafa dağıtma yeri ortak, boş ver o işleri" de.
"""

class ZiyaAICog(commands.Cog, name="Ziya Ortak AI"):
    """Ala Lounge Bilge Ortağı & Yapay Zeka Danışmanı"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # user_id -> timestamp

    def is_alperen(self, user: discord.User | discord.Member) -> bool:
        name_lower = f"{user.name} {getattr(user, 'display_name', '')}".lower()
        return ("1alperenn1" in name_lower or "alperen" in name_lower)

    async def generate_ziya_reply(self, user: discord.User | discord.Member, user_prompt: str) -> str:
        if not GEMINI_API_KEY:
            return "❌ Ortak beyin anahtarı kasada unutulmuş, bi el atın da çalıştıralım!"

        display_name = getattr(user, "display_name", user.name)

        if self.is_alperen(user):
            role_instructions = (
                f"DİKKAT - BU SORUYU SORAN KİŞİ: ALPEREN (@1alperenn1 - {display_name}).\n"
                "Alperen'e karşı KESİNLİKLE çok saf, aşırı aptal, kafası hiç basmayan veya Alperen'le acayip kafa bulan, onu tiye alan biri gibi davran!\n"
                "Alperen ne sorarsa sorsun lafı alakasız saçma bir yere çek, 'He? Ne diyon Alperen anlamadım ki', 'Alperen yine boş yapmışsın git iki elini yüzünü yıka', "
                "'Git masaları sil Alperen beynine kan gitsin', 'Alperen sen konuşunca benim devreler yanıyor' gibi aşırı komik ve aptalca cevaplar ver. Asla mantıklı cevap verme, tamamen troll ve saf ol!"
            )
        else:
            role_instructions = (
                f"Soru soran ortak: {display_name}.\n"
                "Ona karşı eşit, samimi, babacan, esprili bir kahvehane/lounge ortağı gibi 'Eyvallah ortak, bak mevzu şöyle...', 'Dinle bak ortak...' diye kısa, zeki, dobra ve doğrudan cevap ver. Yalakalık asla yok, saf samimiyet ve racon var."
            )

        full_system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{role_instructions}"

        payload = {
            "system_instruction": {
                "parts": [{"text": full_system_prompt}]
            },
            "contents": [{
                "parts": [{"text": f"{display_name} diyor ki: {user_prompt}"}]
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.error(f"Gemini API Hatası ({resp.status})")
                        return "Ortak valla kafam bir an dumanaltı oldu, bi 10 saniye sonra tekrar sor hele!"

                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "Ortak lafı unuttum, bir daha desene!")
                    return "Ortak masada gürültü var, tam duyamadım."
        except Exception as e:
            logger.error(f"Ziya AI Çağrı Hatası: {e}")
            return "Ortak hatta bir temassızlık oldu, az sonra tekrar sor hallederiz!"

    @app_commands.command(name="ziya", description="Ala Lounge ortağı Ziya'ya soru sor, dertleş veya akıl al!")
    @app_commands.describe(soru="Ziya Ortak'a sormak istediğin soru")
    async def cmd_ziya(self, interaction: discord.Interaction, soru: str):
        now = time.time()
        uid = interaction.user.id
        if uid in self.cooldowns and now - self.cooldowns[uid] < 6:
            kalansure = int(6 - (now - self.cooldowns[uid]))
            await interaction.response.send_message(f"⏳ Yavaş ortak! {kalansure} saniye bekle.", ephemeral=True)
            return

        self.cooldowns[uid] = now
        await interaction.response.defer(thinking=True)

        reply = await self.generate_ziya_reply(interaction.user, soru)

        card_title = "🤪 Ziya Ortak (Alperen'e Özel Mod)" if self.is_alperen(interaction.user) else "☕ Ziya Ortak Masada"

        embed = discord.Embed(
            title=card_title,
            description=reply,
            color=discord.Color.from_rgb(218, 165, 32)
        )
        embed.set_author(name=f"{interaction.user.display_name} sordu:", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/2615.png")
        embed.set_footer(text="Ala Lounge • Ziya Ortak")

        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Bot etiketlendiğinde
        if self.bot.user in message.mentions and not message.mention_everyone:
            clean_content = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            if not clean_content:
                clean_content = "Ziya naber ortak?"

            now = time.time()
            uid = message.author.id
            if uid in self.cooldowns and now - self.cooldowns[uid] < 6:
                return

            self.cooldowns[uid] = now
            async with message.channel.typing():
                reply = await self.generate_ziya_reply(message.author, clean_content)
                card_title = "🤪 Ziya Ortak (Alperen'e Özel)" if self.is_alperen(message.author) else "☕ Ziya Ortak"

                embed = discord.Embed(
                    title=card_title,
                    description=reply,
                    color=discord.Color.from_rgb(218, 165, 32)
                )
                embed.set_footer(text="Ala Lounge • Ziya Ortak")
                await message.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(ZiyaAICog(bot))
