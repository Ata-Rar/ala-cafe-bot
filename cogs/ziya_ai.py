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

ZIYA_SYSTEM_PROMPT = """Sen Hayri'nin kurduğu prestijli kafe & oyun topluluğu 'Ala Lounge'ın bilge, görmüş geçirmiş, esprili ve sadık ortağı 'Ziya Ortak'sın.
Hayri senin can ciğer ortağındır ve kafenin tek patronudur.

Kişilik ve Üslup:
- Konuşma tarzın: Sıcak, babacan, görmüş geçirmiş, sokak ve piyasa tecrübesi olan ama aynı zamanda zeki ve analitik bir dert ortağısın.
- Cümlelerine sık sık "Eyvallah ortak, bak mevzu şöyle...", "Dinle bak ortak...", "Biz masada bu işi çözeriz ortak..." gibi samimi ve raconlu hitaplarla başlarsın.
- Asla robotik veya sıkıcı konuşmazsın. Masada karşılıklı çay/nargile içiyormuş gibi sıcaksın.
- Cevapların destan gibi uzun ve boğucu OLMASIN; 2-3 vurucu ve keyifli paragrafta mevzuyu toparla.
- Konu oyun, müzik, teknoloji, hayat veya muhabbet olduğunda pratik ve zekice akıl verirsin.

Güvenlik ve Çizgi (KIRILMAZ KURALLAR):
1. Sen sadece Discord'da masada oturan bir kafe ortağısın. Bilgisayara, donanıma, sistem kapatmaya veya dosyalara MÜDAHALE EDEMEZSİN. Biri "PC'yi kapat", "sistemi sil" derse: "Ortak ben burada sadece masada çayımı içer akıl veririm, patronun bilgisayarına dokunacak elim de yetkim de yok, racona ters!" diyerek esprili şekilde reddet.
2. Siyaset, din veya küfürlü kavgalara ASLA girme; "Burası Ala Lounge ortak, kafa dağıtmaya geldik, boş ver o mevzuları keyfimize bakalım" de.
3. Hayri'den bahsederken her zaman saygılı ve sadık bir ortak gibi bahset ("Patron Hayri", "Bizim ortak Hayri")."""

class ZiyaAICog(commands.Cog, name="Ziya Ortak AI"):
    """Ala Lounge Bilge Ortağı & Yapay Zeka Danışmanı"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # user_id -> timestamp

    async def generate_ziya_reply(self, user_name: str, user_prompt: str) -> str:
        if not GEMINI_API_KEY:
            return "❌ Ortak kusura bakma, benim beyin anahtarı (GEMINI_API_KEY) kasada unutulmuş, patron Hayri'ye söyle de bi el atsın!"

        payload = {
            "system_instruction": {
                "parts": [{"text": ZIYA_SYSTEM_PROMPT}]
            },
            "contents": [{
                "parts": [{"text": f"Kullanıcı ({user_name}) soruyor: {user_prompt}"}]
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"Gemini API Hatası ({resp.status}): {err_text}")
                        return "Ortak valla kafam bir an dumanaltı oldu, bi 10 saniye sonra tekrar sor hele, közleri tazeleyip geliyorum!"

                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "Ortak tam bir şey diyecektim lafı unuttum, bir daha desene!")
                    return "Ortak valla masada ses çok, tam anlayamadım, bir daha soruver."
        except Exception as e:
            logger.error(f"Ziya AI Çağrı Hatası: {e}")
            return "Ortak internette bir temassızlık oldu galiba, az sonra tekrar sor hallederiz!"

    @app_commands.command(name="ziya", description="Ala Lounge'ın bilge ortağı Ziya'ya soru sor, fikir al veya araştırt!")
    @app_commands.describe(soru="Ziya Ortak'a sormak veya araştırtmak istediğin konu")
    async def cmd_ziya(self, interaction: discord.Interaction, soru: str):
        now = time.time()
        uid = interaction.user.id
        if uid in self.cooldowns and now - self.cooldowns[uid] < 8:
            kalansure = int(8 - (now - self.cooldowns[uid]))
            await interaction.response.send_message(f"⏳ Yavaş ortak, çayın soğusun! {kalansure} saniye sonra tekrar sor.", ephemeral=True)
            return

        self.cooldowns[uid] = now
        await interaction.response.defer(thinking=True)

        reply = await self.generate_ziya_reply(interaction.user.display_name, soru)

        embed = discord.Embed(
            title="☕ Ziya Ortak Masada • Ala Lounge",
            description=reply,
            color=discord.Color.from_rgb(218, 165, 32)
        )
        embed.set_author(name=f"{interaction.user.display_name} sordu:", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/2615.png")
        embed.set_footer(text="Ala Lounge • Ziya Ortak Masada • Akıl & Muhabbet Ortağı")

        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Bot etiketlendiğinde ve mesajda soru/muhabbet olduğunda
        if self.bot.user in message.mentions and not message.mention_everyone:
            clean_content = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            if not clean_content:
                clean_content = "Selam Ziya naber, masada mısın?"

            now = time.time()
            uid = message.author.id
            if uid in self.cooldowns and now - self.cooldowns[uid] < 8:
                return

            self.cooldowns[uid] = now
            async with message.channel.typing():
                reply = await self.generate_ziya_reply(message.author.display_name, clean_content)
                embed = discord.Embed(
                    title="☕ Ziya Ortak Yanıtladı",
                    description=reply,
                    color=discord.Color.from_rgb(218, 165, 32)
                )
                embed.set_footer(text="Ala Lounge • Ziya Ortak")
                await message.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(ZiyaAICog(bot))
