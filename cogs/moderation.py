# -*- coding: utf-8 -*-
from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_CAFE
import database as db

class ModerationCog(commands.Cog, name="Moderasyon"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="temizle", description="Kanaldan belirtilen sayıda mesajı siler")
    @app_commands.describe(sayi="Silinecek mesaj sayısı (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def temizle_cmd(self, interaction: discord.Interaction, sayi: int):
        if sayi < 1 or sayi > 100:
            await interaction.response.send_message("❌ 1 ile 100 arasında bir sayı girmelisin.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=sayi)
        await interaction.followup.send(f"🧹 **{len(deleted)}** adet mesaj temizlendi!", ephemeral=True)

    @app_commands.command(name="sustur", description="Belirtilen üyeyi geçici olarak susturur (Timeout)")
    @app_commands.describe(kullanici="Susturulacak üye", dakika="Kaç dakika susturulsun?", sebep="Susturma sebebi")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def sustur_cmd(self, interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Belirtilmedi"):
        if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Senden üst veya eşit yetkideki birini susturamazsın.", ephemeral=True)
            return

        duration = timedelta(minutes=dakika)
        await kullanici.timeout(duration, reason=sebep)
        await db.add_warn(kullanici.id, interaction.guild_id, interaction.user.id, f"Susturuldu ({dakika} dk): {sebep}")

        embed = discord.Embed(
            title="🔇 Üye Susturuldu",
            description=f"{kullanici.mention} kullanıcısı **{dakika} dakika** boyunca susturuldu.\n**Sebep:** {sebep}\n**Yetkili:** {interaction.user.mention}",
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sustur-kaldir", description="Üyenin susturmasını kaldırır")
    @app_commands.describe(kullanici="Susturması kaldırılacak üye")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def sustur_kaldir_cmd(self, interaction: discord.Interaction, kullanici: discord.Member):
        await kullanici.timeout(None, reason="Yetkili susturmayı kaldırdı")
        await interaction.response.send_message(f"🔊 {kullanici.mention} üyesinin susturması kaldırıldı.", ephemeral=True)

    @app_commands.command(name="at", description="Üyeyi sunucudan atar (Kick)")
    @app_commands.describe(kullanici="Atılacak üye", sebep="Atılma sebebi")
    @app_commands.checks.has_permissions(kick_members=True)
    async def at_cmd(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Belirtilmedi"):
        if kullanici.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Bu üyeyi atma yetkiniz yok.", ephemeral=True)
            return

        await kullanici.kick(reason=sebep)
        await interaction.response.send_message(f"👢 {kullanici.mention} sunucudan atıldı. (Sebep: {sebep})")

    @app_commands.command(name="yasakla", description="Üyeyi sunucudan yasaklar (Ban)")
    @app_commands.describe(kullanici="Yasaklanacak üye", sebep="Yasaklama sebebi")
    @app_commands.checks.has_permissions(ban_members=True)
    async def yasakla_cmd(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Belirtilmedi"):
        if kullanici.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Bu üyeyi yasaklama yetkiniz yok.", ephemeral=True)
            return

        await kullanici.ban(reason=sebep)
        await interaction.response.send_message(f"🔨 {kullanici.mention} sunucudan kalıcı olarak yasaklandı! (Sebep: {sebep})")

    @app_commands.command(name="uyar", description="Üyeye resmi uyarı verir ve siciline işler")
    @app_commands.describe(kullanici="Uyarılacak üye", sebep="Uyarı sebebi")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def uyar_cmd(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
        await db.add_warn(kullanici.id, interaction.guild_id, interaction.user.id, sebep)
        warns = await db.get_warns(kullanici.id, interaction.guild_id)

        embed = discord.Embed(
            title="⚠️ Üye Uyarıldı",
            description=(
                f"**Kullanıcı:** {kullanici.mention}\n"
                f"**Sebep:** {sebep}\n"
                f"**Yetkili:** {interaction.user.mention}\n"
                f"**Toplam Uyarı:** `{len(warns)}`"
            ),
            color=COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uyarilar", description="Üyenin geçmiş uyarılarını görüntüler")
    @app_commands.describe(kullanici="Uyarısına bakılacak üye")
    async def uyarilar_cmd(self, interaction: discord.Interaction, kullanici: discord.Member):
        warns = await db.get_warns(kullanici.id, interaction.guild_id)
        if not warns:
            await interaction.response.send_message(f"✅ {kullanici.mention} kullanıcısının tertemiz bir sicili var, uyarısı yok!", ephemeral=True)
            return

        embed = discord.Embed(title=f"📋 {kullanici.display_name} — Ceza Sicili ({len(warns)} Uyarı)", color=COLOR_CAFE)
        for w in warns[:10]:
            mod = interaction.guild.get_member(w["mod_id"])
            mod_name = mod.display_name if mod else f"ID: {w['mod_id']}"
            embed.add_field(name=f"📅 {w['timestamp']}", value=f"**Sebep:** {w['reason']}\n**Yetkili:** {mod_name}", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
