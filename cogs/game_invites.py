# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger("AlaCafeBot.GameInvites")

GAME_TEMPLATES = {
    "bazaar": {
        "title": "🃏 The Bazaar Masası Kuruldu!",
        "color": discord.Color.purple(),
        "icon": "https://images.emojiterra.com/twitter/v14.0/512px/1f0cf.png",
        "default_msg": "Ortak seni **The Bazaar**'a davet ediyorlar! Bence acil gelmen lazım, çok eğlenirsin hem masada herkes var ortak, haydi bakalım kartları diziyoruz! 🎲🃏"
    },
    "cs": {
        "title": "💣 Counter-Strike 2 Ekibi Toplandı!",
        "color": discord.Color.gold(),
        "icon": "https://images.emojiterra.com/twitter/v14.0/512px/1f52b.png",
        "default_msg": "Ortak seni **CS2**'ye çağırıyorlar! Silahları kuşandık, bomba alanında sensiz bir kişi eksiğiz ortak, acil drop lazım haydi bakalım koş gel! 🔫🔥"
    },
    "lol": {
        "title": "⚔️ League of Legends Vadi Çağrısı!",
        "color": discord.Color.blue(),
        "icon": "https://images.emojiterra.com/twitter/v14.0/512px/2694.png",
        "default_msg": "Ortak seni vadiye **LoL**'e çağırıyorlar! Ejder bekliyor, koridorlar sensiz sahipsiz kaldı, bence hemen gelmen lazım ortak haydi bakalım! 🛡️⚡"
    },
    "sezai": {
        "title": "☕ Sezai Özel Muhabbet Masası!",
        "color": discord.Color.from_rgb(230, 126, 34),
        "icon": "https://images.emojiterra.com/twitter/v14.0/512px/2615.png",
        "default_msg": "Ortak seni **Sezai** masasına çağırıyorlar! Masada ortam alev aldı, çaylar tazelendi, sensiz muhabbetin tadı tuzu yok ortak haydi bakalım koş gel! ☕💨"
    }
}

async def send_game_invite(interaction: discord.Interaction, target: discord.Member, game_key: str, custom_name: str = None, extra_note: str = None):
    inviter = interaction.user
    guild = interaction.guild

    if target.id == inviter.id:
        await interaction.response.send_message("❌ Kendine davet gönderemezsin kral, masadaki arkadaşını çağır!", ephemeral=True)
        return

    if target.bot:
        await interaction.response.send_message("❌ Botlara davet gönderemezsin.", ephemeral=True)
        return

    # Oyun şablonunu belirle
    template = GAME_TEMPLATES.get(game_key)
    if not template:
        game_title = f"🎮 {custom_name.title()} Oyun Daveti!"
        game_desc = f"Ortak seni **{custom_name}** oynamaya davet ediyorlar! Bence gelmen lazım çok eğlenirsin hem herkes masada ortak, haydi bakalım! 🎯"
        color = discord.Color.teal()
        icon = "https://images.emojiterra.com/twitter/v14.0/512px/1f3ae.png"
    else:
        game_title = template["title"]
        game_desc = template["default_msg"]
        color = template["color"]
        icon = template["icon"]

    # Ses odası bilgisi (Eğer davet eden sesteyse)
    voice_info = ""
    if inviter.voice and inviter.voice.channel:
        voice_info = f"\n📍 **Şu An Bulunduğumuz Masa:** `{inviter.voice.channel.name}`"

    note_info = f"\n📝 **Özel Not:** *\"{extra_note}\"*" if extra_note else ""

    # Özel DM Embed Kartı
    dm_embed = discord.Embed(
        title=game_title,
        description=f"{game_desc}\n{voice_info}{note_info}",
        color=color
    )
    if guild.icon:
        dm_embed.set_author(name=f"{guild.name} • Ala Lounge", icon_url=guild.icon.url)
    else:
        dm_embed.set_author(name=f"{guild.name} • Ala Lounge")
    dm_embed.set_thumbnail(url=icon)
    dm_embed.add_field(name="👑 Davet Eden Ortak", value=inviter.mention, inline=True)
    dm_embed.add_field(name="🏰 Sunucu", value=f"**{guild.name}**", inline=True)
    dm_embed.set_footer(text="Ala Lounge • Hızlı Oyun Çağrı Servisi")

    # DM Göndermeyi Dene
    try:
        await target.send(embed=dm_embed)
        # Kanala başarı mesajı
        embed_success = discord.Embed(
            title="📨 Oyun Daveti Özelden (DM) Gönderildi!",
            description=f"🎉 **{target.mention}** adlı ortağa özelden **{custom_name or game_key.upper()}** daveti iletildi!\n\n*(Masada yerini ayırdık, gelmesini bekliyoruz).* ☕",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed_success)
        logger.info(f"Oyun daveti gönderildi: {inviter.display_name} -> {target.display_name} ({game_key})")

    except discord.Forbidden:
        # Üyenin DM'si kapalıysa kanaldan açık davet at
        embed_fail = discord.Embed(
            title=f"⚠️ {target.display_name} üyesinin DM kutusu kapalı!",
            description=(
                f"Özel mesaj ayarları kapalı olduğu için DM iletilemedi, buradan sesleniyoruz:\n\n"
                f"📢 {target.mention} **{game_desc}**{voice_info}{note_info}"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(content=f"{target.mention} masaya çağrılıyorsun!", embed=embed_fail)
    except Exception as e:
        await interaction.response.send_message(f"❌ Davet gönderilirken hata oluştu: {e}", ephemeral=True)

class GameInvitesCog(commands.Cog, name="Oyun Davetleri"):
    """DM Üzerinden Özel Oyun ve Masa Davetleri"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bazaar", description="Bir arkadaşına DM'den The Bazaar daveti gönderir!")
    @app_commands.describe(kullanici="Kimi davet etmek istiyorsun?", not_ekle="Varsa özel mesajın")
    async def cmd_bazaar(self, interaction: discord.Interaction, kullanici: discord.Member, not_ekle: str = None):
        await send_game_invite(interaction, kullanici, "bazaar", "The Bazaar", not_ekle)

    @app_commands.command(name="cs", description="Bir arkadaşına DM'den CS2 daveti gönderir!")
    @app_commands.describe(kullanici="Kimi davet etmek istiyorsun?", not_ekle="Varsa özel mesajın")
    async def cmd_cs(self, interaction: discord.Interaction, kullanici: discord.Member, not_ekle: str = None):
        await send_game_invite(interaction, kullanici, "cs", "Counter-Strike 2", not_ekle)

    @app_commands.command(name="lol", description="Bir arkadaşına DM'den League of Legends daveti gönderir!")
    @app_commands.describe(kullanici="Kimi davet etmek istiyorsun?", not_ekle="Varsa özel mesajın")
    async def cmd_lol(self, interaction: discord.Interaction, kullanici: discord.Member, not_ekle: str = None):
        await send_game_invite(interaction, kullanici, "lol", "League of Legends", not_ekle)

    @app_commands.command(name="sezai", description="Bir arkadaşına DM'den Sezai masası daveti gönderir!")
    @app_commands.describe(kullanici="Kimi davet etmek istiyorsun?", not_ekle="Varsa özel mesajın")
    async def cmd_sezai(self, interaction: discord.Interaction, kullanici: discord.Member, not_ekle: str = None):
        await send_game_invite(interaction, kullanici, "sezai", "Sezai Masası", not_ekle)

    @app_commands.command(name="oyun", description="İstediğin herhangi bir oyun için arkadaşına DM'den davet at!")
    @app_commands.describe(oyun_adi="Hangi oyun? (Örn: GTA V, Valorant, FIFA...)", kullanici="Kimi davet etmek istiyorsun?", not_ekle="Varsa özel mesajın")
    async def cmd_oyun(self, interaction: discord.Interaction, oyun_adi: str, kullanici: discord.Member, not_ekle: str = None):
        await send_game_invite(interaction, kullanici, "custom", oyun_adi, not_ekle)

async def setup(bot):
    await bot.add_cog(GameInvitesCog(bot))
