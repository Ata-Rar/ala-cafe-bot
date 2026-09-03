# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from config import COLOR_CAFE, COLOR_SUCCESS, COLOR_ERROR

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Destek kanalı 5 saniye içinde kapatılıyor...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"{interaction.user.name} tarafından kapatıldı")

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="☕ Destek Talebi Aç (Garson Çağır)", style=discord.ButtonStyle.primary, emoji="🛎️", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        # Zaten açık talep var mı kontrol et
        existing_name = f"destek-{member.name}".lower().replace(" ", "-")
        existing_ch = discord.utils.get(guild.text_channels, name=existing_name)
        if existing_ch:
            await interaction.response.send_message(f"❌ Zaten açık bir destek talebiniz bulunuyor: {existing_ch.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(
            name=existing_name,
            overwrites=overwrites,
            reason=f"Destek talebi: {member.name}"
        )

        embed = discord.Embed(
            title=f"🛎️ Destek Masası — {member.display_name}",
            description=(
                f"Merhaba {member.mention}! Sunucu yetkililerine veya özel desteğe bildirmek istediğin konuyu buradan yazabilirsin.\n\n"
                f"🔒 İşiniz bittiğinde aşağıdaki **'Talebi Kapat'** butonuna basarak odayı sonlandırabilirsiniz."
            ),
            color=COLOR_CAFE
        )
        embed.set_footer(text="Ala Cafe • Müşteri Memnuniyeti Masası")
        await channel.send(content=f"{member.mention} | Yetkili ekibi", embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Destek odanız açıldı: {channel.mention}", ephemeral=True)

class TicketsCog(commands.Cog, name="Destek"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Butonların bot yeniden başladığında da dinlenmesini sağla (Persistent Views)
        self.bot.add_view(TicketOpenView())
        self.bot.add_view(TicketCloseView())

    @app_commands.command(name="destek-paneli", description="Kanalda sabit bir butonlu destek/talep paneli oluşturur")
    @app_commands.checks.has_permissions(administrator=True)
    async def destek_paneli(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛎️ Ala Cafe — Müşteri Hizmetleri & Destek Masası",
            description=(
                "Sunucuyla ilgili bir şikayetiniz, öneriniz, sorunuz veya özel bir yetkili görüşmesi ihtiyacınız mı var?\n\n"
                "Aşağıdaki **'Destek Talebi Aç'** butonuna tıklayarak sadece sizin ve yetkililerin görebileceği özel bir oda oluşturabilirsiniz."
            ),
            color=COLOR_CAFE
        )
        embed.set_footer(text="Ala Cafe • Esnaf samimiyeti, profesyonel hizmet")
        await interaction.channel.send(embed=embed, view=TicketOpenView())
        await interaction.response.send_message("✅ Destek paneli başarıyla oluşturuldu!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
