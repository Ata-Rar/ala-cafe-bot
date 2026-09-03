# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_GOLD, COLOR_SUCCESS, COLOR_ERROR
import database as db

class ManagementCog(commands.Cog, name="Yonetim"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="yonetim-ekle", description="Sunucu yönetim kadrosuna veya VIP listesine yeni bir isim ekler")
    @app_commands.describe(kullanici="Listeye eklenecek üye", unvan="Görev / Unvan (Örn: Patron, Kurucu, Baş Nargileci, VIP Misafir)", notlar="Ek açıklamalar")
    @app_commands.checks.has_permissions(administrator=True)
    async def yonetim_ekle(self, interaction: discord.Interaction, kullanici: discord.Member, unvan: str, notlar: str = ""):
        await db.add_vip(kullanici.id, kullanici.display_name, unvan, notlar)
        embed = discord.Embed(
            title="👑 Yönetim & VIP Kadrosuna Eklendi",
            description=(
                f"**Kullanıcı:** {kullanici.mention} ({kullanici.name})\n"
                f"**Unvan:** `{unvan}`\n"
                f"**Notlar:** {notlar or '_Belirtilmedi_'}\n\n"
                f"✅ Kişi botun veritabanına ve **Masaüstü Kontrol Paneli**'ne kaydedildi."
            ),
            color=COLOR_GOLD
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="yonetim-sil", description="Kullanıcıyı yönetim ve VIP listesinden çıkarır")
    @app_commands.describe(kullanici="Listeden çıkarılacak üye")
    @app_commands.checks.has_permissions(administrator=True)
    async def yonetim_sil(self, interaction: discord.Interaction, kullanici: discord.Member):
        await db.remove_vip(kullanici.id)
        await interaction.response.send_message(f"🗑️ {kullanici.mention} yönetim ve VIP listesinden kaldırıldı.", ephemeral=True)

    @app_commands.command(name="yonetim-liste", description="Ala Lounge yönetim ve VIP kadrosunu görüntüler")
    async def yonetim_liste(self, interaction: discord.Interaction):
        vips = await db.get_vips()
        if not vips:
            await interaction.response.send_message("📋 Henüz kayıtlı yönetim veya VIP üyesi bulunmuyor. `/yonetim-ekle` ile ekleyebilirsiniz.", ephemeral=True)
            return

        embed = discord.Embed(
            title="👑 Ala Lounge & Cafe — Yönetim ve VIP Kadrosu",
            description="Sunucumuzun kritik isimleri ve görev dağılımı:\n",
            color=COLOR_GOLD
        )
        for v in vips:
            member = interaction.guild.get_member(v["user_id"])
            tag = member.mention if member else f"**{v['name']}**"
            field_val = f"🎖️ **Unvan:** {v['title']}\n📅 **Kayıt:** `{v['added_at']}`"
            if v.get("notes"):
                field_val += f"\n📝 **Not:** _{v['notes']}_"
            embed.add_field(name=f"⭐ {v['name']}", value=field_val, inline=False)

        embed.set_footer(text="Ala Cafe • Protokol & Yönetim Masası")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ManagementCog(bot))
