# -*- coding: utf-8 -*-
import random
import time
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_NARGILE, COLOR_CAFE, COLOR_GOLD, COLOR_SUCCESS, COLOR_ERROR
import database as db

# ==============================================================================
# MİRAÇ USTA — SİSTEMSEL & VERİ ODAKLI TÜTÜN VERİTABANI
# ==============================================================================
MIRAC_TOBACCO_DB = {
    "inferno_nane": {
        "ad": "🔥 İnferno Nane (Miraç'ın İmza Başyapıtı)",
        "karisim": "%60 Kutup Nanesi + %30 Volkanik Buz + %10 Kristal Okaliptüs",
        "duman_yogunlugu": "%99.4 (Maksimum Opaklık)",
        "yanma_isisi": "238°C Optimum Termal Denge",
        "nikotin_orani": "%0.05 Düşük Nikotin (Sıfır Baş Ağrısı)",
        "lezzet_doygunlugu": "10/10 (Boğazda Termal Şok & Buzul Etkisi)",
        "lule_tipi": "Glaze Solaris veya Phunnel (3x 26mm Hindistan Cevizi Közü)",
        "aciklama": "Miraç Usta'nın laboratuvar hassasiyetiyle geliştirdiği, akciğerlere adeta kriyojenik ferahlık pompalayan rakipsiz tütün harmanı."
    },
    "ala_special": {
        "ad": "🌟 Ala Special (Kral Karışım)",
        "karisim": "Love 66 (%40) + Lady Killer (%30) + Mango (%20) + Hafif Buz (%10)",
        "duman_yogunlugu": "%94.2 Yoğun Beyaz Bulut",
        "yanma_isisi": "225°C Orta-Yüksek Isı",
        "nikotin_orani": "%0.05 Dengeli",
        "lezzet_doygunlugu": "9.2/10 Tropikal & Meyvemsi",
        "lule_tipi": "Phunnel Lüle (Lotus HMD)",
        "aciklama": "Meyvemsi şeker dengesi optimize edilmiş, tat kaybı yaşamaksızın 90 dakika duman performansı veren karışım."
    },
    "bosphorus_night": {
        "ad": "🌊 Bosphorus Night (Boğaz Esintisi)",
        "karisim": "Yaban Mersini (%50) + Guava (%30) + Taze Nane (%20)",
        "duman_yogunlugu": "%91.8 Akıcı Duman",
        "yanma_isisi": "230°C",
        "nikotin_orani": "%0.05 Hafif",
        "lezzet_doygunlugu": "8.8/10 Mayhoş & Serin",
        "lule_tipi": "Glaze Phunnel veya Toprak Lüle",
        "aciklama": "Gece seanslarında kafa dağıtmak ve zihni açmak için tasarlanmış analitik orman meyvesi profili."
    },
    "havana_sunset": {
        "ad": "🌅 Havana Sunset (Tropik Günbatımı)",
        "karisim": "Ananas (%40) + Maracuja (%35) + Çarkıfelek (%25)",
        "duman_yogunlugu": "%89.5 İpeksi Duman",
        "yanma_isisi": "220°C",
        "nikotin_orani": "%0.04 Düşük",
        "lezzet_doygunlugu": "9.0/10 Egzotik Tatlı",
        "lule_tipi": "Phunnel Lüle",
        "aciklama": "Asla acılaşmayan şerbet formülüyle lüle dibine kadar ilk nefes tazeliğini koruyan tropik fırtına."
    },
    "cift_elma": {
        "ad": "🍎 Nostalji Hakiki Çift Elma & Anason",
        "karisim": "Nakhla Çift Elma (%80) + Nane Sakız (%20)",
        "duman_yogunlugu": "%96.0 Ağır & Tok Duman",
        "yanma_isisi": "245°C Yüksek Termal Eşik",
        "nikotin_orani": "%0.50 Yüksek Esnaf Sertliği",
        "lezzet_doygunlugu": "9.5/10 Derin Anason Aroması",
        "lule_tipi": "Geleneksel Toprak Lüle (Deri Marpuç)",
        "aciklama": "Geleneksel köz basımına uygun, anason yoğunluğuyla ciğerleri dolduran efsanevi esnaf standardı."
    },
    "uzum_nane": {
        "ad": "🍇 Efsane Siyah Üzüm & Nane",
        "karisim": "Siyah Üzüm (%70) + Nane (%30)",
        "duman_yogunlugu": "%90.5 Yoğun Rayiha",
        "yanma_isisi": "228°C",
        "nikotin_orani": "%0.05",
        "lezzet_doygunlugu": "8.7/10 Koyu Meyvemsi",
        "lule_tipi": "Klasik Toprak Lüle",
        "aciklama": "Dengeli nane ferahlığıyla tütünün şekerini kesen, sohbeti uzatan stabil duman."
    },
    "pismis_seftali": {
        "ad": "🥧 Pişmiş Şeftali & Bisküvi Şöleni",
        "karisim": "Pişmiş Şeftali (%50) + Bisküvi (%30) + Vanilya (%20)",
        "duman_yogunlugu": "%93.0 Kadifemsi Tatlı Duman",
        "yanma_isisi": "215°C Düşük Isı (Slow Bake)",
        "nikotin_orani": "%0.05 Hafif",
        "lezzet_doygunlugu": "9.4/10 Fırın Gurme",
        "lule_tipi": "Phunnel Glaze",
        "aciklama": "Yavaş pişen lülelerde tatlı krizini çözen, Türk kahvesiyle termodinamik uyum yakalayan tatlı harman."
    }
}

# ==============================================================================
# STOK SİSTEMİ (İnferno Nane Stok Durumu)
# ==============================================================================
INFERNO_STOCK = {
    "kalan": 2,  # Başlangıçta 2 kutu
    "son_guncelleme": time.time()
}

# ==============================================================================
# VIEW: /mirac KATEGORİ VE KONTROL PANELİ
# ==============================================================================
class MiracCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🔥 Miraç'ın Başyapıtı: İnferno Nane", description="Termal Şok, %99.4 duman, mutlak zirve", emoji="🔥", value="inferno_nane"),
            discord.SelectOption(label="🌟 İmza Karışımları (Ala Special, Bosphorus)", description="Yüksek aromalı özel termal reçeteler", emoji="🌟", value="imza"),
            discord.SelectOption(label="🍎 Esnaf & Geleneksel Klasikler (Çift Elma, Üzüm)", description="Yüksek nikotin ve anason matriksi", emoji="🍎", value="klasik"),
            discord.SelectOption(label="🥧 Fırın & Gurme Kremsi Tatlar (Şeftali Bisküvi)", description="Düşük ısıda pişen kadife dumanlar", emoji="🥧", value="tatli"),
        ]
        super().__init__(placeholder="🧪 Miraç Usta'nın Tütün Menüsünden Seçim Yapın...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]

        if val == "inferno_nane":
            item = MIRAC_TOBACCO_DB["inferno_nane"]
            stok_durumu = f"🟢 **Stok Durumu:** {INFERNO_STOCK['kalan']} Kutu Mevcut" if INFERNO_STOCK['kalan'] > 0 else "🔴 **Stok Durumu: TÜKENDİ! (Depolar Boş)**"
            
            embed = discord.Embed(
                title=f"{item['ad']}",
                description=(
                    f"_{item['aciklama']}_\n\n"
                    f"{stok_durumu}\n\n"
                    f"📊 **SİSTEMSEL & TERMAL ANALİZ:**\n"
                    f"• 🌿 **Formül:** `{item['karisim']}`\n"
                    f"• 💨 **Duman Opaklığı:** `{item['duman_yogunlugu']}`\n"
                    f"• 🌡️ **Termal Kalibrasyon:** `{item['yanma_isisi']}`\n"
                    f"• ⚡ **Nikotin İndeksi:** `{item['nikotin_orani']}`\n"
                    f"• 🍯 **Lezzet Katsayısı:** `{item['lezzet_doygunlugu']}`\n"
                    f"• 🏺 **Önerilen Donanım:** `{item['lule_tipi']}`\n\n"
                    f"🗣️ **Miraç Usta Diyor ki:** *\"Bak ortak, bana zevkini sorma. Bu masanın matematiksel olarak en kusursuz tütünü İnferno Nane'dir. Eğer bittiyse macera ekibini toplayıp sefere çıkacağız!\"*"
                ),
                color=COLOR_GOLD
            )
            embed.set_footer(text="Ala Lounge • Köz & Tütün Mühendisi Miraç")
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "imza":
            embed = discord.Embed(
                title="🌟 Miraç Usta — İmza Karışımları & Termal Veri",
                description="Ala Lounge laboratuvarında optimize edilmiş özel karışımlar:",
                color=COLOR_NARGILE
            )
            for k in ["ala_special", "bosphorus_night", "havana_sunset"]:
                it = MIRAC_TOBACCO_DB[k]
                embed.add_field(
                    name=it["ad"],
                    value=f"🌿 `{it['karisim']}`\n💨 Duman: `{it['duman_yogunlugu']}` | 🌡️ Isı: `{it['yanma_isisi']}`\n💡 _{it['aciklama']}_",
                    inline=False
                )
            embed.set_footer(text="Miraç Usta: 'Aroma kalibrasyonu tamamlandı.'")
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "klasik":
            embed = discord.Embed(
                title="🍎 Miraç Usta — Ağır Esnaf Klasikleri",
                description="Yüksek nikotin ve anason matriksine sahip köklü reçeteler:",
                color=COLOR_CAFE
            )
            for k in ["cift_elma", "uzum_nane"]:
                it = MIRAC_TOBACCO_DB[k]
                embed.add_field(
                    name=it["ad"],
                    value=f"🌿 `{it['karisim']}`\n💨 Duman: `{it['duman_yogunlugu']}` | ⚡ Nikotin: `{it['nikotin_orani']}`\n💡 _{it['aciklama']}_",
                    inline=False
                )
            embed.set_footer(text="Miraç Usta: 'Çift elmada közü merkeze koyan tütünü yakar.'")
            await interaction.response.edit_message(embed=embed, view=self.view)

        else:
            embed = discord.Embed(
                title="🥧 Miraç Usta — Fırın & Gurme Kremsi Tatlar",
                description="Düşük termal toleransla ağır ağır pişen lüks dumanlar:",
                color=COLOR_SUCCESS
            )
            it = MIRAC_TOBACCO_DB["pismis_seftali"]
            embed.add_field(
                name=it["ad"],
                value=f"🌿 `{it['karisim']}`\n💨 Duman: `{it['duman_yogunlugu']}` | 🌡️ Isı: `{it['yanma_isisi']}`\n💡 _{it['aciklama']}_",
                inline=False
            )
            embed.set_footer(text="Miraç Usta: '2 közle yavaş pişir, acele eden aromayı öldürür.'")
            await interaction.response.edit_message(embed=embed, view=self.view)

class MiracMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=240)
        self.add_item(MiracCategorySelect())

    @discord.ui.button(label="🔥 İnferno Nane İste", style=discord.ButtonStyle.danger, emoji="💨")
    async def btn_request_inferno(self, interaction: discord.Interaction, button: discord.ui.Button):
        if INFERNO_STOCK["kalan"] > 0:
            INFERNO_STOCK["kalan"] -= 1
            embed = discord.Embed(
                title="🔥 Masaya İnferno Nane Ateşlendi!",
                description=(
                    f"**{interaction.user.mention}** için özel **İnferno Nane** lülesi hazırlandı!\n\n"
                    f"🌡️ **Köz Sıcaklığı:** `238°C Tam Termal Verim`\n"
                    f"💨 **Duman Durumu:** Akciğerlerde anında buzul şoku başladı.\n"
                    f"📦 **Kalan Stok:** `{INFERNO_STOCK['kalan']} Kutu`\n\n"
                    f"🗣️ **Miraç Usta:** *\"Közleri tam lülenin kenarlarına oturttum ortak. İlk 3 nefesi derin çek, dumanın saflığını ciğerlerinde hisset!\"*"
                ),
                color=COLOR_GOLD
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="🔴 EYVAH! İnferno Nane Tükendi!",
                description=(
                    f"**Miraç Usta:** *\"Ortak dur! Dolapları kontrol ettim, maalesef son kutuyu az önce bitirdik. Stok sıfır!\"*\n\n"
                    f"Bu efsanevi tütünü getirmeden masalarda huzur olmaz.\n"
                    f"Aşağıdaki **'🧭 Maceraya Başla'** butonuna basarak veya `/mirac-inferno-nane-macerasi` yazarak tütünü getirme görevine çıkabilirsin!"
                ),
                color=COLOR_ERROR
            )
            view = discord.ui.View()
            view.add_item(StartAdventureButton())
            await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label="🧭 İnferno Macerasına Çık", style=discord.ButtonStyle.success, emoji="⚔️")
    async def btn_start_quest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await start_inferno_adventure(interaction)

class StartAdventureButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🧭 İnferno Nane Macerasını Başlat!", style=discord.ButtonStyle.danger, emoji="⚔️")

    async def callback(self, interaction: discord.Interaction):
        await start_inferno_adventure(interaction)

# ==============================================================================
# İNTERAKTİF MACERA OYUNU: /mirac-inferno-nane-macerasi
# ==============================================================================
class AdventureStage1View(discord.ui.View):
    def __init__(self, player: discord.User | discord.Member):
        super().__init__(timeout=120)
        self.player = player

    @discord.ui.button(label="🚢 Gizli Liman Sevkiyatı (Riskli & Hızlı)", style=discord.ButtonStyle.primary, emoji="⚓")
    async def route_port(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("❌ Bu macerayı sadece başlatan oynayabilir!", ephemeral=True)
            return
        await handle_adventure_stage_2(interaction, self.player, "port")

    @discord.ui.button(label="⛰️ Toros Zirveleri Gizli Serası (Zorlu & Doğal)", style=discord.ButtonStyle.success, emoji="🏔️")
    async def route_mountain(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("❌ Bu macerayı sadece başlatan oynayabilir!", ephemeral=True)
            return
        await handle_adventure_stage_2(interaction, self.player, "mountain")

class AdventureStage2View(discord.ui.View):
    def __init__(self, player: discord.User | discord.Member, route: str):
        super().__init__(timeout=120)
        self.player = player
        self.route = route

    @discord.ui.button(label="🕵️‍♂️ Karşı Taktik / Zeka Kullan", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def action_smart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("❌ Bu macerayı sadece başlatan oynayabilir!", ephemeral=True)
            return
        await handle_adventure_stage_3(interaction, self.player, self.route, "smart")

    @discord.ui.button(label="🔥 Miraç'ın Termal Baskısı (Doğrudan Atıl)", style=discord.ButtonStyle.danger, emoji="💥")
    async def action_force(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("❌ Bu macerayı sadece başlatan oynayabilir!", ephemeral=True)
            return
        await handle_adventure_stage_3(interaction, self.player, self.route, "force")

class AdventureStage3View(discord.ui.View):
    def __init__(self, player: discord.User | discord.Member):
        super().__init__(timeout=120)
        self.player = player

    @discord.ui.button(label="🌡️ 238°C Termal Kalibrasyon Testi Yap", style=discord.ButtonStyle.danger, emoji="🔥")
    async def final_test(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("❌ Bu macerayı sadece başlatan oynayabilir!", ephemeral=True)
            return
        await handle_adventure_final(interaction, self.player)

async def start_inferno_adventure(interaction: discord.Interaction):
    player = interaction.user
    embed = discord.Embed(
        title="⚔️ Efsanevi İnferno Nane Arama Macerası — Bölüm 1",
        description=(
            f"**Miraç Usta çantayı sırtladı:**\n"
            f"*\"Dinle beni {player.mention}! Ala Lounge'ın en kıymetli hazinesi olan İnferno Nane bitti.* \n"
            f"*Bu tütün sıradan dükkanlarda satılmaz. Formülünü sadece iki yer saklar.* \n\n"
            f"🧭 **Nereden Gideceğiz? Güzergahını Seç:**\n\n"
            f"1. ⚓ **Gizli Liman Sevkiyatı:** Gece yarısı gelen tütün kalyonundan gizlice almak. Hızlıdır ama gümrükçüler ve sahte tütün mafyası kol gezer.\n"
            f"2. 🏔️ **Toros Zirveleri Gizli Serası:** Karlı dağların tepesinde buz gibi kaynak suyuyla yetişen orijinal nane yapraklarını toplamak. Zorludur ama saf lezzettir.\n\n"
            f"Aşağıdaki butonlardan birine basarak kararını ver!"
        ),
        color=COLOR_GOLD
    )
    embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f525.png")
    embed.set_footer(text="Miraç Usta: 'Hata payımız sıfır, veri odaklı ilerliyoruz.'")
    view = AdventureStage1View(player)
    
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)

async def handle_adventure_stage_2(interaction: discord.Interaction, player: discord.Member, route: str):
    if route == "port":
        desc = (
            f"🚢 **Limanın karanlık rıhtımına yanaştınız!**\n\n"
            f"Sislerin arasından paslı bir kalyon belirdi. Ancak tam tütün sandıklarına uzanırken, "
            f"**Sahte Tütüncü Şevket** ve adamları yolunuzu kesti:\n"
            f"*\"Hop delikanlı! O İnferno Nane kasalarını almak o kadar kolay değil!\"*\n\n"
            f"Miraç Usta fısıldadı: *\"Ortak, tütünlerin sahte talaş karışımı olma ihtimali %74.3. Ne yapıyoruz?\"*\n\n"
            f"• 🧠 **Zeka & Taktik:** Şevket'in tütünlerine refraktometre tutarak sahte olduğunu kanıtla ve depoyu ele geçir!\n"
            f"• 💥 **Termal Baskı:** Miraç'ın 500 derecelik köz maşasını çekerek rıhtımı inlet ve kasaları alıp kaç!"
        )
    else:
        desc = (
            f"🏔️ **Toros Dağlarının 2500 metre zirvesindesiniz!**\n\n"
            f"Buz gibi bir fırtına koptu. Termometreler -12°C'yi gösteriyor. Tam İnferno nane kristallerine ulaşmışken, "
            f"dağın yaşlı tütün koruyucusu **Duman Keşişi** karşınıza dikildi:\n"
            f"*\"Bu kutsal naneyi sadece nefesi köz gibi sıcak, aklı buz gibi berrak olanlar Ala Lounge'a götürebilir!\"*\n\n"
            f"• 🧠 **Zeka & Taktik:** Keşişe lüle aerodinamiği ve şerbet dengesini anlatarak bilgeliğini kanıtla!\n"
            f"• 💥 **Termal Baskı:** Dağ fırtınasında meşe közünü söndürmeden yakarak termal gücünü göster!"
        )

    embed = discord.Embed(
        title="⚔️ İnferno Nane Macerası — Bölüm 2: Tehlike Anı!",
        description=desc,
        color=COLOR_CAFE
    )
    embed.set_footer(text="Kararını ver ortak, zaman aleyhimize işliyor!")
    view = AdventureStage2View(player, route)
    await interaction.response.edit_message(embed=embed, view=view)

async def handle_adventure_stage_3(interaction: discord.Interaction, player: discord.Member, route: str, action: str):
    embed = discord.Embed(
        title="⚔️ İnferno Nane Macerası — Bölüm 3: Son Test!",
        description=(
            f"🎉 **Engeli başarıyla aştınız!**\n\n"
            f"Miraç Usta ile birlikte orijinal İnferno Nane tütün yapraklarını ve buz kristali esansını güvenle sandıklara doldurdunuz!\n\n"
            f"Ancak Miraç Usta tütünü Ala Lounge masalarına sunmadan önce son ve en kritik adımı istiyor:\n"
            f"**\"LABORATUVAR TERMAL KALİBRASYON TESTİ!\"**\n\n"
            f"Tütünün gerçek İnferno Nane olup olmadığını anlamak için lüleye yerleştirip tam **238°C**'de duman yoğunluğunu test etmemiz gerek.\n\n"
            f"Aşağıdaki butona basarak testi ateşle!"
        ),
        color=COLOR_GOLD
    )
    view = AdventureStage3View(player)
    await interaction.response.edit_message(embed=embed, view=view)

async def handle_adventure_final(interaction: discord.Interaction, player: discord.Member):
    # Başarı: Stok yenilenir, oyuncuya XP eklenir!
    INFERNO_STOCK["kalan"] += 5
    INFERNO_STOCK["son_guncelleme"] = time.time()

    # XP Ödülü Ver
    old_lvl, new_lvl, new_xp = db.add_user_xp(player.id, interaction.guild_id or 1112406647738994718, 250)

    embed = discord.Embed(
        title="🏆 GÖREV BAŞARILI: İNFERNO NANE KASADA!",
        description=(
            f"🔥 **TEBRİKLER {player.mention}!**\n\n"
            f"Miraç Usta test tüpünü havaya kaldırdı:\n"
            f"*\"Matematik yanılmaz ortak! Duman yoğunluğu %99.4, buz kristalizasyonu mükemmel! Hakiki İnferno Nane'yi Ala Lounge'a getirdik!\"*\n\n"
            f"📦 **GÜNCEL STOK:** `+5 Kutu Hakiki İnferno Nane Depoya Eklendi!`\n"
            f"⭐ **ÖDÜLÜN:** `+250 XP Kazandın!` (Yeni XP: **{new_xp}**)\n"
            f"👑 **Unvan:** `🔥 İnferno Kaşifi`\n\n"
            f"Şimdi masaya dönüp `/mirac` yazarak hakiki zafer dumanını tüttürebilirsiniz!"
        ),
        color=COLOR_SUCCESS
    )
    embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f3c6.png")
    embed.set_footer(text="Ala Lounge • Görev Tamamlandı | Közler Taze!")

    await interaction.response.edit_message(embed=embed, view=None)

# ==============================================================================
# COG TANIMI VE SLASH KOMUTLARI
# ==============================================================================
class NargileCog(commands.Cog, name="Nargileci Miraç"):
    """Ala Lounge Köz & Tütün Mühendisi Miraç Usta"""

    def __init__(self, bot):
        self.bot = bot

    # 1. /mirac (Ana Menü)
    @app_commands.command(name="mirac", description="Köz & Tütün Mühendisi Miraç Usta'nın sistemsel ve veri odaklı nargile menüsü")
    async def cmd_mirac(self, interaction: discord.Interaction):
        stok_durumu = f"🟢 `{INFERNO_STOCK['kalan']} Kutu`" if INFERNO_STOCK['kalan'] > 0 else "🔴 `TÜKENDİ!`"
        embed = discord.Embed(
            title="💨 Köz & Tütün Mühendisi Miraç Usta — Ala Lounge",
            description=(
                f"Selamlar ortak! Ben **Miraç**, Ala Lounge'ın duman aerodinamiği, köz kalibrasyonu ve tütün şerbeti benden sorulur. "
                f"Bizde tesadüf yoktur, her lüle miligramla ve termal veriyle hazırlanır.\n\n"
                f"🌟 **Miraç'ın Mutlak Tavsiyesi:** 🔥 **İnferno Nane** *(Stok: {stok_durumu})*\n\n"
                f"👇 **Aşağıdaki menüden kategori seçerek termal ve analitik reçeteleri inceleyebilir, "
                f"veya doğrudan butonlarla İnferno Nane isteyebilir / maceraya çıkabilirsin!**"
            ),
            color=COLOR_NARGILE
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Ala Lounge Shisha Lab • Miraç Usta Onaylı")
        await interaction.response.send_message(embed=embed, view=MiracMainView())

    # 2. /mirac-inferno-nane-macerasi (İnteraktif RPG Oyunu)
    @app_commands.command(name="mirac-inferno-nane-macerasi", description="İnferno Nane stoğu bittiğinde Miraç Usta ile tütünü getirme macerasına çık!")
    async def cmd_mirac_macerasi(self, interaction: discord.Interaction):
        await start_inferno_adventure(interaction)

    # 3. Eski /nargile-menusu Uyumluluğu
    @app_commands.command(name="nargile-menusu", description="Miraç Usta'nın nargile çeşitlerini ve reçetelerini açar")
    async def cmd_nargile_menusu(self, interaction: discord.Interaction):
        await self.cmd_mirac(interaction)

    # 4. /nargile-karisim (Miraç Usta'nın Veri Odaklı Karışım Analizi)
    @app_commands.command(name="nargile-karisim", description="Kendi tütün karışımınızı girin, Miraç Usta termal ve lezzet analizini çıkarsın")
    @app_commands.describe(tat1="1. Tütün / Aroma", tat2="2. Tütün / Aroma", tat3="3. Tütün (isteğe bağlı)")
    async def cmd_nargile_karisim(self, interaction: discord.Interaction, tat1: str, tat2: str, tat3: str = None):
        tatlar = [tat1.strip(), tat2.strip()]
        if tat3:
            tatlar.append(tat3.strip())

        title = " + ".join(tatlar)
        tuyo_analiz = [
            "Termal analiz: Şerbet yoğunluğu yüksek. İlk 15 dakika 3 közle ısıtıp ardından 2 köze düşürmeniz yanma eğrisini dengeler.",
            "Aroma kalibrasyonu: Ana aromayı %60, ferahlatıcı ajanı %40 tutmanızı öneririm. Fazlası koku reseptörlerini bloke eder.",
            "Lüle aerodinamiği: Tütünleri birbirine bastırmadan havalandırarak serin; hava kanalları açık kaldığında duman verimi %35 artar.",
            "Bu kombinasyon fena değil ortak ama benim laboratuvar standardım olan İnferno Nane'nin yanına yaklaşamaz, benden söylemesi!"
        ]

        embed = discord.Embed(
            title=f"💨 Miraç Usta Veri Analizi: {title}",
            description=(
                f"📊 **MİRAÇ USTA SİSTEMSEL RAPORU:**\n\n"
                f"• 🧪 **Karışım Matrisi:** `{title}`\n"
                f"• 🌡️ **Önerilen Isı:** `225°C - 235°C Aralığı`\n"
                f"• 🏺 **Tavsiye Lüle:** `Glaze Phunnel & Lotus HMD`\n"
                f"• 💨 **Duman Tahmini:** `%92.5 Opaklık`\n\n"
                f"🗣️ **Miraç Usta Diyor ki:** *\"{random.choice(tuyo_analiz)}\"*\n\n"
                f"*(Unutma, favorim her zaman 🔥 **İnferno Nane**'dir!)*"
            ),
            color=COLOR_NARGILE
        )
        embed.set_footer(text="Ala Lounge • Miraç Usta Shisha Engineering")
        await interaction.response.send_message(embed=embed)

    # 5. /nargile-tavsiye (Miraç Usta'nın Algoritmik Tavsiyesi)
    @app_commands.command(name="nargile-tavsiye", description="Damak zevkinize göre Miraç Usta'dan anında veri odaklı tütün tavsiyesi alın")
    @app_commands.describe(tercih="Nasıl bir tat istersiniz?")
    @app_commands.choices(tercih=[
        app_commands.Choice(name="🔥 Zirve Ferahlık (Miraç'ın İmza İnferno Nanesi)", value="inferno"),
        app_commands.Choice(name="🍓 Tatlı & Meyvemsi (Love 66, Lady Killer vb.)", value="tatli_meyveli"),
        app_commands.Choice(name="🧊 Aşırı Ferah & Buzlu (Buz, Yaban Mersini)", value="ferah_buz"),
        app_commands.Choice(name="👑 Sert & Esnaf Klasik (Hakiki Çift Elma & Anason)", value="sert_klasik"),
        app_commands.Choice(name="🥧 Tatlı & Fırın / Kremsi (Pişmiş Şeftali, Bisküvi)", value="kremsi_tatli"),
    ])
    async def cmd_nargile_tavsiye(self, interaction: discord.Interaction, tercih: app_commands.Choice[str]):
        if tercih.value == "inferno":
            onerilen = "🔥 **İnferno Nane:** %60 Kutup Nanesi + %30 Volkanik Buz + %10 Kristal Okaliptüs"
            aciklama = "Miraç Usta'nın şahsi başyapıtı. Buzul şokuyla ciğerleri yenileyen mutlak 1 numara."
        elif tercih.value == "tatli_meyveli":
            onerilen = "🌟 **Ala Special:** Love 66 (%40) + Lady Killer (%30) + Mango (%20) + Buz (%10)"
            aciklama = "Meyvemsi şeker dengesi optimize edilmiş, dumanı odayı saran favori."
        elif tercih.value == "ferah_buz":
            onerilen = "🌊 **Bosphorus Night:** Yaban Mersini (%50) + Guava (%30) + Taze Nane (%20)"
            aciklama = "Boğazı ferahlatan, zihni açan dengeli bir gece nargilesi."
        elif tercih.value == "sert_klasik":
            onerilen = "🍎 **Nostalji Hakiki Çift Elma:** Nakhla Çift Elma (%80) + Nane Sakız (%20)"
            aciklama = "Ağır abilerin tercihi. Hakiki deri marpuç ve demli çayla servis edilir."
        else:
            onerilen = "🥧 **Pişmiş Şeftali & Bisküvi:** Pişmiş Şeftali (%50) + Bisküvi (%30) + Vanilya (%20)"
            aciklama = "Sıcak fırın lezzeti, kahvenin yanına en çok yakışan tatlı duman."

        embed = discord.Embed(
            title="🎯 Miraç Usta'nın Algoritmik Tavsiyesi",
            description=(
                f"{interaction.user.mention} için veri odaklı lezzet tavsiyesi:\n\n"
                f"{onerilen}\n\n"
                f"💡 _{aciklama}_\n\n"
                f"*(Favorim her zaman **İnferno Nane**'dir ortak, fırsat buldukça onu dene!)*"
            ),
            color=COLOR_GOLD
        )
        embed.set_footer(text="Ala Lounge • Masanıza hemen hazırlıyoruz!")
        await interaction.response.send_message(embed=embed)

    # 6. /nargile-tuyo (Miraç Usta'nın 4 Termal İlkesi)
    @app_commands.command(name="nargile-tuyo", description="Miraç Usta'dan kusursuz nargile hazırlamanın 4 bilimsel kuralı")
    async def cmd_nargile_tuyo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💨 Miraç Usta'nın 4 Termodinamik Nargile Kuralı",
            description=(
                "**1. Havalandırarak Doldurma (Aerodinamik):** Tütünü lüleye ASLA bastırmayın. Hava akışı olmazsa şerbet yanar, duman acılaşır.\n\n"
                "**2. Termal Boşluk (2 mm Kuralı):** Tütünün en üst katmanı folyodan veya HMD metalinden en az 2 mm aşağıda kalmalıdır.\n\n"
                "**3. Köz Rotasyonu:** Közleri lülenin tam ortasına koymayın. Kenarlara yerleştirip 18-20 dakikada bir 90 derece çevirin.\n\n"
                "**4. Hijyen ve Şişe Sıcaklığı:** Şişedeki suyun sıcaklığı 15°C'yi geçerse duman ağırlaşır; şişeye 3-4 parça buz atmak filtrelemeyi %40 iyileştirir."
            ),
            color=COLOR_NARGILE
        )
        embed.set_footer(text="Miraç Usta Shisha Labs")
        await interaction.response.send_message(embed=embed)

    # Prefix komutları: !mirac, !nargile
    @commands.command(name="mirac", aliases=["nargile"])
    async def prefix_mirac(self, ctx):
        embed = discord.Embed(
            title="💨 Köz & Tütün Mühendisi Miraç Usta — Ala Lounge",
            description="Miraç Usta masada! Menüyü incelemek için aşağıdaki menüyü kullanın veya `/mirac` yazın.",
            color=COLOR_NARGILE
        )
        await ctx.send(embed=embed, view=MiracMainView())

async def setup(bot):
    await bot.add_cog(NargileCog(bot))
