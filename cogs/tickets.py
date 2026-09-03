# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
import database
import os
import asyncio
import time
from datetime import datetime
from config import COLOR_CAFE

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transcripts")
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat & Arşivle 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        await interaction.response.send_message("🔒 Destek konuşması metne dökülüyor ve arşivleniyor, kanal 5 saniye sonra kapatılacak...", ephemeral=False)

        # Mesaj geçmişini topla
        lines = [
            "=" * 80,
            f"  ALA CAFE & LOUNGE — DESTEK TALEBİ DÖKÜMÜ",
            f"  Kanal Adı   : #{channel.name}",
            f"  Kapatan     : {interaction.user.display_name} ({interaction.user.name})",
            f"  Tarih       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80 + "\n"
        ]

        try:
            async for msg in channel.history(limit=1000, oldest_first=True):
                t_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{t_str}] {msg.author.display_name}: {msg.clean_content}")
                if msg.attachments:
                    for att in msg.attachments:
                        lines.append(f"  [Ek Dosya: {att.filename} -> {att.url}]")
        except Exception as e:
            lines.append(f"[Döküm Hatası: {e}]")

        full_transcript = "\n".join(lines)

        # Veritabanına kaydet
        database.close_ticket_log(channel.id, interaction.user.display_name, full_transcript)

        # Diske .txt dosyası olarak da kaydet
        safe_name = channel.name.replace(" ", "_")
        filename = f"ticket_{safe_name}_{int(time.time())}.txt"
        file_path = os.path.join(TRANSCRIPTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_transcript)

        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Destek kapatıldı ve arşivlendi ({interaction.user.display_name})")
        except Exception:
            pass

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="☕ Destek Talebi Aç (Garson Çağır)", style=discord.ButtonStyle.primary, emoji="🛎️", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        existing_name = f"destek-{member.name}".lower().replace(" ", "-")
        existing_ch = discord.utils.get(guild.text_channels, name=existing_name)
        if existing_ch:
            await interaction.response.send_message(f"❌ Zaten açık bir destek talebiniz bulunuyor: {existing_ch.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(
            name=existing_name,
            overwrites=overwrites,
            reason=f"Destek talebi: {member.name}"
        )

        # Veritabanına açık bilet olarak kaydet
        database.create_ticket_log(channel.id, channel.name, member.id, member.display_name)

        embed = discord.Embed(
            title=f"🛎️ Destek Masası — {member.display_name}",
            description=(
                f"Merhaba {member.mention}! Sunucu yetkililerine veya özel desteğe bildirmek istediğin konuyu buradan yazabilirsin.\n\n"
                f"🔒 İşiniz bittiğinde aşağıdaki **'Talebi Kapat & Arşivle'** butonuna basarak odayı sonlandırabilirsiniz.\n"
                f"*(Tüm görüşmeler kayıt altına alınmaktadır).* 📜"
            ),
            color=COLOR_CAFE
        )
        embed.set_footer(text="Ala Cafe • Müşteri Memnuniyeti Masası")
        await channel.send(content=f"{member.mention} | Yetkili ekibi", embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Destek odanız açıldı: {channel.mention}", ephemeral=True)

class TicketsCog(commands.Cog, name="Destek"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketOpenView())
        self.bot.add_view(TicketCloseView())

    @app_commands.command(name="destek-paneli", description="Kanalda sabit bir butonlu destek/talep paneli oluşturur")
    @app_commands.checks.has_permissions(administrator=True)
    async def destek_paneli(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛎️ Ala Cafe — Müşteri Hizmetleri & Destek Masası",
            description=(
                "Sunucuyla ilgili bir şikayetiniz, öneriniz, sorunuz veya özel bir yetkili görüşmesi ihtiyacınız mı var?\n\n"
                "Aşağıdaki **'Destek Talebi Aç'** butonuna tıklayarak sadece sizin ve yetkililerin görebileceği özel bir oda oluşturabilirsiniz."
            ),
            color=COLOR_CAFE
        )
        embed.set_footer(text="Ala Cafe • Esnaf samimiyeti, profesyonel hizmet")
        await interaction.channel.send(embed=embed, view=TicketOpenView())
        await interaction.response.send_message("✅ Destek paneli başarıyla oluşturuldu!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
