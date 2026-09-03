# -*- coding: utf-8 -*-
import os
import io
import re
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_SUCCESS, COLOR_INFO, COLOR_ERROR

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transcripts")

class TranscriptorCog(commands.Cog, name="DökümMakinesi"):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    @commands.command(name="dokum", aliases=["chat-dokum", "sohbet-dokum"])
    @commands.has_permissions(administrator=True)
    async def prefix_dokum(self, ctx, limit: int = 100):
        await self.execute_transcript(ctx.channel, limit, ctx.author, ctx.send)

    @app_commands.command(name="chat-dokum", description="Seçilen kanalın tüm mesajlarını, kullanıcılarını ve eklerini metin (.txt) dosyasına döker")
    @app_commands.describe(kanal="Dökümü alınacak metin kanalı (boş bırakılırsa bulunulan kanal)", limit="Çekilecek mesaj sayısı (10-1000 arası, varsayılan: 100)")
    @app_commands.checks.has_permissions(administrator=True)
    async def chat_dokum(self, interaction: discord.Interaction, kanal: discord.TextChannel = None, limit: int = 100):
        target_channel = kanal or interaction.channel
        if limit < 10 or limit > 1000:
            await interaction.response.send_message("❌ Mesaj sayısı 10 ile 1000 arasında olmalıdır.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        await self.execute_transcript(target_channel, limit, interaction.user, interaction.followup.send)

    async def execute_transcript(self, channel: discord.TextChannel, limit: int, author: discord.Member, send_func):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Güvenli dosya adı oluşturma (Path traversal koruması)
        clean_ch_name = re.sub(r'[^a-zA-Z0-9_\-]', '', channel.name.replace(" ", "_")) or "kanal"
        filename = f"dokum_{clean_ch_name}_{file_timestamp}.txt"
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)

        header = (
            f"================================================================================\n"
            f"  ALA CAFE & LOUNGE — SOHBET METİN DÖKÜMÜ\n"
            f"  Kanal Adı   : #{channel.name} (ID: {channel.id})\n"
            f"  Sunucu      : {channel.guild.name} (ID: {channel.guild.id})\n"
            f"  Döküm Tarihi: {now_str}\n"
            f"  Talep Eden  : {author.display_name} ({author.name}#{author.discriminator})\n"
            f"  Hedef Limit : Son {limit} mesaj\n"
            f"================================================================================\n\n"
        )

        messages = []
        async for msg in channel.history(limit=limit, oldest_first=True):
            messages.append(msg)

        lines = [header]
        for msg in messages:
            t_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author_str = f"{msg.author.display_name} ({msg.author.name})"
            content = msg.clean_content.strip()

            line = f"[{t_str}] {author_str}:\n"
            if content:
                line += f"  {content}\n"

            # Ekler / Görseller
            if msg.attachments:
                for att in msg.attachments:
                    line += f"  [Ek Dosya: {att.filename} -> {att.url}]\n"

            # Embed bağlantıları
            if msg.embeds:
                for em in msg.embeds:
                    if em.title or em.description:
                        line += f"  [Zengin Kart: {em.title or ''} | {em.description or ''}]\n"

            line += "-" * 80 + "\n"
            lines.append(line)

        summary_text = (
            f"\n================================================================================\n"
            f"  DÖKÜM TAMAMLANDI: Toplam {len(messages)} adet mesaj başarıyla metne çevrildi.\n"
            f"================================================================================\n"
        )
        lines.append(summary_text)

        full_text = "".join(lines)

        # Dosyayı yerel arşive kaydet
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_text)

        # Discord'a dosya olarak yükle
        file_bytes = io.BytesIO(full_text.encode("utf-8"))
        discord_file = discord.File(file_bytes, filename=filename)

        embed = discord.Embed(
            title="📜 Chat Metin Dökümü Hazırlandı!",
            description=(
                f"**Kanal:** {channel.mention}\n"
                f"**Çekilen Mesaj:** `{len(messages)}` adet\n"
                f"**Arşiv Dosyası:** `{filename}`\n\n"
                f"💾 Dosya ekte sunulmuştur ve ayrıca **Masaüstü Yönetim Paneli**'ne aktarılmıştır."
            ),
            color=COLOR_SUCCESS
        )
        embed.set_footer(text="Ala Cafe • Metin Döküm Makinesi")
        await send_func(embed=embed, file=discord_file)

async def setup(bot):
    await bot.add_cog(TranscriptorCog(bot))
