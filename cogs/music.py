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

COLOR_SPOTIFY = 0x1DB954  # Spotify Resmi Yeşili

class MusicPlayerView(discord.ui.View):
    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Duraklat / Devam", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="m_pause_resume", row=0)
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

    @discord.ui.button(label="Geç", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="m_skip", row=0)
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

    @discord.ui.button(label="🛑 Tamamen Kapat & Sıfırla", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="m_stop_clear", row=1)
    async def btn_stop_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.stop_and_clear(self.guild_id)
        await interaction.response.send_message("🛑 **Müzik tamamen durduruldu ve tüm çalma sırası temizlendi!** Artık yeni bir playliste veya şarkıya geçebilirsin.", ephemeral=False)

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

class MusicCog(commands.Cog, name="Müzik"):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}
        self.volumes = {}
        self.loops = {}
        self.autoplay = {}
        self.is_stopped = {}
        self.last_text_channels = {}
        self.idle_tasks = {}

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def clear_queue(self, guild_id: int):
        self.queues[guild_id] = []
        self.now_playing[guild_id] = None

    def stop_and_clear(self, guild_id: int):
        """Müziği tamamen durdurur, kuyruğu sıfırlar ve autoplay döngüsünü keser."""
        self.is_stopped[guild_id] = True
        self.clear_queue(guild_id)
        self.now_playing[guild_id] = None
        guild = self.bot.get_guild(guild_id)
        if guild and guild.voice_client:
            vc = guild.voice_client
            if vc.is_playing() or vc.is_paused():
                vc.stop()

    def get_volume(self, guild_id: int):
        return self.volumes.get(guild_id, 80)

    def set_volume(self, guild_id: int, vol: int):
        self.volumes[guild_id] = vol
        vc = self.bot.get_guild(guild_id).voice_client if self.bot.get_guild(guild_id) else None
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = vol / 100.0

    # --- SPOTIFY GELİŞMİŞ PARSER (Şarkı, Albüm, Playlist) ---
    def parse_spotify_url(self, raw_url: str):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        clean_url = raw_url.split("?")[0].strip()
        m = re.search(r"spotify\.com/(?:intl-[a-z]+/)?(playlist|album|track)/([a-zA-Z0-9]+)", clean_url)
        if not m:
            return None

        item_type = m.group(1)
        item_id = m.group(2)
        embed_url = f"https://open.spotify.com/embed/{item_type}/{item_id}"

        try:
            req = urllib.request.Request(embed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8")
                match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
                if match:
                    data = json.loads(match.group(1))
                    props = data.get("props", {}).get("pageProps", {})
                    state_data = props.get("state", {}).get("data", {})
                    entity = state_data.get("entity", {})

                    title = entity.get("name") or entity.get("title") or "Spotify Listesi"

                    if item_type == "track":
                        artists_raw = entity.get("subtitle") or entity.get("artists") or ""
                        if isinstance(artists_raw, list):
                            artist_str = ", ".join([a.get("name", "") if isinstance(a, dict) else str(a) for a in artists_raw])
                        else:
                            artist_str = str(artists_raw)
                        full_name = f"{artist_str} - {title}" if artist_str else title
                        return {
                            "type": "track",
                            "title": title,
                            "tracks": [full_name]
                        }
                    else:
                        track_list = entity.get("trackList", [])
                        tracks = []
                        for t in track_list:
                            t_title = t.get("title")
                            t_art = t.get("subtitle") or ""
                            if t_title:
                                tracks.append(f"{t_art} - {t_title}" if t_art else t_title)
                        return {
                            "type": item_type,
                            "title": title,
                            "tracks": tracks
                        }
        except Exception as e:
            print("Spotify parse hatası:", e)
            return None

    async def search_track(self, query: str):
        if "spotify.com" in query:
            spot_data = await asyncio.to_thread(self.parse_spotify_url, query)
            if spot_data and spot_data.get("tracks"):
                query = spot_data["tracks"][0]

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

            raw_dur = info.get("duration", 0)
            try:
                dur = int(float(raw_dur)) if raw_dur else 0
            except Exception:
                dur = 0

            mins, secs = divmod(dur, 60)
            dur_str = f"{mins}:{secs:02d}" if dur else "Canlı / Bilinmiyor"

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
        if self.is_stopped.get(guild_id, False):
            return

        try:
            uploader = last_track.get("uploader", "")
            title = last_track.get("title", "")
            clean_title = title.split("(")[0].split("[")[0].strip()
            query = f"ytsearch:{uploader} {clean_title} radio" if uploader else f"ytsearch:{clean_title} mix"

            def _search_mix():
                with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                    try:
                        res = ydl.extract_info(query, download=False)
                        if res and "entries" in res and len(res["entries"]) > 1:
                            return res["entries"][1]
                        if res and "entries" in res and res["entries"]:
                            return res["entries"][0]
                    except Exception:
                        pass
                return None

            candidate = await asyncio.to_thread(_search_mix)
            if candidate and not self.is_stopped.get(guild_id, False):
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

    def _start_playback(self, vc: discord.VoiceClient, guild_id: int, channel: discord.TextChannel, track: dict):
        if self.is_stopped.get(guild_id, False):
            return

        self.now_playing[guild_id] = track
        vol = self.get_volume(guild_id)

        try:
            source = discord.FFmpegPCMAudio(track["url"], executable=FFMPEG_EXE, **FFMPEG_OPTIONS)
            vol_source = discord.PCMVolumeTransformer(source, volume=vol / 100.0)

            def after_finish(err):
                if err:
                    print("Oynatma hatası:", err)
                if self.is_stopped.get(guild_id, False):
                    return
                if self.loops.get(guild_id, False):
                    q_cur = self.get_queue(guild_id)
                    q_cur.insert(0, track)
                self.bot.loop.call_soon_threadsafe(self.play_next, guild_id, channel)

            vc.play(vol_source, after=after_finish)

            card_color = COLOR_SPOTIFY if track.get("is_spotify") else COLOR_SUCCESS
            badge = "🟢 Spotify • " if track.get("is_spotify") else "🎵 "

            embed = discord.Embed(
                title=f"{badge}Şimdi Çalıyor",
                description=(
                    f"**[{track['title']}]({track.get('webpage_url', '')})**\n\n"
                    f"👤 **Sanatçı:** `{track.get('uploader', 'Bilinmeyen')}`\n"
                    f"⏱️ **Süre:** `{track.get('duration_str', 'Bilinmiyor')}`\n"
                    f"🔊 **Ses:** `%{vol}`"
                ),
                color=card_color
            )
            if track.get("thumbnail"):
                embed.set_thumbnail(url=track["thumbnail"])
            embed.set_footer(text="Ala Lounge Müzik İstasyonu • Keyifli dinlemeler!")

            view = MusicPlayerView(self, guild_id)
            asyncio.run_coroutine_threadsafe(channel.send(embed=embed, view=view), self.bot.loop)

        except Exception as e:
            print("Şarkı başlatma hatası:", e)
            self.play_next(guild_id, channel)

    def play_next(self, guild_id: int, channel: discord.TextChannel):
        if self.is_stopped.get(guild_id, False):
            self.now_playing[guild_id] = None
            return

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

        if not q and is_loop and last_track:
            q.append(last_track)

        if not q and not is_loop and is_autoplay and last_track:
            asyncio.run_coroutine_threadsafe(self._fetch_and_queue_autoplay(guild_id, channel, last_track), self.bot.loop)
            return

        if not q:
            self.now_playing[guild_id] = None
            return

        track = q.pop(0)

        # Lazy Spotify şarkısı ise sırası geldiğinde akışı çöz
        if track.get("is_spotify_lazy"):
            async def _resolve_and_play():
                if self.is_stopped.get(guild_id, False):
                    return
                resolved = await self.search_track(track["query"])
                if resolved:
                    resolved["is_spotify"] = True
                    self._start_playback(vc, guild_id, channel, resolved)
                else:
                    self.play_next(guild_id, channel)
            asyncio.run_coroutine_threadsafe(_resolve_and_play(), self.bot.loop)
            return

        self._start_playback(vc, guild_id, channel, track)

    async def _resolve_voice_channel(self, channel, user, target_vc: discord.VoiceChannel = None):
        guild = channel.guild
        member = guild.get_member(user.id) or user
        voice_channel = target_vc
        if not voice_channel:
            if hasattr(member, "voice") and member.voice and member.voice.channel:
                voice_channel = member.voice.channel
            else:
                for v in guild.voice_channels:
                    if any(m.id == user.id for m in v.members):
                        voice_channel = v
                        break
        vc = guild.voice_client
        if not voice_channel and vc and vc.is_connected():
            voice_channel = vc.channel
        return voice_channel, vc

    # --- SPOTIFY ÇALMA LİSTESİ TOPLU KUYRUĞA EKLEME ---
    async def handle_spotify_import(self, channel, user, spot_data: dict, send_func, target_vc: discord.VoiceChannel = None, sirayi_sifirla: bool = False):
        guild = channel.guild
        self.last_text_channels[guild.id] = channel

        if sirayi_sifirla:
            self.stop_and_clear(guild.id)

        self.is_stopped[guild.id] = False

        voice_channel, vc = await self._resolve_voice_channel(channel, user, target_vc)
        if not voice_channel:
            await send_func("❌ Ses kanalın tespit edilemedi ortak! Lütfen önce bir ses kanalına gir.")
            return

        if not vc or not vc.is_connected():
            try:
                vc = await voice_channel.connect(self_deaf=True)
            except Exception as e:
                await send_func(f"❌ Ses kanalına bağlanılamadı: {e}")
                return
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        tracks = spot_data.get("tracks", [])
        if not tracks:
            await send_func("❌ Spotify listesinde çalınabilir parça bulunamadı.")
            return

        title = spot_data.get("title", "Spotify Çalma Listesi")
        first_track_name = tracks[0]
        q = self.get_queue(guild.id)

        is_already_playing = (vc.is_playing() or vc.is_paused()) and not sirayi_sifirla

        if not is_already_playing:
            # İlk şarkıyı hemen çözüp başlat
            first_resolved = await self.search_track(first_track_name)
            if first_resolved:
                first_resolved["is_spotify"] = True
                q.append(first_resolved)
                self.play_next(guild.id, channel)
            
            # Kalan tüm parçaları lazy olarak kuyruğa diz
            for t_name in tracks[1:]:
                q.append({
                    "title": f"🟢 {t_name}",
                    "query": t_name,
                    "is_spotify_lazy": True,
                    "is_spotify": True
                })

            embed = discord.Embed(
                title="🟢 Spotify Çalma Listesi Başlatıldı!",
                description=(
                    f"🎧 **Liste Adı:** `{title}`\n"
                    f"📊 **Toplam Parça:** `{len(tracks)} adet şarkı`\n"
                    f"▶️ **İlk Çalan:** **{first_track_name}**\n\n"
                    f"Kalan {len(tracks) - 1} şarkı arka arkaya çalmak üzere sıraya alındı! 🎵"
                ),
                color=COLOR_SPOTIFY
            )
            embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f3a7.png")
            embed.set_footer(text="Ala Lounge • Spotify Müzik İstasyonu")
            await send_func(embed=embed)

        else:
            # Zaten çalıyorsa tüm listeyi doğrudan kuyruğa ekle
            for t_name in tracks:
                q.append({
                    "title": f"🟢 {t_name}",
                    "query": t_name,
                    "is_spotify_lazy": True,
                    "is_spotify": True
                })

            embed = discord.Embed(
                title="🟢 Spotify Çalma Listesi Sıraya Eklendi!",
                description=(
                    f"🎧 **Liste Adı:** `{title}`\n"
                    f"📊 **Eklenen Parça:** `{len(tracks)} adet şarkı`\n"
                    f"📋 **Kuyruk Sırası:** #{len(q) - len(tracks) + 1} ile #{len(q)} arası"
                ),
                color=COLOR_SPOTIFY
            )
            embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f3a7.png")
            embed.set_footer(text="Ala Lounge • Spotify Müzik İstasyonu")
            await send_func(embed=embed)

    async def handle_play(self, channel, user, sarki: str, send_func, target_vc: discord.VoiceChannel = None, sirayi_sifirla: bool = False):
        guild = channel.guild
        member = guild.get_member(user.id) or user
        self.last_text_channels[guild.id] = channel

        if sirayi_sifirla:
            self.stop_and_clear(guild.id)

        self.is_stopped[guild.id] = False

        if guild.id in self.idle_tasks and not self.idle_tasks[guild.id].done():
            self.idle_tasks[guild.id].cancel()
            self.idle_tasks.pop(guild.id, None)

        # Spotify playlist veya albüm mü kontrol et
        if "spotify.com" in sarki and ("playlist" in sarki or "album" in sarki):
            spot_data = await asyncio.to_thread(self.parse_spotify_url, sarki)
            if spot_data and spot_data.get("tracks"):
                await self.handle_spotify_import(channel, user, spot_data, send_func, target_vc, sirayi_sifirla)
                return

        voice_channel, vc = await self._resolve_voice_channel(channel, user, target_vc)
        if not voice_channel:
            await send_func("❌ Ses kanalın tespit edilemedi kral! Lütfen önce herhangi bir ses kanalına gir veya komutta ses kanalını seç.")
            return

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

        if "spotify.com" in sarki:
            track["is_spotify"] = True

        q = self.get_queue(guild.id)

        if (vc.is_playing() or vc.is_paused()) and not sirayi_sifirla:
            q.append(track)
            card_color = COLOR_SPOTIFY if track.get("is_spotify") else COLOR_INFO
            badge = "🟢 Spotify • " if track.get("is_spotify") else ""
            embed = discord.Embed(
                title=f"➕ {badge}Sıraya Eklendi",
                description=(
                    f"**[{track['title']}]({track['webpage_url']})**\n\n"
                    f"Sıradaki Pozisyon: `#{len(q)}` | Süre: `{track['duration_str']}`"
                ),
                color=card_color
            )
            if track.get("thumbnail"):
                embed.set_thumbnail(url=track["thumbnail"])
            await send_func(embed=embed)
        else:
            q.append(track)
            await send_func(f"🔎 **{track['title']}** bulundu, başlatılıyor...")
            self.play_next(guild.id, channel)

    # ==================== SPOTIFY ÖZEL KOMUTU ====================
    @app_commands.command(name="spotify", description="Spotify playlist, albüm veya şarkı linkini anında kuyruğa ekler ve çalar")
    @app_commands.describe(
        link_veya_arama="Spotify playlist, albüm veya şarkı linki (veya şarkı adı)",
        sirayi_sifirla="Eski sırayı ve çalan şarkıyı tamamen temizleyip bu listeyi baştan başlat",
        kanal="İsteğe bağlı: Çalınacak ses kanalı"
    )
    async def slash_spotify(self, interaction: discord.Interaction, link_veya_arama: str, sirayi_sifirla: bool = False, kanal: discord.VoiceChannel = None):
        await interaction.response.defer(thinking=True)
        await self.handle_play(interaction.channel, interaction.user, link_veya_arama, interaction.followup.send, kanal, sirayi_sifirla)

    @commands.command(name="spotify")
    async def prefix_spotify(self, ctx, *, link_veya_arama: str):
        await self.handle_play(ctx.channel, ctx.author, link_veya_arama, ctx.send)

    # ==================== STANDART KOMUTLAR ====================
    @commands.command(name="play", aliases=["oynat", "çal", "cal"])
    async def prefix_play(self, ctx, *, sarki: str):
        await self.handle_play(ctx.channel, ctx.author, sarki, ctx.send)

    @app_commands.command(name="oynat", description="SoundCloud, Spotify veya YouTube üzerinden anında şarkı veya çalma listesi çalar")
    @app_commands.describe(
        sarki="Şarkı adı veya link (Spotify Playlist/YouTube/SoundCloud)",
        sirayi_sifirla="Eski sırayı ve çalan şarkıyı tamamen temizleyip bu şarkıyı/listeyi baştan başlat",
        kanal="İsteğe bağlı: Çalınacak ses kanalı"
    )
    async def slash_play(self, interaction: discord.Interaction, sarki: str, sirayi_sifirla: bool = False, kanal: discord.VoiceChannel = None):
        await interaction.response.defer(thinking=True)
        await self.handle_play(interaction.channel, interaction.user, sarki, interaction.followup.send, kanal, sirayi_sifirla)

    # ==================== TAM DURDURMA & SIFIRLAMA ====================
    @app_commands.command(name="kapat", description="Müziği tamamen kapatır, tüm kuyruğu temizler ve botu sessize alır")
    async def cmd_kapat(self, interaction: discord.Interaction):
        self.stop_and_clear(interaction.guild_id)
        embed = discord.Embed(
            title="🛑 Müzik Tamamen Kapatıldı",
            description="Çalan müzik durduruldu, kuyruktaki tüm şarkılar temizlendi ve otomatik oynatma kesildi.\n\nArtık yeni bir şarkı veya playlist başlatabilirsin!",
            color=COLOR_ERROR
        )
        embed.set_footer(text="Ala Lounge Müzik İstasyonu • Sıfırlandı")
        await interaction.response.send_message(embed=embed)

    @commands.command(name="kapat", aliases=["stop", "temizle", "sifirla"])
    async def prefix_kapat(self, ctx):
        self.stop_and_clear(ctx.guild.id)
        await ctx.send("🛑 **Müzik tamamen kapatıldı ve tüm çalma sırası temizlendi!**")

    @app_commands.command(name="durdur", description="Müziği geçici olarak duraklatır (Devam ettirmek için /devam, tamamen kapatmak için /kapat)")
    async def cmd_pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Müzik geçici olarak duraklatıldı. Devam için `/devam`, tamamen kapatıp sırayı sıfırlamak için `/kapat` kullanabilirsin.")
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
            badge = "🟢 " if cur.get("is_spotify") else "▶️ "
            desc += f"{badge}**Şimdi Çalıyor:** {cur['title']}\n\n**Sırada Bekleyenler:**\n"
        if q:
            desc += "\n".join([f"**{i+1}.** {t['title']}" for i, t in enumerate(q[:15])])
            if len(q) > 15:
                desc += f"\n_...ve {len(q) - 15} şarkı daha sırada bekliyor._"
        else:
            desc += "_Sırada başka şarkı yok._"

        embed = discord.Embed(title="📜 Müzik Çalma Sırası", description=desc, color=COLOR_SPOTIFY if cur and cur.get("is_spotify") else COLOR_INFO)
        embed.set_footer(text=f"Toplam {len(q)} şarkı sırada bekliyor | Sırayı temizlemek için: /kapat")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ses", description="Müzik ses seviyesini ayarlar (1-150)")
    @app_commands.describe(seviye="Ses seviyesi yüzdesi (örn: 80)")
    async def cmd_volume(self, interaction: discord.Interaction, seviye: int):
        if seviye < 1 or seviye > 150:
            await interaction.response.send_message("❌ Ses seviyesi 1 ile 150 arasında olmalıdır.", ephemeral=True)
            return
        self.set_volume(interaction.guild_id, seviye)
        await interaction.response.send_message(f"🔊 Ses seviyesi **%{seviye}** olarak ayarlandı!")

    @app_commands.command(name="ayril", description="Botu ses kanalından çıkartır ve sırayı temizler")
    async def cmd_leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            self.stop_and_clear(interaction.guild_id)
            await vc.disconnect()
            await interaction.response.send_message("👋 Ses kanalından ayrıldım ve sırayı temizledim!")
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
