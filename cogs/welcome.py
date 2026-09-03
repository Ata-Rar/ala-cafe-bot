# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_CAFE, COLOR_SUCCESS
import database as db

class WelcomeCog(commands.Cog, name="Karsilama"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = await db.get_guild_settings(member.guild.id)
        customs = await db.get_customizations()

        channel_id = settings.get("welcome_channel_id")
        channel = None
        if channel_id:
            channel = member.guild.get_channel(channel_id)
        if not channel:
            # Otomatik uygun metin kanalı bul
            for ch_name in ["hoş-geldiniz", "hos-geldiniz", "gelen-giden", "genel", "sohbet", "chat"]:
                ch = discord.utils.get(member.guild.text_channels, name=ch_name)
                if ch and ch.permissions_for(member.guild.me).send_messages:
                    channel = ch
                    break

        # Otomatik rol atama
        auto_role_id = settings.get("auto_role_id")
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role and member.guild.me.guild_permissions.manage_roles:
                try:
                    await member.add_roles(role)
                except Exception:
                    pass

        if channel:
            # Panelden girilen dinamik metin şablonunu işle
            raw_title = customs.get("welcome_title", "☕ Ala Lounge'a Hoş Geldiniz!")
            raw_msg = customs.get("welcome_message", "Aramıza hoş geldin {kullanici}!")

            processed_title = raw_title.replace("{kullanici}", member.display_name).replace("{sunucu}", member.guild.name).replace("{uye_sayisi}", str(member.guild.member_count))
            processed_msg = raw_msg.replace("{kullanici}", member.mention).replace("{kullanici_adi}", member.display_name).replace("{sunucu}", member.guild.name).replace("{uye_sayisi}", str(member.guild.member_count))

            embed = discord.Embed(
                title=processed_title,
                description=processed_msg,
                color=COLOR_CAFE
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Sunucunun {member.guild.member_count}. üyesisin! • Ala Lounge")
            await channel.send(content=f"🎉 {member.mention} kapıdan içeri girdi!", embed=embed)

    @app_commands.command(name="ayar-hosgeldin", description="Karşılama mesajının atılacağı kanalı ayarlar")
    @app_commands.describe(kanal="Karşılama kanalı")
    @app_commands.checks.has_permissions(administrator=True)
    async def ayar_hosgeldin_cmd(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        await db.set_guild_setting(interaction.guild_id, "welcome_channel_id", kanal.id)
        await interaction.response.send_message(f"✅ Karşılama kanalı {kanal.mention} olarak ayarlandı!", ephemeral=True)

    @app_commands.command(name="ayar-otorol", description="Yeni katılan üyelere verilecek varsayılan rolü ayarlar")
    @app_commands.describe(rol="Otomatik verilecek rol")
    @app_commands.checks.has_permissions(administrator=True)
    async def ayar_otorol_cmd(self, interaction: discord.Interaction, rol: discord.Role):
        await db.set_guild_setting(interaction.guild_id, "auto_role_id", rol.id)
        await interaction.response.send_message(f"✅ Otomatik üye rolü **{rol.name}** olarak ayarlandı!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
