# -*- coding: utf-8 -*-
import asyncio
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
    },
    "ziya": {
        "title": "☕ Ziya Ortak Masası Toplandı!",
        "color": discord.Color.dark_teal(),
        "icon": "https://images.emojiterra.com/twitter/v14.0/512px/2615.png",
        "default_msg": "Ortak seni **Ziya** masasına çağırıyorlar! Masada ortam alev aldı, demli çaylar geldi, sensiz muhabbet dönmüyor ortak haydi koş gel! ☕🔥"
    }
}

async def send_bulk_invites(
    interaction_or_ctx,
    initial_targets: list[discord.Member],
    game_key: str,
    custom_name: str = None,
    extra_note: str = None,
    role: discord.Role = None
):
    is_slash = isinstance(interaction_or_ctx, discord.Interaction)
    inviter = interaction_or_ctx.user if is_slash else interaction_or_ctx.author
    guild = interaction_or_ctx.guild
    channel = interaction_or_ctx.channel

    if is_slash:
        await interaction_or_ctx.response.defer()

    async def _respond(content=None, embed=None, ephemeral=False):
        if is_slash:
            return await interaction_or_ctx.followup.send(content=content, embed=embed, ephemeral=ephemeral)
        else:
            return await channel.send(content=content, embed=embed)

    targets = list(initial_targets) if initial_targets else []

    # Eğer rol verildiyse o roldeki tüm üyeleri ekle
    if role:
        for m in role.members:
            if m not in targets:
                targets.append(m)

    # Botları ve davet edenin kendisini çıkar, tekrarları temizle
    filtered_targets = []
    for t in targets:
        if t and not t.bot and t.id != inviter.id and t not in filtered_targets:
            filtered_targets.append(t)

    if not filtered_targets:
        await _respond("❌ Davet edilecek geçerli bir ortak bulunamadı! (Botlar ve kendi hesabın hariç tutulur)", ephemeral=True)
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

    sent_dm = []
    failed_dm = []

    for target in filtered_targets:
        try:
            await target.send(embed=dm_embed)
            sent_dm.append(target)
            logger.info(f"Oyun daveti gönderildi: {inviter.display_name} -> {target.display_name} ({game_key})")
        except discord.Forbidden:
            failed_dm.append(target)
        except Exception as e:
            logger.error(f"Davet gönderme hatası ({target.display_name}): {e}")
            failed_dm.append(target)
        await asyncio.sleep(0.2)

    # DM kutusu kapalı olanlara kanaldan açık seslen
    if failed_dm:
        mentions_str = " ".join([t.mention for t in failed_dm])
        embed_fail = discord.Embed(
            title=f"⚠️ {len(failed_dm)} Ortağın DM Kutusu Kapalı!",
            description=(
                f"Özel mesajları kapalı olduğu için buradan sesleniyoruz:\n\n"
                f"📢 {mentions_str} **{game_desc}**{voice_info}{note_info}"
            ),
            color=discord.Color.gold()
        )
        await channel.send(content=f"{mentions_str} masaya çağrılıyorsunuz!", embed=embed_fail)

    # Kanala Toplu Rapor Embed Kartı
    total_count = len(sent_dm) + len(failed_dm)
    display_game = custom_name or game_key.upper()
    embed_report = discord.Embed(
        title=f"📨 Toplu Oyun Daveti Gönderildi! ({display_game})",
        description=f"🎉 Toplam **{total_count}** ortağa **{display_game}** çağrısı iletildi!\n*(Masada yerler ayrıldı, ortaklar bekleniyor).* ☕",
        color=color
    )
    if sent_dm:
        embed_report.add_field(
            name=f"✅ Özelden (DM) Ulaşanlar ({len(sent_dm)})",
            value=", ".join([t.mention for t in sent_dm]),
            inline=False
        )
    if failed_dm:
        embed_report.add_field(
            name=f"📢 DM'si Kapalı Olanlar ({len(failed_dm)})",
            value=", ".join([t.mention for t in failed_dm]) + " *(Kanaldan etiketlendi)*",
            inline=False
        )
    if role:
        embed_report.add_field(name="👥 Hedef Rol", value=role.mention, inline=True)
    embed_report.set_footer(text="Ala Lounge • Hızlı Masa Çağrı Servisi")

    await _respond(embed=embed_report)


class GameInvitesCog(commands.Cog, name="Oyun Davetleri"):
    """DM Üzerinden Tekli ve Toplu Oyun & Masa Davetleri"""

    def __init__(self, bot):
        self.bot = bot

    def _collect_targets(self, k1, k2, k3, k4, k5):
        return [k for k in [k1, k2, k3, k4, k5] if k is not None]

    # ==================== SLASH KOMUTLARI ====================
    @app_commands.command(name="bazaar", description="Bir veya birden fazla arkadaşına (veya role) The Bazaar daveti gönderir!")
    @app_commands.describe(
        kullanici="Davet edilecek 1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_bazaar(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "bazaar", "The Bazaar", not_ekle, rol)

    @app_commands.command(name="sezai", description="Bir veya birden fazla ortağa Sezai muhabbet masası daveti gönderir!")
    @app_commands.describe(
        kullanici="Davet edilecek 1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_sezai(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "sezai", "Sezai Masası", not_ekle, rol)

    @app_commands.command(name="ziya-masasi", description="Bir veya birden fazla ortağa Ziya muhabbet masası daveti gönderir!")
    @app_commands.describe(
        kullanici="Davet edilecek 1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_ziya(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "ziya", "Ziya Masası", not_ekle, rol)

    @app_commands.command(name="cs", description="Bir veya birden fazla ortağa CS2 daveti gönderir!")
    @app_commands.describe(
        kullanici="Davet edilecek 1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_cs(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "cs", "Counter-Strike 2", not_ekle, rol)

    @app_commands.command(name="lol", description="Bir veya birden fazla ortağa LoL daveti gönderir!")
    @app_commands.describe(
        kullanici="Davet edilecek 1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_lol(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "lol", "League of Legends", not_ekle, rol)

    @app_commands.command(name="toplu-davet", description="İstediğin oyunu seçip birden fazla ortağa veya role toplu davet gönderir!")
    @app_commands.describe(
        oyun="Hangi oyuna veya masaya davet ediyorsun?",
        kullanici="1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    @app_commands.choices(oyun=[
        app_commands.Choice(name="🃏 The Bazaar", value="bazaar"),
        app_commands.Choice(name="💣 Counter-Strike 2", value="cs"),
        app_commands.Choice(name="⚔️ League of Legends", value="lol"),
        app_commands.Choice(name="☕ Sezai Muhabbet Masası", value="sezai"),
        app_commands.Choice(name="☕ Ziya Ortak Masası", value="ziya")
    ])
    async def cmd_toplu_davet(
        self,
        interaction: discord.Interaction,
        oyun: app_commands.Choice[str],
        kullanici: discord.Member = None,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        if not targets and not rol:
            await interaction.response.send_message("❌ Lütfen en az bir kullanıcı veya bir rol seçin ortak!", ephemeral=True)
            return
        await send_bulk_invites(interaction, targets, oyun.value, oyun.name, not_ekle, rol)

    @app_commands.command(name="oyun", description="İstediğin herhangi bir özel oyun için arkadaşlarına davet at!")
    @app_commands.describe(
        oyun_adi="Hangi oyun? (Örn: GTA V, Valorant, FIFA...)",
        kullanici="1. ortak",
        kullanici2="İsteğe bağlı: 2. ortak",
        kullanici3="İsteğe bağlı: 3. ortak",
        kullanici4="İsteğe bağlı: 4. ortak",
        kullanici5="İsteğe bağlı: 5. ortak",
        rol="İsteğe bağlı: Belirli bir roldeki herkese toplu davet at",
        not_ekle="Varsa özel mesajın"
    )
    async def cmd_oyun(
        self,
        interaction: discord.Interaction,
        oyun_adi: str,
        kullanici: discord.Member,
        kullanici2: discord.Member = None,
        kullanici3: discord.Member = None,
        kullanici4: discord.Member = None,
        kullanici5: discord.Member = None,
        rol: discord.Role = None,
        not_ekle: str = None
    ):
        targets = self._collect_targets(kullanici, kullanici2, kullanici3, kullanici4, kullanici5)
        await send_bulk_invites(interaction, targets, "custom", oyun_adi, not_ekle, rol)

    # ==================== PREFIX KOMUTLARI (Sınırsız @Etiket) ====================
    @commands.command(name="bazaar")
    async def prefix_bazaar(self, ctx, *args):
        targets = list(ctx.message.mentions)
        roles = list(ctx.message.role_mentions)
        target_role = roles[0] if roles else None
        note = " ".join([a for a in args if not a.startswith("<@")]) or None
        if not targets and not target_role:
            await ctx.send("❌ Kullanım: `!bazaar @kullanıcı1 @kullanıcı2 ... [varsa not]`")
            return
        await send_bulk_invites(ctx, targets, "bazaar", "The Bazaar", note, target_role)

    @commands.command(name="cs")
    async def prefix_cs(self, ctx, *args):
        targets = list(ctx.message.mentions)
        roles = list(ctx.message.role_mentions)
        target_role = roles[0] if roles else None
        note = " ".join([a for a in args if not a.startswith("<@")]) or None
        if not targets and not target_role:
            await ctx.send("❌ Kullanım: `!cs @kullanıcı1 @kullanıcı2 ... [varsa not]`")
            return
        await send_bulk_invites(ctx, targets, "cs", "Counter-Strike 2", note, target_role)

    @commands.command(name="lol")
    async def prefix_lol(self, ctx, *args):
        targets = list(ctx.message.mentions)
        roles = list(ctx.message.role_mentions)
        target_role = roles[0] if roles else None
        note = " ".join([a for a in args if not a.startswith("<@")]) or None
        if not targets and not target_role:
            await ctx.send("❌ Kullanım: `!lol @kullanıcı1 @kullanıcı2 ... [varsa not]`")
            return
        await send_bulk_invites(ctx, targets, "lol", "League of Legends", note, target_role)

    @commands.command(name="sezai")
    async def prefix_sezai(self, ctx, *args):
        targets = list(ctx.message.mentions)
        roles = list(ctx.message.role_mentions)
        target_role = roles[0] if roles else None
        note = " ".join([a for a in args if not a.startswith("<@")]) or None
        if not targets and not target_role:
            await ctx.send("❌ Kullanım: `!sezai @kullanıcı1 @kullanıcı2 ... [varsa not]`")
            return
        await send_bulk_invites(ctx, targets, "sezai", "Sezai Masası", note, target_role)

    @commands.command(name="ziyamasasi", aliases=["ziya-masasi"])
    async def prefix_ziya(self, ctx, *args):
        targets = list(ctx.message.mentions)
        roles = list(ctx.message.role_mentions)
        target_role = roles[0] if roles else None
        note = " ".join([a for a in args if not a.startswith("<@")]) or None
        if not targets and not target_role:
            await ctx.send("❌ Kullanım: `!ziya @kullanıcı1 @kullanıcı2 ... [varsa not]`")
            return
        await send_bulk_invites(ctx, targets, "ziya", "Ziya Masası", note, target_role)

async def setup(bot):
    await bot.add_cog(GameInvitesCog(bot))
