# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import time

class GiveawayJoinView(discord.ui.View):
    def __init__(self, prize: str, end_time: float, winner_count: int, host_id: int):
        super().__init__(timeout=None)
        self.prize = prize
        self.end_time = end_time
        self.winner_count = winner_count
        self.host_id = host_id
        self.participants = set()  # set of user_ids

    @discord.ui.button(label="Çekilişe Katıl", style=discord.ButtonStyle.success, emoji="🎉", custom_id="btn_giveaway_join")
    async def btn_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.participants:
            self.participants.remove(uid)
            button.label = f"Çekilişe Katıl ({len(self.participants)})"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("❌ Çekilişten ayrıldın.", ephemeral=True)
        else:
            self.participants.add(uid)
            button.label = f"Çekilişe Katıl ({len(self.participants)})"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🎉 Çekilişe başarıyla katıldın! Bol şans!", ephemeral=True)

class GiveawayCog(commands.Cog, name="Çekiliş"):
    """Süreli ve İsim Listeli Hızlı Çekiliş Sistemi"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cekilis-hizli", description="Yazdığın isimler veya üyeler arasında anında çekiliş yapar!")
    @app_commands.describe(
        odul="Çekilişin ödülü nedir?",
        isimler="Adayların isimleri (Virgül veya boşluk ile ayırın: Ahmet, Mehmet, Ali...)",
        kazanan_sayisi="Kaç kişi kazansın? (Varsayılan: 1)"
    )
    async def cmd_quick_giveaway(self, interaction: discord.Interaction, odul: str, isimler: str, kazanan_sayisi: int = 1):
        # İsimleri ayıkla
        raw_list = [name.strip() for name in isimler.replace(",", " ").split() if name.strip()]
        if not raw_list:
            await interaction.response.send_message("❌ Lütfen en az bir isim veya aday girin.", ephemeral=True)
            return

        if kazanan_sayisi > len(raw_list):
            kazanan_sayisi = len(raw_list)

        # Heyecan verici animasyonlu mesaj
        embed_loading = discord.Embed(
            title="🎲 ÇEKİLİŞ ÇARKI DÖNÜYOR...",
            description=(
                f"🎁 **Ödül:** `{odul}`\n"
                f"👥 **Aday Sayısı:** `{len(raw_list)} kişi`\n\n"
                "🎰 *Adaylar karıştırılıyor, çark dönüyor... Lütfen bekleyin!*"
            ),
            color=discord.Color.gold()
        )
        embed_loading.set_footer(text="Ala Lounge • Şans Çarkı")
        await interaction.response.send_message(embed=embed_loading)

        # 2 saniye heyecan payı
        await asyncio.sleep(2.5)

        # Kazananları seç
        winners = random.sample(raw_list, kazanan_sayisi)
        winners_str = ", ".join([f"**{w}**" for w in winners])

        embed_result = discord.Embed(
            title="🎉 ÇEKİLİŞ SONUÇLANDI! TEBRİKLER! 🎉",
            description=(
                f"🎁 **Kazanılan Ödül:** `{odul}`\n\n"
                f"🏆 **KAZANAN(LAR):**\n✨ {winners_str} ✨\n\n"
                f"👥 **Toplam Katılımcı:** {len(raw_list)} aday\n"
                f"🎯 **Çekilişi Yapan:** {interaction.user.mention}"
            ),
            color=discord.Color.green()
        )
        embed_result.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f389.png")
        embed_result.set_footer(text="Ala Lounge • Adil & Şeffaf Çekiliş Sistemi")

        await interaction.edit_original_response(embed=embed_result)

    @app_commands.command(name="cekilis-baslat", description="Süreli ve butonlu büyük çekiliş başlatır!")
    @app_commands.describe(
        odul="Çekiliş ödülü (Örn: 1 Aylık Discord Nitro, VIP Rolü)",
        sure_dakika="Çekiliş kaç dakika sürsün? (Örn: 5, 10, 60)",
        kazanan_sayisi="Kaç kişi kazansın? (Varsayılan: 1)"
    )
    async def cmd_timed_giveaway(self, interaction: discord.Interaction, odul: str, sure_dakika: int, kazanan_sayisi: int = 1):
        if sure_dakika <= 0:
            await interaction.response.send_message("❌ Süre en az 1 dakika olmalıdır.", ephemeral=True)
            return

        end_timestamp = int(time.time() + (sure_dakika * 60))
        view = GiveawayJoinView(prize=odul, end_time=end_timestamp, winner_count=kazanan_sayisi, host_id=interaction.user.id)

        embed = discord.Embed(
            title=f"🎉 BÜYÜK ÇEKİLİŞ BAŞLADI: {odul.upper()} 🎉",
            description=(
                f"Aşağıdaki **'🎉 Çekilişe Katıl'** butonuna basarak çekilişe katılabilirsiniz!\n\n"
                f"🎁 **Ödül:** `{odul}`\n"
                f"👑 **Düzenleyen:** {interaction.user.mention}\n"
                f"🏆 **Kazanan Sayısı:** `{kazanan_sayisi}`\n"
                f"⏳ **Bitiş Zamanı:** <t:{end_timestamp}:R> (<t:{end_timestamp}:T>)"
            ),
            color=discord.Color.from_rgb(250, 179, 135)
        )
        embed.set_footer(text="Ala Lounge • Çekiliş Etkinliği")

        await interaction.response.send_message(content="📢 @everyone Yeni bir çekiliş başladı!", embed=embed, view=view)
        message = await interaction.original_response()

        # Arka planda süreyi bekle
        asyncio.create_task(self._giveaway_timer(message, view, odul, sure_dakika * 60, kazanan_sayisi, interaction.channel))

    async def _giveaway_timer(self, message: discord.Message, view: GiveawayJoinView, prize: str, seconds: int, winner_count: int, channel: discord.TextChannel):
        await asyncio.sleep(seconds)

        # Katılımcıları al
        participants = list(view.participants)
        for child in view.children:
            child.disabled = True

        if not participants:
            embed_ended = discord.Embed(
                title=f"❌ ÇEKİLİŞ İPTAL EDİLDİ: {prize}",
                description="Yeterli katılım olmadığı için (0 katılımcı) çekiliş iptal edildi.",
                color=discord.Color.red()
            )
            try:
                await message.edit(embed=embed_ended, view=view)
            except Exception:
                pass
            return

        # Kazananları belirle
        actual_winners_count = min(len(participants), winner_count)
        winner_ids = random.sample(participants, actual_winners_count)
        mentions = [f"<@{uid}>" for uid in winner_ids]
        mentions_str = ", ".join(mentions)

        embed_winner = discord.Embed(
            title=f"🎉 ÇEKİLİŞ SONA ERDİ: {prize.upper()} 🎉",
            description=(
                f"🎁 **Ödül:** `{prize}`\n\n"
                f"🏆 **KAZANANLAR:**\n✨ {mentions_str} ✨\n\n"
                f"👥 **Toplam Katılım:** {len(participants)} kişi\n"
                f"*(Tebrik ederiz! Ödülünüz için yetkililerle iletişime geçin).* 🎊"
            ),
            color=discord.Color.green()
        )
        embed_winner.set_footer(text="Ala Lounge • Çekiliş Sona Erdi")

        try:
            await message.edit(embed=embed_winner, view=view)
            await channel.send(f"🎊 Tebrikler {mentions_str}! **{prize}** çekilişini kazandınız!")
        except Exception as e:
            print("Çekiliş bitiş hatası:", e)

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
