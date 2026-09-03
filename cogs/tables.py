# -*- coding: utf-8 -*-
import discord
from discord.ext import commands, tasks
from discord import app_commands
import database
import logging
import asyncio

logger = logging.getLogger("AlaCafeBot.Tables")

class TableControlModal(discord.ui.Modal, title="✏️ Masa Adını Değiştir"):
    name_input = discord.ui.TextInput(
        label="Yeni Masa Adı",
        placeholder="Örn: Muhabbet Masası, CS2 Odası...",
        max_length=32
    )

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        new_name = f"☕・{self.name_input.value}"
        await self.channel.edit(name=new_name)
        await interaction.response.send_message(f"✅ Masa adı `{new_name}` olarak güncellendi!", ephemeral=True)

class TableLimitModal(discord.ui.Modal, title="👥 Masa Kapasitesini Belirle"):
    limit_input = discord.ui.TextInput(
        label="Kişi Sayısı (0 = Sınırsız)",
        placeholder="Örn: 2, 4, 8 veya 0",
        max_length=2
    )

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            lim = int(self.limit_input.value)
            if lim < 0 or lim > 99:
                await interaction.response.send_message("❌ Lütfen 0 ile 99 arasında bir sayı girin.", ephemeral=True)
                return
            await self.channel.edit(user_limit=lim)
            msg = "sınırsız yapıldı." if lim == 0 else f"{lim} kişi ile sınırlandı."
            await interaction.response.send_message(f"✅ Masa kapasitesi {msg}", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Geçersiz sayı girdiniz.", ephemeral=True)

class TableControlView(discord.ui.View):
    def __init__(self, owner_id: int, channel: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.channel = channel
        self.is_locked = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu masa sana ait değil! Sadece masa sahibi yönetebilir.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Kilitle / Aç", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="btn_table_lock")
    async def btn_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        current_overwrites = self.channel.overwrites_for(guild.default_role)
        
        if not self.is_locked:
            current_overwrites.connect = False
            await self.channel.set_permissions(guild.default_role, overwrite=current_overwrites)
            self.is_locked = True
            button.emoji = "🔓"
            button.label = "Kilidi Aç"
            button.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔒 Masa kilitlendi! Artık davet etmediklerin giremez.", ephemeral=True)
        else:
            current_overwrites.connect = True
            await self.channel.set_permissions(guild.default_role, overwrite=current_overwrites)
            self.is_locked = False
            button.emoji = "🔒"
            button.label = "Kilitle"
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔓 Masa kilidi açıldı! Herkes katılabilir.", ephemeral=True)

    @discord.ui.button(label="Kapasite", style=discord.ButtonStyle.primary, emoji="👥", custom_id="btn_table_limit")
    async def btn_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TableLimitModal(self.channel))

    @discord.ui.button(label="İsim Değiştir", style=discord.ButtonStyle.success, emoji="✏️", custom_id="btn_table_name")
    async def btn_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TableControlModal(self.channel))

    @discord.ui.button(label="Masayı Kapat", style=discord.ButtonStyle.danger, emoji="❌", custom_id="btn_table_delete")
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚪 Masa dağıtılıyor ve siliniyor...", ephemeral=True)
        database.remove_temp_table(self.channel.id)
        try:
            await self.channel.delete(reason="Masa sahibi masayı kapattı.")
        except Exception:
            pass

class TablesCog(commands.Cog, name="Sanal Masalar"):
    """Sanal Kafe Masaları (Geçici Ses Odaları - Join to Create)"""

    def __init__(self, bot):
        self.bot = bot
        self.cleaner_task.start()

    def cog_unload(self):
        self.cleaner_task.cancel()

    # 15 saniyede bir boş kalan tüm ☕ masalarını tarar ve temizler (Garantili Temizlik)
    @tasks.loop(seconds=15)
    async def cleaner_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for vc in list(guild.voice_channels):
                if vc.name.startswith("☕") or database.get_temp_table(vc.id):
                    # Masa Aç kanalına dokunma
                    if "➕" in vc.name or "Masa Aç" in vc.name:
                        continue
                    if len(vc.members) == 0:
                        try:
                            database.remove_temp_table(vc.id)
                            await vc.delete(reason="Oto-temizleyici: Odada kimse kalmadığı için silindi.")
                            logger.info(f"Boş masa süpürüldü: {vc.name} ({vc.id})")
                        except Exception as e:
                            logger.error(f"Süpürücü masa silme hatası ({vc.id}): {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # 1. KULLANICI "➕ Masa Aç" KANALINA GİRDİĞİNDE
        if after.channel and ("➕" in after.channel.name or "Masa Aç" in after.channel.name or "masa-ac" in after.channel.name.lower()):
            guild = member.guild
            category = after.channel.category

            table_name = f"☕・{member.display_name} Masası"
            try:
                new_channel = await guild.create_voice_channel(
                    name=table_name,
                    category=category,
                    user_limit=0,
                    reason=f"{member.display_name} için sanal masa açıldı."
                )

                # Kullanıcıyı masaya taşı
                await member.move_to(new_channel)
                database.add_temp_table(new_channel.id, guild.id, member.id)

                # Kontrol Paneli Mesajı Gönder
                embed = discord.Embed(
                    title=f"☕ {member.display_name}'nin Masası Hazır!",
                    description=(
                        "Ala Lounge masana hoş geldin! Bu masa tamamen sana aittir.\n\n"
                        "**Aşağıdaki butonları kullanarak masanı yönetebilirsin:**\n"
                        "• **🔒 Kilitle / Aç:** Masaya yabancıların girişini engelle.\n"
                        "• **👥 Kapasite:** Masayı 2, 4, 6 kişilik sınırla.\n"
                        "• **✏️ İsim Değiştir:** Masana özel isim ver.\n"
                        "• **❌ Masayı Kapat:** Masayı sil ve bitir.\n\n"
                        "*(Masadan herkes çıktığında oda kendiliğinden silinir).* 💨"
                    ),
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Ala Cafe & Lounge • Sanal Masa Hizmeti")

                view = TableControlView(owner_id=member.id, channel=new_channel)
                await new_channel.send(content=f"{member.mention}", embed=embed, view=view)
                logger.info(f"Sanal masa açıldı: {new_channel.name} (Sahip: {member.display_name})")

            except Exception as e:
                logger.error(f"Sanal masa oluşturma hatası: {e}")

        # 2. KULLANICI BİR ODADAN ÇIKTIĞINDA (ODADA KİMSE KALMADIYSA ANINDA SİL)
        if before.channel:
            ch_name = before.channel.name
            if ch_name.startswith("☕") or database.get_temp_table(before.channel.id):
                if "➕" not in ch_name and "Masa Aç" not in ch_name:
                    # Discord önbelleğinin tazelenmesi için 1 saniye bekle
                    await asyncio.sleep(1)
                    fresh_channel = member.guild.get_channel(before.channel.id)
                    if fresh_channel and len(fresh_channel.members) == 0:
                        try:
                            database.remove_temp_table(fresh_channel.id)
                            await fresh_channel.delete(reason="Masada kimse kalmadığı için otomatik silindi.")
                            logger.info(f"Boşalan sanal masa anında silindi: {fresh_channel.name}")
                        except Exception as e:
                            logger.error(f"Masa anında silme hatası: {e}")

    @app_commands.command(name="masa-kurucu-olustur", description="Kategoriye otomatik '➕ Masa Aç' ses odası ekler.")
    @app_commands.default_permissions(administrator=True)
    async def cmd_create_generator(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = interaction.channel.category
        ch = await guild.create_voice_channel(
            name="➕・Masa Aç",
            category=category,
            user_limit=1,
            reason="Sanal Masa Kurucu Kanalı"
        )
        await interaction.response.send_message(f"✅ `➕・Masa Aç` kanalı başarıyla oluşturuldu! ({ch.mention})\nÜyeler bu kanala tıkladıklarında otomatik olarak özel masaları açılacak.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TablesCog(bot))
