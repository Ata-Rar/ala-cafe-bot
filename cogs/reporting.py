# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import database
import io
import time
from datetime import datetime
import logging

logger = logging.getLogger("AlaCafeBot.Reporting")

class ReportActionView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="📄 Tam Komut Dökümünü İndir (.txt)", style=discord.ButtonStyle.primary, emoji="📥", custom_id="btn_download_cmd_report")
    async def btn_download_cmd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logs = database.get_all_command_logs_full()
        if not logs:
            await interaction.followup.send("❌ Henüz kaydedilmiş komut günlüğü bulunmuyor.", ephemeral=True)
            return

        lines = [
            "=" * 90,
            f"  ALA CAFE & LOUNGE — TAM KOMUT & AKTİVİTE DENETİM RAPORU",
            f"  Sunucu: {self.guild.name} (ID: {self.guild.id})",
            f"  Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Toplam Kayıt: {len(logs)} adet komut",
            "=" * 90 + "\n"
        ]

        for r in logs:
            lines.append(f"[{r['executed_at']}] Üye: {r['user_name']} (ID: {r['user_id']})")
            lines.append(f"  Komut  : /{r['command_name']}")
            lines.append(f"  Detay  : {r['command_args']}")
            lines.append(f"  Kanal  : #{r['channel_name']}")
            lines.append("-" * 90)

        report_txt = "\n".join(lines)
        file = discord.File(io.BytesIO(report_txt.encode("utf-8")), filename=f"tam_komut_raporu_{int(time.time())}.txt")
        await interaction.followup.send(content="✅ **Tam komut döküm dosyanız hazırlandı:**", file=file, ephemeral=True)

    @discord.ui.button(label="🎫 Destek Konuşmalarını İndir (.txt)", style=discord.ButtonStyle.success, emoji="📜", custom_id="btn_download_ticket_report")
    async def btn_download_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        tickets = database.get_all_tickets()
        if not tickets:
            await interaction.followup.send("❌ Henüz açılmış/kapanmış bir destek talebi bulunmuyor.", ephemeral=True)
            return

        lines = [
            "=" * 90,
            f"  ALA CAFE & LOUNGE — DESTEK TALEPLERİ VE KONUŞMA DÖKÜMLERİ",
            f"  Sunucu: {self.guild.name} (ID: {self.guild.id})",
            f"  Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Toplam Bilet: {len(tickets)} adet",
            "=" * 90 + "\n"
        ]

        for t in tickets:
            lines.append(f"🎫 TALEP: #{t['ticket_name']} (Durum: {t['status']})")
            lines.append(f"  Açan Kişi   : {t['user_name']} (ID: {t['user_id']})")
            lines.append(f"  Açılış      : {t['opened_at']}")
            lines.append(f"  Kapanış     : {t.get('closed_at') or 'Hala Açık'}")
            lines.append(f"  Kapatan     : {t.get('closed_by') or '-'}")
            lines.append("--- KONUŞMA METNİ ---")
            lines.append(t.get('transcript_text') or "Bu talepte henüz kaydedilmiş metin bulunmuyor.")
            lines.append("=" * 90 + "\n")

        ticket_txt = "\n".join(lines)
        file = discord.File(io.BytesIO(ticket_txt.encode("utf-8")), filename=f"destek_konusmalari_{int(time.time())}.txt")
        await interaction.followup.send(content="✅ **Destek konuşmaları arşivi hazırlandı:**", file=file, ephemeral=True)

class ReportingCog(commands.Cog, name="Raporlama"):
    """Sunucu Aktivite, Komut Kullanım ve Bilet Denetim Sistemi"""

    def __init__(self, bot):
        self.bot = bot

    # 1. TÜM SLASH KOMUTLARINI OTOMATİK DİNLE VE KAYDET
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command):
        try:
            user = interaction.user
            guild_id = interaction.guild_id or 0
            channel_name = interaction.channel.name if interaction.channel else "Bilinmeyen"
            
            # Parametreleri toparla
            args_dict = {}
            if interaction.data and "options" in interaction.data:
                for opt in interaction.data["options"]:
                    args_dict[opt.get("name")] = opt.get("value")
            
            args_str = ", ".join([f"{k}: {v}" for k, v in args_dict.items()]) if args_dict else "Parametresiz"
            
            database.log_command(
                user_id=user.id,
                user_name=user.display_name,
                command_name=command.name,
                command_args=args_str,
                channel_name=channel_name,
                guild_id=guild_id
            )
        except Exception as e:
            logger.error(f"Slash komut loglama hatası: {e}")

    # 2. PREFIX KOMUTLARINI DA DİNLE VE KAYDET
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        try:
            channel_name = ctx.channel.name if ctx.channel else "Bilinmeyen"
            guild_id = ctx.guild.id if ctx.guild else 0
            args_str = ctx.message.clean_content.replace(f"{ctx.prefix}{ctx.command.name}", "").strip() or "Parametresiz"

            database.log_command(
                user_id=ctx.author.id,
                user_name=ctx.author.display_name,
                command_name=ctx.command.name,
                command_args=args_str,
                channel_name=channel_name,
                guild_id=guild_id
            )
        except Exception as e:
            logger.error(f"Prefix komut loglama hatası: {e}")

    # 3. /rapor MASTER DENETİM KOMUTU
    @app_commands.command(name="rapor", description="Sunucudaki tüm bot aktivitelerini, en çok kullananları ve destek taleplerini döker!")
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_report(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        # İstatistikleri Çek
        top_users = database.get_top_command_users(limit=5)
        top_commands = database.get_top_commands(limit=5)
        recent_logs = database.get_recent_command_logs(limit=6)
        all_tickets = database.get_all_tickets()

        open_tickets = [t for t in all_tickets if t.get("status") == "AÇIK"]
        closed_tickets = [t for t in all_tickets if t.get("status") == "KAPALI"]

        embed = discord.Embed(
            title="📊 Ala Lounge — Master Aktivite & Denetim Raporu",
            description="Sunucudaki tüm bot komutları, en aktif üyeler ve destek konuşmalarının canlı dökümü:",
            color=discord.Color.gold()
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        # 👑 En Çok Kullananlar
        if top_users:
            user_lines = [f"**{i+1}.** `{u['user_name']}` — **{u['cmd_count']} komut**" for i, u in enumerate(top_users)]
            embed.add_field(name="👑 En Çok Bot Kullananlar (Top 5)", value="\n".join(user_lines), inline=False)
        else:
            embed.add_field(name="👑 En Çok Bot Kullananlar", value="*Henüz kaydedilmiş veri yok.*", inline=False)

        # ⚡ En Çok Kullanılan Komutlar
        if top_commands:
            cmd_lines = [f"**{i+1}.** `/{c['command_name']}` — **{c['use_count']} kez**" for i, c in enumerate(top_commands)]
            embed.add_field(name="⚡ En Popüler Komutlar (Top 5)", value="\n".join(cmd_lines), inline=True)

        # 🎫 Destek Biletleri Durumu
        ticket_summary = f"🟢 **Açık Talepler:** {len(open_tickets)} adet\n🔒 **Kapatılan / Arşiv:** {len(closed_tickets)} adet"
        embed.add_field(name="🎫 Destek Talepleri", value=ticket_summary, inline=True)

        # 🕒 Son Komut Akışı (Kim ne yazmış?)
        if recent_logs:
            log_lines = []
            for r in recent_logs:
                t_short = r['executed_at'].split(" ")[1][:5]
                log_lines.append(f"• `[{t_short}]` **{r['user_name']}** -> `/{r['command_name']}` *({r['command_args'][:35]}...)*")
            embed.add_field(name="🕒 Son Komut Hareketleri (Canlı Log)", value="\n".join(log_lines), inline=False)

        embed.set_footer(text="Ala Lounge • Yönetim & Denetim Sistemi | Butonlara basarak tam dökümleri indirebilirsiniz")

        view = ReportActionView(guild=interaction.guild)
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ReportingCog(bot))
