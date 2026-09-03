# -*- coding: utf-8 -*-
import asyncio
import re
import urllib.request
import json
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg
from config import COLOR_SUCCESS, COLOR_INFO, COLOR_ERROR
import database as db

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "scsearch",
    "extract_flat": False,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "source_address": "0.0.0.0"
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

class MusicPlayerView(discord.ui.View):
    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Duraklat / Devam", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="m_pause_resume")
    async def btn_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Bot herhangi bir ses kanalında değil.", ephemeral=True)
            return
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Müzik duraklatıldı.", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Müzik çalmaya devam ediyor.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şey yok.", ephemeral=True)

    @discord.ui.button(label="Geç", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="m_skip")
    async def btn_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ Şarkı atlandı, sıradakine geçiliyor!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Atlanacak şarkı yok.", ephemeral=True)

    
    @discord.ui.button(label="Döngü", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="m_loop", row=0)
    async def btn_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        cur = self.cog.loops.get(self.guild_id, False)
        new_state = not cur
        self.cog.loops[self.guild_id] = new_state
        if new_state:
            button.style = discord.ButtonStyle.success
            await interaction.response.send_message("🔁 **Döngü Modu AÇIK:** Çalan şarkı bittikçe tekrar edecek!", ephemeral=True)
        else:
            button.style = discord.ButtonStyle.secondary
            await interaction.response.send_message("➡️ **Döngü Modu KAPALI:** Sıradaki şarkılara normal devam edilecek.", ephemeral=True)

    @discord.ui.button(label="Oto-Öneri", style=discord.ButtonStyle.secondary, emoji="📻", custom_id="m_autoplay", row=0)
    async def btn_autoplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        cur = self.cog.autoplay.get(self.guild_id, True)
        new_state = not cur
        self.cog.autoplay[self.guild_id] = new_state
        if new_state:
            button.style = discord.ButtonStyle.success
            await interaction.response.send_message("📻 **Otomatik Oynatma AÇIK:** Kuyruk bittiğinde benzer müzikler otomatik çalmaya devam edecek!", ephemeral=True)
        else:
            button.style = discord.ButtonStyle.secondary
            await interaction.response.send_message("⏹️ **Otomatik Oynatma KAPALI:** Kuyruktaki şarkılar bitince bot beklemede kalacak.", ephemeral=True)

    @discord.ui.button(label="Ses -%10", row=1, style=discord.ButtonStyle.secondary, emoji="🔉", custom_id="m_vol_down")
    async def btn_vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        cur_vol = self.cog.get_volume(self.guild_id)
        new_vol = max(10, cur_vol - 10)
        self.cog.set_volume(self.guild_id, new_vol)
        await interaction.response.send_message(f"🔉 Ses seviyesi: **%{new_vol}**", ephemeral=True)

    @discord.ui.button(label="Ses +%10", row=1, style=discord.ButtonStyle.secondary, emoji="🔊", custom_id="m_vol_up")
    async def btn_vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        cur_vol = self.cog.get_volume(self.guild_id)
        new_vol = min(150, cur_vol + 10)
        self.cog.set_volume(self.guild_id, new_vol)
        await interaction.response.send_message(f"🔊 Ses seviyesi: **%{new_vol}**", ephemeral=True)

    @discord.ui.button(label="Kuyruk", row=1, style=discord.ButtonStyle.secondary, emoji="📜", custom_id="m_queue")
    async def btn_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.cog.get_queue(self.guild_id)
        if not q:
            await interaction.response.send_message("📜 Sırada bekleyen başka şarkı yok.", ephemeral=True)
            return
        lines = [f"**{i+1}.** {track['title']} ({track.get('duration_str', 'Bilinmiyor')})" for i, track in enumerate(q[:10])]
        embed = discord.Embed(title="📜 Müzik Çalma Sırası", description="\n".join(lines), color=COLOR_INFO)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Durdur & Çık", row=1, style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="m_stop")
    async def btn_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            if self.guild_id in self.cog.idle_tasks and not self.cog.idle_tasks[self.guild_id].done():
                self.cog.idle_tasks[self.guild_id].cancel()
                self.cog.idle_tasks.pop(self.guild_id, None)
            self.cog.clear_queue(self.guild_id)
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Müzik kapatıldı ve sesten ayrılındı.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Zaten seste değilim.", ephemeral=True)

class MusicCog(commands.Cog, name="Müzik"):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}             # guild_id -> list of track dicts
        self.volumes = {}            # guild_id -> int (10 to 150)
        self.now_playing = {}        # guild_id -> current track dict
        self.idle_tasks = {}         # guild_id -> asyncio.Task (5 dk boş oda sayacı)
        self.last_text_channels = {} # guild_id -> discord.TextChannel
        self.loops = {}              # guild_id -> bool (şarkı tekrarı)
        self.autoplay = {}           # guild_id -> bool (otomatik benzer şarkı çalma)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        vc = guild.voice_client
        if not vc or not vc.is_connected() or not vc.channel:
            return

        # Botun olduğu odadaki gerçek insan sayısı
        human_members = [m for m in vc.channel.members if not m.bot]

        if len(human_members) == 0:
            # Odada hiç kimse kalmadı, 5 dakikalık (300 saniye) sayaç başlat
            if guild.id not in self.idle_tasks or self.idle_tasks[guild.id].done():
                self.idle_tasks[guild.id] = asyncio.create_task(self._auto_disconnect_timer(guild, vc))
        else:
            # Biri odaya girdiğinde sayacı iptal et
            if guild.id in self.idle_tasks and not self.idle_tasks[guild.id].done():
                self.idle_tasks[guild.id].cancel()
                self.idle_tasks.pop(guild.id, None)

    async def _auto_disconnect_timer(self, guild: discord.Guild, vc: discord.VoiceClient):
        try:
            # 5 dakika (300 saniye) bekle
            await asyncio.sleep(300)
            if vc and vc.is_connected() and vc.channel:
                humans = [m for m in vc.channel.members if not m.bot]
                if len(humans) == 0:
                    self.clear_queue(guild.id)
                    await vc.disconnect()
                    tch = self.last_text_channels.get(guild.id)
                    if tch:
                        try:
                            await tch.send("👋 Odada 5 dakikadır kimse olmadığı için ses kanalından ayrıldım.")
                        except Exception:
                            pass
        except asyncio.CancelledError:
            pass
        finally:
            self.idle_tasks.pop(guild.id, None)

    def get_queue(self, guild_id: int):
        return self.queues.setdefault(guild_id, [])

    def clear_queue(self, guild_id: int):
        self.queues[guild_id] = []
        self.now_playing[guild_id] = None

    def get_volume(self, guild_id: int):
        return self.volumes.get(guild_id, 80)

    def set_volume(self, guild_id: int, vol: int):
        self.volumes[guild_id] = vol
        vc = self.bot.get_guild(guild_id).voice_client if self.bot.get_guild(guild_id) else None
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = vol / 100.0

    def resolve_spotify(self, url: str):
        try:
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                title = data.get("title", "")
                return title
        except Exception:
            return None

    async def search_track(self, query: str):
        # Spotify linki ise başlığı çöz
        if "spotify.com" in query:
            spot_title = await asyncio.to_thread(self.resolve_spotify, query)
            if spot_title:
                query = spot_title

        # Arama yap (Önce YouTube [en stabil FFmpeg akışı], sonra SoundCloud)
        def _extract():
            if not query.startswith("http"):
                search_primary = f"ytsearch:{query}"
                search_secondary = f"scsearch:{query}"
            else:
                search_primary = query
                search_secondary = None

            with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                try:
                    res = ydl.extract_info(search_primary, download=False)
                    if res and "entries" in res and res["entries"]:
                        return res["entries"][0]
                    if res:
                        return res
                except Exception as e1:
                    print("Birincil arama hatası:", e1)

                if search_secondary:
                    try:
                        res2 = ydl.extract_info(search_secondary, download=False)
                        if res2 and "entries" in res2 and res2["entries"]:
                            return res2["entries"][0]
                        if res2:
                            return res2
                    except Exception as e2:
                        print("İkincil arama hatası:", e2)
            return None

        try:
            info = await asyncio.to_thread(_extract)
            if not info:
                return None

            # Float duration hatasını önlemek için tam sayıya yuvarla
            raw_dur = info.get("duration", 0)
            try:
                dur = int(float(raw_dur)) if raw_dur else 0
            except Exception:
                dur = 0

            mins, secs = divmod(dur, 60)
            dur_str = f"{mins}:{secs:02d}" if dur else "Canlı / Bilinmiyor"

            # Doğrudan akış URL'si seçimi
            stream_url = info.get("url")
            if not stream_url and "formats" in info:
                audio_formats = [f for f in info["formats"] if f.get("acodec") != "none"]
                if audio_formats:
                    stream_url = audio_formats[-1]["url"]
                elif info["formats"]:
                    stream_url = info["formats"][-1]["url"]

            return {
                "title": info.get("title", query),
                "url": stream_url,
                "webpage_url": info.get("webpage_url", query),
                "duration_str": dur_str,
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader", "Bilinmeyen Sanatçı")
            }
        except Exception as e:
            print("Müzik arama hatası:", e)
            return None

    async def _fetch_and_queue_autoplay(self, guild_id: int, channel: discord.TextChannel, last_track: dict):
        try:
            uploader = last_track.get("uploader", "")
            title = last_track.get("title", "")
            clean_title = title.split("(")[0].split("[")[0].strip()
            if uploader and uploader != "Bilinmeyen Sanatçı":
                search_q = f"ytsearch5:{uploader} {clean_title} mix"
            else:
                search_q = f"ytsearch5:{clean_title} benzeri şarkılar"

            def _get_candidate():
                with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                    data = ydl.extract_info(search_q, download=False)
                    if data and "entries" in data and data["entries"]:
                        for e in data["entries"]:
                            if e and e.get("title") != last_track.get("title"):
                                return e
                        return data["entries"][0]
                    return None

            candidate = await asyncio.to_thread(_get_candidate)
            if candidate:
                raw_dur = candidate.get("duration", 0)
                try:
                    dur = int(float(raw_dur)) if raw_dur else 0
                except Exception:
                    dur = 0
                mins, secs = divmod(dur, 60)
                dur_str = f"{mins}:{secs:02d}" if dur else "Canlı / Bilinmiyor"

                stream_url = candidate.get("url")
                if not stream_url and "formats" in candidate:
                    audio_formats = [f for f in candidate["formats"] if f.get("acodec") != "none"]
                    stream_url = audio_formats[-1]["url"] if audio_formats else candidate["formats"][-1]["url"]

                next_track = {
                    "title": candidate.get("title", "Önerilen Şarkı"),
                    "url": stream_url,
                    "webpage_url": candidate.get("webpage_url", ""),
                    "duration_str": dur_str,
                    "thumbnail": candidate.get("thumbnail"),
                    "uploader": candidate.get("uploader", "Bilinmeyen Sanatçı"),
                    "is_autoplay": True
                }
                q = self.get_queue(guild_id)
                q.append(next_track)
                try:
                    await channel.send(f"📻 **Otomatik Öneri:** Sırada şarkı kalmadığı için benzer bir parça başlatılıyor: **{next_track['title']}**")
                except Exception:
                    pass
                self.play_next(guild_id, channel)
            else:
                self.now_playing[guild_id] = None
        except Exception as e:
            print("Autoplay hatası:", e)
            self.now_playing[guild_id] = None

    def play_next(self, guild_id: int, channel: discord.TextChannel):
        q = self.get_queue(guild_id)
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        vc = guild.voice_client
        if not vc or not vc.is_connected():
            return

        if vc.is_playing():
            return

        is_loop = self.loops.get(guild_id, False)
        is_autoplay = self.autoplay.get(guild_id, True)
        last_track = self.now_playing.get(guild_id)

        # 1. Kuyruk boşsa ve döngü açıksa aynı şarkıyı çal
        if not q and is_loop and last_track:
            q.append(last_track)

        # 2. Kuyruk boşsa, döngü kapalıysa ve otomatik oynatma açıksa benzer şarkı çek
        if not q and not is_loop and is_autoplay and last_track:
            asyncio.run_coroutine_threadsafe(self._fetch_and_queue_autoplay(guild_id, channel, last_track), self.bot.loop)
            return

        if not q:
            self.now_playing[guild_id] = None
            return

        track = q.pop(0)
        self.now_playing[guild_id] = track
        vol = self.get_volume(guild_id)

        try:
            source = discord.FFmpegPCMAudio(track["url"], executable=FFMPEG_EXE, **FFMPEG_OPTIONS)
            vol_source = discord.PCMVolumeTransformer(source, volume=vol / 100.0)

            def after_finish(err):
                if err:
                    print("Oynatma hatası:", err)
                if self.loops.get(guild_id, False):
                    # Döngü açıksa bu şarkıyı tekrar kuyruğun en başına koy
                    q_cur = self.get_queue(guild_id)
                    q_cur.insert(0, track)
                self.bot.loop.call_soon_threadsafe(self.play_next, guild_id, channel)

            vc.play(vol_source, after=after_finish)

            embed = discord.Embed(
                title="🎵 Şimdi Çalıyor",
                description=f"**[{track['title']}]({track['webpage_url']})**\n\n👤 **Sanatçı:** `{track['uploader']}`\n⏱️ **Süre:** `{track['duration_str']}`\n🔊 **Ses:** `%{vol}`",
                color=COLOR_SUCCESS
            )
            if track.get("thumbnail"):
                embed.set_thumbnail(url=track["thumbnail"])
            embed.set_footer(text="Ala Lounge Müzik İstasyonu • Keyifli dinlemeler!")

            view = MusicPlayerView(self, guild_id)
            asyncio.run_coroutine_threadsafe(channel.send(embed=embed, view=view), self.bot.loop)

        except Exception as e:
            print("Şarkı başlatma hatası:", e)
            self.play_next(guild_id, channel)

    @commands.command(name="play", aliases=["oynat", "çal", "cal"])
    async def prefix_play(self, ctx, *, sarki: str):
        await self.handle_play(ctx.channel, ctx.author, sarki, ctx.send)

    @app_commands.command(name="oynat", description="SoundCloud, Spotify veya YouTube üzerinden anında şarkı çalar")
    @app_commands.describe(
        sarki="Şarkı adı veya link (Spotify/YouTube/SoundCloud)",
        kanal="İsteğe bağlı: Çalınacak ses kanalı (boş bırakırsan bulunduğun kanala otomatik gelir)"
    )
    async def slash_play(self, interaction: discord.Interaction, sarki: str, kanal: discord.VoiceChannel = None):
        await interaction.response.defer(thinking=True)
        await self.handle_play(interaction.channel, interaction.user, sarki, interaction.followup.send, kanal)

    async def handle_play(self, channel, user, sarki: str, send_func, target_vc: discord.VoiceChannel = None):
        guild = channel.guild
        member = guild.get_member(user.id) or user
        self.last_text_channels[guild.id] = channel

        # Yeni şarkı başlatılırken boş oda sayacı varsa iptal et
        if guild.id in self.idle_tasks and not self.idle_tasks[guild.id].done():
            self.idle_tasks[guild.id].cancel()
            self.idle_tasks.pop(guild.id, None)

        # 1. Ses kanalını tespit et (Önce parametre, sonra üyenin bulunduğu ses kanalı)
        voice_channel = target_vc
        if not voice_channel:
            if hasattr(member, "voice") and member.voice and member.voice.channel:
                voice_channel = member.voice.channel
            else:
                # Sunucudaki tüm ses kanallarını tara
                for v in guild.voice_channels:
                    if any(m.id == user.id for m in v.members):
                        voice_channel = v
                        break

        # 2. Eğer hala bulunamadıysa botun zaten bağlı olduğu ses kanalı var mı bak
        vc = guild.voice_client
        if not voice_channel and vc and vc.is_connected():
            voice_channel = vc.channel

        if not voice_channel:
            await send_func("❌ Ses kanalın tespit edilemedi kral! Lütfen önce herhangi bir ses kanalına gir veya komutta ses kanalını seç.")
            return

        # 3. Ses kanalına otomatik bağlan
        if not vc or not vc.is_connected():
            try:
                vc = await voice_channel.connect(self_deaf=True)
            except Exception as e:
                await send_func(f"❌ Ses kanalına bağlanılamadı: {e}")
                return
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        track = await self.search_track(sarki)
        if not track:
            await send_func(f"❌ `{sarki}` bulunamadı veya açılamadı. Farklı bir arama deneyin.")
            return

        q = self.get_queue(guild.id)

        if vc.is_playing() or vc.is_paused():
            q.append(track)
            embed = discord.Embed(
                title="➕ Sıraya Eklendi",
                description=f"**[{track['title']}]({track['webpage_url']})**\n\nSıradaki Pozisyon: `#{len(q)}` | Süre: `{track['duration_str']}`",
                color=COLOR_INFO
            )
            if track.get("thumbnail"):
                embed.set_thumbnail(url=track["thumbnail"])
            await send_func(embed=embed)
        else:
            q.append(track)
            await send_func(f"🔎 **{track['title']}** bulundu, başlatılıyor...")
            self.play_next(guild.id, channel)

    @app_commands.command(name="durdur", description="Müziği duraklatır")
    async def cmd_pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Müzik duraklatıldı.")
        else:
            await interaction.response.send_message("❌ Şu an çalan bir müzik yok.", ephemeral=True)

    @app_commands.command(name="devam", description="Duraklatılan müziği devam ettirir")
    async def cmd_resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Müzik devam ediyor.")
        else:
            await interaction.response.send_message("❌ Duraklatılmış bir müzik yok.", ephemeral=True)

    @app_commands.command(name="gec", description="Çalan şarkıyı geçer")
    async def cmd_skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ Şarkı atlandı!")
        else:
            await interaction.response.send_message("❌ Çalan bir şarkı yok.", ephemeral=True)

    @app_commands.command(name="kuyruk", description="Müzik sırasını görüntüler")
    async def cmd_queue(self, interaction: discord.Interaction):
        q = self.get_queue(interaction.guild_id)
        cur = self.now_playing.get(interaction.guild_id)
        if not cur and not q:
            await interaction.response.send_message("📜 Sıra boş.", ephemeral=True)
            return

        desc = ""
        if cur:
            desc += f"▶️ **Şimdi Çalıyor:** {cur['title']}\n\n**Sırada Bekleyenler:**\n"
        if q:
            desc += "\n".join([f"**{i+1}.** {t['title']}" for i, t in enumerate(q[:10])])
        else:
            desc += "_Sırada başka şarkı yok._"

        embed = discord.Embed(title="📜 Müzik Çalma Sırası", description=desc, color=COLOR_INFO)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ses", description="Müzik ses seviyesini ayarlar (1-150)")
    @app_commands.describe(seviye="Ses seviyesi yüzdesi (örn: 80)")
    async def cmd_volume(self, interaction: discord.Interaction, seviye: int):
        if seviye < 1 or seviye > 150:
            await interaction.response.send_message("❌ Ses seviyesi 1 ile 150 arasında olmalıdır.", ephemeral=True)
            return
        self.set_volume(interaction.guild_id, seviye)
        await interaction.response.send_message(f"🔊 Ses seviyesi **%{seviye}** olarak ayarlandı!")

    @app_commands.command(name="ayril", description="Botu ses kanalından çıkartır")
    async def cmd_leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            self.clear_queue(interaction.guild_id)
            await vc.disconnect()
            await interaction.response.send_message("👋 Ses kanalından ayrıldım!")
        else:
            await interaction.response.send_message("❌ Seste değilim.", ephemeral=True)

    @app_commands.command(name="kafe-radyo", description="7/24 kesintisiz canlı kafe ve lounge radyolarını açar!")
    @app_commands.describe(istasyon="Dinlemek istediğin radyo tarzı")
    @app_commands.choices(istasyon=[
        app_commands.Choice(name="☕ Lo-Fi Chill Cafe (Ders & Rahatlama)", value="lofi"),
        app_commands.Choice(name="🎸 Türkçe Akustik & Kafe Nostalji", value="akustik"),
        app_commands.Choice(name="🎷 Smooth Lounge Jazz (Piyano & Saksafon)", value="jazz"),
        app_commands.Choice(name="🎧 Deep House & Chillout Lounge", value="deephouse")
    ])
    async def cmd_kafe_radyo(self, interaction: discord.Interaction, istasyon: app_commands.Choice[str]):
        queries = {
            "lofi": "ytsearch:lofi hip hop radio beats to relax study to",
            "akustik": "ytsearch:turkce akustik gitar kafe dinletisi",
            "jazz": "ytsearch:coffee shop jazz relaxing piano cafe music",
            "deephouse": "ytsearch:relaxing deep house lounge music chill"
        }
        await interaction.response.defer(thinking=True)
        q = queries.get(istasyon.value, queries["lofi"])
        await self.handle_play(interaction.channel, interaction.user, q, interaction.followup.send)


    @app_commands.command(name="dongu", description="Çalan şarkıyı sürekli tekrarlama modunu (Loop) açar veya kapatır")
    @app_commands.describe(durum="Döngü durumu")
    @app_commands.choices(durum=[
        app_commands.Choice(name="🔁 Açık (Çalan şarkıyı sürekli tekrarla)", value="ac"),
        app_commands.Choice(name="➡️ Kapalı (Sıradaki şarkılara devam et)", value="kapat")
    ])
    async def cmd_loop(self, interaction: discord.Interaction, durum: app_commands.Choice[str]):
        is_on = (durum.value == "ac")
        self.loops[interaction.guild_id] = is_on
        if is_on:
            await interaction.response.send_message("🔁 **Döngü Modu AÇILDI!** Çalan şarkı bittikçe durmadan tekrar çalacak.")
        else:
            await interaction.response.send_message("➡️ **Döngü Modu KAPATILDI.** Sıradaki şarkılara normal şekilde devam edilecek.")

    @app_commands.command(name="otomatik-oynat", description="Kuyruk bitince benzer şarkıları otomatik başlatma modunu ayarlar")
    @app_commands.describe(durum="Otomatik oynatma modu")
    @app_commands.choices(durum=[
        app_commands.Choice(name="📻 Açık (Kuyruk bitince benzer şarkılar çalsın)", value="ac"),
        app_commands.Choice(name="⏹️ Kapalı (Kuyruk bitince sessiz kalsın)", value="kapat")
    ])
    async def cmd_autoplay(self, interaction: discord.Interaction, durum: app_commands.Choice[str]):
        is_on = (durum.value == "ac")
        self.autoplay[interaction.guild_id] = is_on
        if is_on:
            await interaction.response.send_message("📻 **Otomatik Oynatma (Autoplay) AÇILDI!** Kuyruk bittiğinde radyo gibi benzer şarkılar çalmaya devam edecek.")
        else:
            await interaction.response.send_message("⏹️ **Otomatik Oynatma KAPATILDI.** Kuyruk bittiğinde müzik duracak.")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
