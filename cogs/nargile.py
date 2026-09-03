# -*- coding: utf-8 -*-
import random
import discord
from discord import app_commands
from discord.ext import commands
from config import NARGILELER, COLOR_NARGILE, COLOR_CAFE

class NargileSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(NargileCategorySelect())

class NargileCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ala Özel İmza Karışımları", description="Love 66, Lady Killer, Bosphorus Night...", emoji="🌟", value="imza"),
            discord.SelectOption(label="Geleneksel & Esnaf Klasikleri", description="Çift Elma, Siyah Üzüm & Nane...", emoji="🍎", value="klasik"),
            discord.SelectOption(label="Tatlı & Kremsi Karışımlar", description="Pişmiş Şeftali, Bisküvi, Karamel Macchiato...", emoji="🍰", value="tatli"),
        ]
        super().__init__(placeholder="Nargile kategorisi seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0]
        cat_data = NARGILELER[cat_key]

        embed = discord.Embed(
            title=f"{cat_data['kategori']}",
            description=f"_{cat_data['aciklama']}_\n\n**Aşağıda Ala Cafe'nin usta reçeteleri yer almaktadır:**",
            color=COLOR_NARGILE
        )
        for key, item in cat_data["cesitler"].items():
            field_val = (
                f"🌿 **Karışım Oranı:** {item['karisim']}\n"
                f"💨 **Tat Profili:** {item['tat_profili']}\n"
                f"🏺 **Lüle & Köz:** {item['lule_tipi']} • {item['koz_ayari']}\n"
                f"💡 **Usta Tüyosu:** _{item['tuyo']}_"
            )
            embed.add_field(name=f"💨 {item['ad']}", value=field_val, inline=False)

        embed.set_footer(text="Ala Cafe • Közümüz taze, dumanımız beyaz!")
        await interaction.response.edit_message(embed=embed, view=self.view)

class NargileCog(commands.Cog, name="Nargile"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nargile", aliases=["nargile-menusu", "nargileler"])
    async def prefix_nargile(self, ctx):
        embed = discord.Embed(
            title="💨 Ala Cafe — Meşhur Nargile & Tütün Menüsü",
            description=(
                "Ala Cafe'nin usta ellerinden çıkan, dumanı ve aromasıyla ün salmış meşhur nargile çeşitlerimiz!\n\n"
                "👇 **Aşağıdaki menüden kategori seçerek karışım oranlarını ve lüle tüyolarını görebilirsiniz:**"
            ),
            color=COLOR_NARGILE
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed, view=NargileSelectView())

    @app_commands.command(name="nargile-menusu", description="Ala Cafe meşhur nargile çeşitlerini ve tütün reçetelerini açar")
    async def nargile_menusu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💨 Ala Cafe — Meşhur Nargile & Tütün Menüsü",
            description=(
                "Ala Cafe'nin usta ellerinden çıkan, dumanı ve aromasıyla ün salmış meşhur nargile çeşitlerimiz!\n\n"
                "👇 **Aşağıdaki menüden kategori seçerek karışım oranlarını, köz ayarlarını ve usta tüyolarını görebilirsiniz:**\n\n"
                "• Karışım analizi için: `/nargile-karisim <tat1> <tat2> [tat3]`\n"
                "• Zevkinize göre tavsiye için: `/nargile-tavsiye <tat_tercihi>`\n"
                "• Lüle hazırlama rehberi için: `/nargile-tuyo`"
            ),
            color=COLOR_NARGILE
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Ala Cafe Shisha Lounge • Hakiki köz, hakiki lezzet")
        await interaction.response.send_message(embed=embed, view=NargileSelectView())

    @app_commands.command(name="nargile-karisim", description="Kendi tütün karışımınızı girin, Ala Cafe ustası analiz edip köz ve lüle tüyosu versin")
    @app_commands.describe(tat1="1. Tütün / Aroma", tat2="2. Tütün / Aroma", tat3="3. Tütün (isteğe bağlı)")
    async def nargile_karisim(self, interaction: discord.Interaction, tat1: str, tat2: str, tat3: str = None):
        tatlar = [tat1.strip(), tat2.strip()]
        if tat3:
            tatlar.append(tat3.strip())

        title = " + ".join(tatlar)
        tuyo_listesi = [
            "Bu kombinasyonda ana aromayı %60, ferahlatıcıyı %40 oranında tutmanızı öneririm. Fazla baskılarsa tat dengesi bozulur.",
            "Tütünleri lüleye koymadan önce parmak uçlarınızla havalandırarak harmanlayın, şerbeti eşit dağılsın.",
            "Bu karışım orta ısıyı sever; 3 közle açıp 10 dakika sonra közün birini kenara çekmeniz aromayı yakmadan uzun süre korur.",
            "Phunnel lüle ile içerseniz tütünün şerbeti gövdeye akmaz, 1.5 saat boyunca lezzetini kaybetmez."
        ]

        embed = discord.Embed(
            title=f"💨 Usta Nargileci Analizi: {title}",
            description=(
                f"**Karışım:** `{title}`\n\n"
                f"🔥 **Önerilen Dolum:** Havalandırarak, lüle kenarına yapıştırmadan gevşek dolum.\n"
                f"🏺 **Lüle Tercihi:** Glaze Phunnel veya Kaliteli Toprak Lüle\n"
                f"💨 **Köz Ayarı:** 3 adet 26mm hindistan cevizi közü ile başlatın.\n\n"
                f"🗣️ **Usta Notu:** *\"{random.choice(tuyo_listesi)}\"*"
            ),
            color=COLOR_NARGILE
        )
        embed.set_footer(text="Ala Cafe • Köz Ustası Onaylı")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nargile-tavsiye", description="Damak zevkinize göre Ala Cafe'den anında özel nargile tavsiyesi alın")
    @app_commands.describe(tercih="Nasıl bir tat istersiniz?")
    @app_commands.choices(tercih=[
        app_commands.Choice(name="🍓 Tatlı & Meyvemsi (Love 66, Lady Killer vb.)", value="tatli_meyveli"),
        app_commands.Choice(name="🧊 Aşırı Ferah & Buzlu (Buz, Nane, Yaban Mersini)", value="ferah_buz"),
        app_commands.Choice(name="👑 Sert & Esnaf Klasik (Hakiki Çift Elma & Anason)", value="sert_klasik"),
        app_commands.Choice(name="🍰 Tatlı & Fırın / Kremsi (Pişmiş Şeftali, Bisküvi)", value="kremsi_tatli"),
    ])
    async def nargile_tavsiye(self, interaction: discord.Interaction, tercih: app_commands.Choice[str]):
        if tercih.value == "tatli_meyveli":
            onerilen = "🌟 **Ala Special:** Love 66 (%40) + Lady Killer (%30) + Mango (%20) + Buz (%10)"
            aciklama = "Meyvenin dibine vurmak isteyenlerin vazgeçilmezi. Dumanı odada mis gibi kokar."
        elif tercih.value == "ferah_buz":
            onerilen = "🧊 **Bosphorus Night:** Yaban Mersini (%50) + Guava (%30) + Taze Nane (%20)"
            aciklama = "Boğazı ferahlatan, kafayı açan serin bir akşam nargilesi."
        elif tercih.value == "sert_klasik":
            onerilen = "🍎 **Nostalji Hakiki Çift Elma:** Nakhla Çift Elma (%80) + Nane Sakız (%20)"
            aciklama = "Ağır abilerin tercihi. Hakiki deri marpuç ve demli çayla servis edilir."
        else:
            onerilen = "🍰 **Pişmiş Şeftali & Bisküvi:** Pişmiş Şeftali (%50) + Bisküvi (%30) + Vanilya (%20)"
            aciklama = "Sıcak fırın lezzeti, kahvenin yanına en çok yakışan tatlı duman."

        embed = discord.Embed(
            title="🎯 Size Özel Nargile Tavsiyesi",
            description=f"{interaction.user.mention} için önerilen lezzet:\n\n{onerilen}\n\n_{aciklama}_",
            color=COLOR_NARGILE
        )
        embed.set_footer(text="Ala Cafe • Masanıza hemen hazırlıyoruz!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nargile-tuyo", description="Mükemmel nargile hazırlamanın 4 altın kuralı")
    async def nargile_tuyo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💨 Ala Cafe'den Kusursuz Nargile Rehberi",
            description=(
                "**1. Havalandırarak Doldurma:** Tütünü lüleye bastırmayın. Hava akışı olmazsa tütün yanar ve duman acılaşır.\n\n"
                "**2. Folyoya Değdirmeme:** Tütünün en üst katmanı folyodan veya HMD metalinden en az 2 mm aşağıda olmalıdır.\n\n"
                "**3. Köz Rotasyonu:** Közleri lülenin tam ortasına koymayın, kenarlara yerleştirin ve 15-20 dakikada bir çevirin.\n\n"
                "**4. Temiz Takım:** Her seans sonrası ser ve şişeyi mutlaka fırçalayın; önceki tütünün kokusu yeni lezzeti bozar."
            ),
            color=COLOR_NARGILE
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NargileCog(bot))
