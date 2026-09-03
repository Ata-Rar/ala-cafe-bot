# -*- coding: utf-8 -*-
import random
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_CAFE, COLOR_INFO
import database as db

class UtilityCog(commands.Cog, name="Araçlar"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sunucu-bilgi", description="Sunucu istatistiklerini ve bilgilerini görüntüler")
    async def sunucu_bilgi(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"🏰 {guild.name} — Sunucu İncelemesi", color=COLOR_INFO)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Sunucu Sahibi", value=f"{guild.owner.mention}", inline=True)
        embed.add_field(name="👥 Toplam Üye", value=f"**{guild.member_count}** Kişi", inline=True)
        embed.add_field(name="💬 Metin Kanalları", value=f"**{len(guild.text_channels)}**", inline=True)
        embed.add_field(name="🔊 Ses Kanalları", value=f"**{len(guild.voice_channels)}**", inline=True)
        embed.add_field(name="🛡️ Rol Sayısı", value=f"**{len(guild.roles)}**", inline=True)
        embed.add_field(name="📅 Kuruluş Tarihi", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)

        embed.set_footer(text="Ala Cafe • Güvenli ve Samimi Sunucu")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profil", description="Kullanıcının sunucu kimlik kartını ve yönetim/VIP durumunu görüntüler")
    @app_commands.describe(kullanici="Kimin profiline bakmak istiyorsun?")
    async def profil_cmd(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        target = kullanici or interaction.user
        vips = await db.get_vips()
        vip_info = next((v for v in vips if v["user_id"] == target.id), None)

        color = COLOR_INFO
        unvan_text = "Üye"
        if vip_info:
            unvan_text = f"👑 **{vip_info['title']}**"
        elif target.guild_permissions.administrator:
            unvan_text = "🛡️ **Sunucu Yöneticisi**"
        elif target.top_role.name != "@everyone":
            unvan_text = f"⭐ **{target.top_role.name}**"

        embed = discord.Embed(title=f"🪪 {target.display_name} — Sunucu Kimlik Kartı", color=color)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🎖️ Statü / Unvan", value=unvan_text, inline=False)
        embed.add_field(name="🆔 Discord ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="📅 Sunucuya Giriş", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🎂 Hesap Oluşturma", value=f"<t:{int(target.created_at.timestamp())}:D>", inline=True)

        # Rolleri listele (en fazla 5 rol)
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        if roles:
            embed.add_field(name="🎭 Rolleri", value=" • ".join(roles[:6]), inline=False)

        if vip_info and vip_info.get("notes"):
            embed.add_field(name="📝 Protokol Notu", value=f"_{vip_info['notes']}_", inline=False)

        embed.set_footer(text="Ala Lounge • Güvenli Sunucu Kimliği")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="anket", description="Sunucuda butonlu hızlı oylama başlatır")
    @app_commands.describe(soru="Oylanacak soru", secenek1="1. Seçenek", secenek2="2. Seçenek")
    async def anket_cmd(self, interaction: discord.Interaction, soru: str, secenek1: str = "Evet 👍", secenek2: str = "Hayır 👎"):
        embed = discord.Embed(
            title="📊 Sunucu Anketi",
            description=f"**Soru:**\n> {soru}\n\n1️⃣ {secenek1}\n2️⃣ {secenek2}",
            color=COLOR_CAFE
        )
        embed.set_footer(text=f"{interaction.user.display_name} tarafından başlatıldı")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")

    @app_commands.command(name="zar", description="Şans zarı atar (1-100)")
    async def zar_cmd(self, interaction: discord.Interaction):
        sonuc = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 {interaction.user.mention} zar attı: **{sonuc}** geldi!")

    @app_commands.command(name="yazitura", description="Yazı-tura atar")
    async def yazitura_cmd(self, interaction: discord.Interaction):
        sonuc = random.choice(["Yazı 🪙", "Tura 👑"])
        await interaction.response.send_message(f"🪙 Madeni para havaya atıldı: **{sonuc}**!")

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
