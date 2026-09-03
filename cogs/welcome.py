# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_CAFE
import database as db
import logging

logger = logging.getLogger("AlaCafeBot.Welcome")

DEFAULT_WELCOME_CHANNEL_ID = 1112407824539070475

class WelcomeCog(commands.Cog, name="Karsilama"):
    def __init__(self, bot):
        self.bot = bot

    async def send_welcome_package(self, member: discord.Member, target_channel: discord.TextChannel = None):
        """Hem sunucu kanalına hem de özelden DM olarak karşılama paketi gönderir."""
        guild = member.guild
        settings = db.get_guild_settings(guild.id)
        customs = db.get_customizations()

        # 1. SUNUCU KANALINA GÖNDERME
        ch = target_channel
        if not ch:
            target_id = settings.get("welcome_channel_id") or DEFAULT_WELCOME_CHANNEL_ID
            ch = guild.get_channel(int(target_id))
            if not ch:
                try:
                    ch = await guild.fetch_channel(int(target_id))
                except Exception:
                    ch = None

        if ch and ch.permissions_for(guild.me).send_messages:
            raw_title = customs.get("welcome_title", "☕ Ala Lounge & Cafe'ye Hoş Geldiniz!")
            raw_msg = customs.get("welcome_message", "{kullanici}, **Ala Lounge & Cafe** masamıza teşrif ettin! Masalarda yerini alabilir, nargileni söyleyebilir veya sohbete katılabilirsin.")

            proc_title = raw_title.replace("{kullanici}", member.display_name).replace("{sunucu}", guild.name).replace("{uye_sayisi}", str(guild.member_count))
            proc_msg = raw_msg.replace("{kullanici}", member.mention).replace("{kullanici_adi}", member.display_name).replace("{sunucu}", guild.name).replace("{uye_sayisi}", str(guild.member_count))

            embed = discord.Embed(
                title=proc_title,
                description=proc_msg,
                color=COLOR_CAFE
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Sunucumuzun {guild.member_count}. üyesisin! • Ala Lounge")
            try:
                await ch.send(content=f"🎉 {member.mention} kapıdan içeri girdi! Hoş geldin ortak!", embed=embed)
                logger.info(f"Karşılama mesajı kanala gönderildi (#{ch.name}): {member.name}")
            except Exception as e:
                logger.error(f"Kanala karşılama mesajı atılamadı: {e}")
        else:
            logger.warning(f"Karşılama kanalı bulunamadı veya yetki yok! Hedef ID: {DEFAULT_WELCOME_CHANNEL_ID}")

        # 2. ÖZELDEN (DM) GÖNDERME
        try:
            dm_embed = discord.Embed(
                title="☕ Ala Lounge & Cafe'ye Hoş Geldin Ortak!",
                description=(
                    f"Selam **{member.display_name}**! **{guild.name}** sunucumuza teşrif ettiğin için çok mutlu olduk! 🎉\n\n"
                    "📍 **Burada Neler Var?**\n"
                    "• `➕ Masa Aç` ses kanalına girerek arkadaşlarınla sana özel sanal masa kurabilirsin.\n"
                    "• `/ziya` yazarak bilge ortağımız Ziya ile sohbet edebilir, akıl alabilirsin.\n"
                    "• `/oynat` ile müzik dinleyebilir veya `/bazaar`, `/cs`, `/lol` ile arkadaşlarını oyuna davet edebilirsin.\n\n"
                    "Keyifli vakitler dileriz, masada yerin hazır! ☕💨🎲"
                ),
                color=COLOR_CAFE
            )
            if guild.icon:
                dm_embed.set_thumbnail(url=guild.icon.url)
            dm_embed.set_footer(text="Ala Lounge • Esnaf samimiyeti, profesyonel ortam")
            await member.send(embed=dm_embed)
            logger.info(f"Özel DM karşılama mesajı başarıyla iletildi: {member.name}")
        except discord.Forbidden:
            logger.warning(f"{member.name} kullanıcısının DM'leri kapalı olduğu için özel mesaj iletilemedi.")
        except Exception as e:
            logger.error(f"DM gönderme hatası ({member.name}): {e}")

        # 3. OTOMATİK ROL ATAMA
        auto_role_id = settings.get("auto_role_id")
        if auto_role_id:
            role = guild.get_role(int(auto_role_id))
            if role and guild.me.guild_permissions.manage_roles:
                try:
                    await member.add_roles(role)
                    logger.info(f"Otorol verildi ({role.name}): {member.name}")
                except Exception as e:
                    logger.error(f"Otorol verilemedi: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"Sunucuya yeni üye katıldı: {member.name} ({member.id})")
        await self.send_welcome_package(member)

    @app_commands.command(name="hosgeldin-test", description="Karşılama sistemini test eder (hem kanala hem DM'ye mesaj atar)")
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_test_welcome(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self.send_welcome_package(interaction.user, target_channel=interaction.channel)
        await interaction.followup.send("✅ Karşılama paketi başarıyla test edildi! Hem bu kanala kart atıldı hem de sana özelden DM gönderildi.", ephemeral=True)

    @app_commands.command(name="ayar-hosgeldin", description="Karşılama mesajının atılacağı kanalı ayarlar")
    @app_commands.describe(kanal="Karşılama kanalı")
    @app_commands.checks.has_permissions(administrator=True)
    async def ayar_hosgeldin_cmd(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        db.set_guild_setting(interaction.guild_id, "welcome_channel_id", kanal.id)
        await interaction.response.send_message(f"✅ Karşılama kanalı {kanal.mention} (ID: `{kanal.id}`) olarak ayarlandı!", ephemeral=True)

    @app_commands.command(name="ayar-otorol", description="Yeni katılan üyelere verilecek varsayılan rolü ayarlar")
    @app_commands.describe(rol="Otomatik verilecek rol")
    @app_commands.checks.has_permissions(administrator=True)
    async def ayar_otorol_cmd(self, interaction: discord.Interaction, rol: discord.Role):
        db.set_guild_setting(interaction.guild_id, "auto_role_id", rol.id)
        await interaction.response.send_message(f"✅ Otomatik üye rolü **{rol.name}** olarak ayarlandı!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
