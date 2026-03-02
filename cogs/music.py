import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import os

# yt-dlp ayarları
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,  # Playlist desteği AÇIK!
    'nocheckcertificate': True,
    'ignoreerrors': True,  # Hatalı videoları atla
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'playlistend': 50,  # Maximum 50 şarkı
    'extract_flat': False,  # Playlist içeriğini tam çek
    'age_limit': None,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, seek_to=0):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        # Seek desteği
        ffmpeg_opts = FFMPEG_OPTIONS.copy()
        if seek_to > 0:
            ffmpeg_opts['before_options'] = f'-ss {seek_to} ' + ffmpeg_opts['before_options']
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = False
        self.current_position = 0  # Seek için gerekli
        self.stay_in_channel = False  # Stay komutu için
        self.timeout_task = None  # Timeout görevi

    def add(self, song):
        self.queue.append(song)

    def get_next(self):
        if self.loop and self.current:
            return self.current
        if self.queue:
            self.current = self.queue.pop(0)
            self.current_position = 0  # Yeni şarkı başladığında sıfırla
            return self.current
        self.current = None
        self.current_position = 0
        return None

    def clear(self):
        self.queue.clear()
        self.current = None
        self.current_position = 0
    
    def shuffle(self):
        """Kuyruğu karıştır"""
        import random
        random.shuffle(self.queue)
    
    def jump_to(self, index):
        """Belirli sıradaki şarkıya atla"""
        if 0 <= index < len(self.queue):
            # İstenen şarkıyı al
            song = self.queue.pop(index)
            # Diğer şarkıları başa al
            self.current = song
            self.current_position = 0
            return song
        return None

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queues = {}  # guild_id: MusicQueue
        self.inactivity_timeout = 300  # 5 dakika (saniye)

    def get_queue(self, guild_id):
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = MusicQueue()
        return self.music_queues[guild_id]
    
    async def start_inactivity_timer(self, guild):
        """İnaktivite zamanlayıcısını başlat"""
        queue = self.get_queue(guild.id)
        
        # Eğer stay aktifse timer başlatma
        if queue.stay_in_channel:
            return
        
        # Eski timer varsa iptal et
        if queue.timeout_task:
            queue.timeout_task.cancel()
        
        # Yeni timer başlat
        queue.timeout_task = asyncio.create_task(self.inactivity_disconnect(guild))
    
    async def inactivity_disconnect(self, guild):
        """Belirtilen süre sonra otomatik çık"""
        try:
            await asyncio.sleep(self.inactivity_timeout)
            
            voice_client = guild.voice_client
            queue = self.get_queue(guild.id)
            
            # Hala inaktif mi ve stay açık değil mi kontrol et
            if voice_client and not voice_client.is_playing() and not queue.stay_in_channel:
                # Kanal bilgisini al
                channel = voice_client.channel
                
                # Bağlantıyı kes
                await voice_client.disconnect()
                
                # Kuyruğu temizle
                queue.clear()
                queue.timeout_task = None
                
                # Bilgilendirme mesajı gönder (text kanalına)
                try:
                    # Son aktif olduğu text kanalını bul
                    for text_channel in guild.text_channels:
                        if text_channel.permissions_for(guild.me).send_messages:
                            embed = discord.Embed(
                                title="⏱️ İnaktivite Zaman Aşımı",
                                description=f"**{self.inactivity_timeout // 60} dakika** boyunca müzik çalmadığım için {channel.mention} kanalından ayrıldım.\n\n💡 `/stay` komutu ile seste kalmamı sağlayabilirsiniz.",
                                color=0xFFA500
                            )
                            await text_channel.send(embed=embed, delete_after=30)
                            break
                except:
                    pass
        except asyncio.CancelledError:
            # Timer iptal edildi, normal durum
            pass
        except Exception as e:
            print(f"Inactivity disconnect hatası: {e}")

    async def play_next(self, guild, seek_to=0):
        queue = self.get_queue(guild.id)
        next_song = queue.get_next()

        if next_song is None:
            # Kuyruk bitti, inaktivite timer'ını başlat
            await self.start_inactivity_timer(guild)
            return

        voice_client = guild.voice_client
        if voice_client and not voice_client.is_playing():
            # Timer'ı iptal et (yeni şarkı çalacak)
            if queue.timeout_task:
                queue.timeout_task.cancel()
                queue.timeout_task = None
            
            player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True, seek_to=seek_to)
            queue.current = next_song
            queue.current_position = seek_to
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild), self.bot.loop
            ))

    @app_commands.command(name="play", description="YouTube'dan müzik çalar veya playlist ekler")
    @app_commands.describe(sarki="YouTube linki, playlist linki veya arama kelimesi")
    async def play(self, interaction: discord.Interaction, sarki: str):
        # Kullanıcı ses kanalında mı?
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Önce bir ses kanalına katılmalısın!", ephemeral=True)

        await interaction.response.defer()

        # Bot ses kanalına bağlan
        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        try:
            # Video/Playlist bilgilerini al
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(sarki, download=False))

            queue = self.get_queue(interaction.guild.id)
            
            # Playlist mı tek şarkı mı?
            if 'entries' in data and len(data['entries']) > 1:
                # PLAYLIST!
                entries = data['entries'][:50]  # Max 50 şarkı
                
                songs = []
                skipped = 0
                for entry in entries:
                    # None veya hatalı videoları atla
                    if not entry or not entry.get('url'):
                        skipped += 1
                        continue
                    
                    try:
                        song = {
                            'url': entry['url'],
                            'title': entry.get('title', 'Bilinmiyor'),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail'),
                            'webpage_url': entry.get('webpage_url', 'https://youtube.com')
                        }
                        songs.append(song)
                        queue.add(song)
                    except Exception as e:
                        print(f"Şarkı eklenemedi: {e}")
                        skipped += 1
                        continue
                
                if not songs:
                    return await interaction.followup.send(
                        "❌ Playlist'teki hiçbir video çalınamadı! Başka bir playlist deneyin.",
                        ephemeral=True
                    )
                
                # Eğer hiç çalmıyorsa ilk şarkıyı başlat
                if not voice_client.is_playing():
                    await self.play_next(interaction.guild)
                
                # Playlist eklendi mesajı
                total_duration = sum(s.get('duration', 0) for s in songs)
                duration_str = f"{total_duration // 60}:{total_duration % 60:02d}" if total_duration else "Bilinmiyor"
                
                embed = discord.Embed(
                    title="📜 Playlist Kuyruğa Eklendi!",
                    description=f"**{data.get('title', 'Playlist')}**",
                    color=0x9B59B6
                )
                embed.add_field(name="🎵 Şarkı Sayısı", value=f"{len(songs)} şarkı", inline=True)
                embed.add_field(name="⏱️ Toplam Süre", value=duration_str, inline=True)
                embed.add_field(name="📊 Sırada", value=f"{len(queue.queue)} şarkı", inline=True)
                
                if skipped > 0:
                    embed.set_footer(text=f"⚠️ {skipped} video atlandı (erişilemiyor)")
                
                await interaction.followup.send(embed=embed)
                
            else:
                # TEK ŞARKI
                if 'entries' in data:
                    data = data['entries'][0]
                
                # Video erişilebilir mi kontrol et
                if not data or not data.get('url'):
                    return await interaction.followup.send(
                        "❌ Bu video çalınamıyor! (Yaş kısıtlaması, telif hakkı veya coğrafi engel olabilir)",
                        ephemeral=True
                    )

                song = {
                    'url': data['url'],
                    'title': data.get('title', 'Bilinmiyor'),
                    'duration': data.get('duration', 0),
                    'thumbnail': data.get('thumbnail'),
                    'webpage_url': data.get('webpage_url', 'https://youtube.com')
                }

                # Eğer şu an çalıyorsa kuyruğa ekle
                if voice_client.is_playing():
                    queue.add(song)
                    
                    duration_str = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song['duration'] else "Bilinmiyor"
                    
                    embed = discord.Embed(
                        title="➕ Kuyruğa Eklendi",
                        description=f"[{song['title']}]({song['webpage_url']})",
                        color=0x00FF00
                    )
                    embed.add_field(name="⏱️ Süre", value=duration_str, inline=True)
                    embed.add_field(name="📊 Sırada", value=f"{len(queue.queue)} şarkı", inline=True)
                    if song.get('thumbnail'):
                        embed.set_thumbnail(url=song['thumbnail'])
                    
                    await interaction.followup.send(embed=embed)
                else:
                    # Direkt çal
                    queue.add(song)
                    await self.play_next(interaction.guild)
                    
                    duration_str = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song['duration'] else "Bilinmiyor"
                    
                    embed = discord.Embed(
                        title="🎵 Şimdi Çalıyor",
                        description=f"[{song['title']}]({song['webpage_url']})",
                        color=0x5865F2
                    )
                    embed.add_field(name="⏱️ Süre", value=duration_str, inline=True)
                    embed.add_field(name="🎧 Talep Eden", value=interaction.user.mention, inline=True)
                    if song.get('thumbnail'):
                        embed.set_thumbnail(url=song['thumbnail'])
                    
                    await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Play hatası: {e}")
            await interaction.followup.send(
                f"❌ Video çalınamadı! Sebep: {str(e)[:100]}\n💡 Farklı bir şarkı/link deneyin.",
                ephemeral=True
            )

    @app_commands.command(name="pause", description="Müziği duraklatır")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            # Durakladığında timer başlat
            await self.start_inactivity_timer(interaction.guild)
            await interaction.response.send_message("⏸️ Müzik duraklatıldı!")
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)

    @app_commands.command(name="resume", description="Müziği devam ettirir")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            # Devam ettiğinde timer'ı iptal et
            if queue.timeout_task:
                queue.timeout_task.cancel()
                queue.timeout_task = None
            await interaction.response.send_message("▶️ Müzik devam ediyor!")
        else:
            await interaction.response.send_message("❌ Müzik zaten çalıyor!", ephemeral=True)

    @app_commands.command(name="skip", description="Şarkıyı atlar")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏭️ Şarkı atlandı!")
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)

    @app_commands.command(name="stop", description="Müziği durdurur ve kuyrugu temizler")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)

        if voice_client:
            queue.clear()
            queue.stay_in_channel = False
            # Timer'ı iptal et
            if queue.timeout_task:
                queue.timeout_task.cancel()
                queue.timeout_task = None
            
            voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("⏹️ Müzik durduruldu ve kuyruk temizlendi!")
        else:
            await interaction.response.send_message("❌ Bot ses kanalında değil!", ephemeral=True)

    @app_commands.command(name="queue", description="Müzik kuyruğunu gösterir")
    async def queue_command(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current and not queue.queue:
            return await interaction.response.send_message("❌ Kuyruk boş!", ephemeral=True)

        embed = discord.Embed(
            title="🎵 Müzik Kuyruğu",
            color=0x5865F2
        )

        if queue.current:
            duration_str = f"{queue.current['duration'] // 60}:{queue.current['duration'] % 60:02d}" if queue.current.get('duration') else "Bilinmiyor"
            embed.add_field(
                name="▶️ Şimdi Çalıyor",
                value=f"**[{queue.current['title']}]({queue.current.get('webpage_url', 'https://youtube.com')})**\nSüre: {duration_str}",
                inline=False
            )

        if queue.queue:
            queue_text = ""
            for i, song in enumerate(queue.queue[:10], 1):
                duration_str = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song.get('duration') else "?"
                queue_text += f"`{i}.` [{song['title'][:50]}]({song.get('webpage_url', 'https://youtube.com')}) `[{duration_str}]`\n"
            
            if len(queue.queue) > 10:
                queue_text += f"\n... ve {len(queue.queue) - 10} şarkı daha"
            
            embed.add_field(name="📜 Sırada", value=queue_text, inline=False)

        embed.set_footer(text=f"Toplam: {len(queue.queue)} şarkı")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Şu an çalan şarkıyı gösterir")
    async def nowplaying(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current:
            return await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)

        song = queue.current
        duration_str = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song.get('duration') else "Bilinmiyor"

        embed = discord.Embed(
            title="🎶 Şimdi Çalıyor",
            description=f"[{song['title']}]({song.get('webpage_url', 'https://youtube.com')})",
            color=0xFF6B6B
        )
        embed.add_field(name="⏱️ Süre", value=duration_str, inline=True)
        
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Ses seviyesini ayarlar")
    @app_commands.describe(seviye="Ses seviyesi (0-100)")
    async def volume(self, interaction: discord.Interaction, seviye: int):
        if seviye < 0 or seviye > 100:
            return await interaction.response.send_message("❌ Ses seviyesi 0-100 arası olmalı!", ephemeral=True)

        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.source:
            voice_client.source.volume = seviye / 100
            await interaction.response.send_message(f"🔊 Ses seviyesi **{seviye}%** olarak ayarlandı!")
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)

    @app_commands.command(name="loop", description="Mevcut şarkıyı tekrarlar")
    async def loop(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        queue.loop = not queue.loop

        if queue.loop:
            await interaction.response.send_message("🔁 Tekrar modu **açık**!")
        else:
            await interaction.response.send_message("🔁 Tekrar modu **kapalı**!")
    
    @app_commands.command(name="seek", description="Şarkının belirli bir saniyesine atlar")
    @app_commands.describe(zaman="Atlanacak zaman (saniye veya mm:ss formatında)")
    async def seek(self, interaction: discord.Interaction, zaman: str):
        # ÖNCELİKLE defer - zaman aşımını önler
        await interaction.response.defer()
        
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            return await interaction.followup.send("❌ Şu an çalan bir şarkı yok!", ephemeral=True)
        
        if not queue.current:
            return await interaction.followup.send("❌ Kuyrukta şarkı yok!", ephemeral=True)
        
        try:
            # Zaman formatını parse et (saniye veya mm:ss)
            if ':' in zaman:
                parts = zaman.split(':')
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = int(zaman)
            
            # Şarkı süresini kontrol et
            duration = queue.current.get('duration', 0)
            if duration and seconds >= duration:
                return await interaction.followup.send(
                    f"❌ Şarkı süresi {duration} saniye! Daha kısa bir zaman girin.",
                    ephemeral=True
                )
            
            if seconds < 0:
                return await interaction.followup.send("❌ Zaman 0'dan küçük olamaz!", ephemeral=True)
            
            # Mevcut şarkı URL'ini kontrol et
            if not queue.current.get('url'):
                return await interaction.followup.send("❌ Şarkı URL'si bulunamadı!", ephemeral=True)
            
            # Mevcut şarkıyı durdur
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)  # Durması için kısa bekleme
            
            # Aynı şarkıyı belirtilen yerden başlat
            player = await YTDLSource.from_url(
                queue.current['url'], 
                loop=self.bot.loop, 
                stream=True, 
                seek_to=seconds
            )
            queue.current_position = seconds
            
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction.guild), self.bot.loop
            ))
            
            # Zaman gösterimi
            time_str = f"{seconds // 60}:{seconds % 60:02d}"
            
            embed = discord.Embed(
                title="⏩ Şarkı İleri Sarıldı",
                description=f"**{queue.current.get('title', 'Bilinmiyor')}**",
                color=0xFFD700
            )
            embed.add_field(name="⏱️ Konum", value=time_str, inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except ValueError:
            await interaction.followup.send(
                "❌ Geçersiz zaman formatı! Örnek: `30` (30 saniye) veya `1:30` (1 dakika 30 saniye)",
                ephemeral=True
            )
        except Exception as e:
            print(f"Seek hatası: {e}")
            await interaction.followup.send(f"❌ Seek hatası: Şarkı yeniden başlatılıyor...", ephemeral=True)
            # Hata olursa şarkıyı baştan başlat
            try:
                if voice_client.is_playing():
                    voice_client.stop()
                await self.play_next(interaction.guild)
            except:
                pass
    
    @app_commands.command(name="shuffle", description="Kuyruktaki şarkıları karıştırır")
    async def shuffle(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        
        if not queue.queue:
            return await interaction.response.send_message("❌ Kuyruk boş!", ephemeral=True)
        
        if len(queue.queue) < 2:
            return await interaction.response.send_message("❌ Karıştırmak için en az 2 şarkı olmalı!", ephemeral=True)
        
        queue.shuffle()
        
        embed = discord.Embed(
            title="🔀 Kuyruk Karıştırıldı!",
            description=f"**{len(queue.queue)}** şarkı rastgele sıralandı!",
            color=0x9B59B6
        )
        
        # İlk 5 şarkıyı göster
        if queue.queue:
            preview = "\n".join([
                f"`{i+1}.` {song['title'][:40]}..."
                for i, song in enumerate(queue.queue[:5])
            ])
            if len(queue.queue) > 5:
                preview += f"\n... ve {len(queue.queue) - 5} şarkı daha"
            embed.add_field(name="🎵 Yeni Sıralama (İlk 5)", value=preview, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="jump", description="Kuyruktaki belirli bir şarkıya atlar")
    @app_commands.describe(sira="Atlanacak şarkının sıra numarası (1'den başlar)")
    async def jump(self, interaction: discord.Interaction, sira: int):
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)
        
        if not voice_client:
            return await interaction.response.send_message("❌ Bot ses kanalında değil!", ephemeral=True)
        
        if not queue.queue:
            return await interaction.response.send_message("❌ Kuyruk boş!", ephemeral=True)
        
        # Sıra numarasını array index'e çevir
        index = sira - 1
        
        if index < 0 or index >= len(queue.queue):
            return await interaction.response.send_message(
                f"❌ Geçersiz sıra numarası! Kuyrukta 1-{len(queue.queue)} arası şarkı var.",
                ephemeral=True
            )
        
        await interaction.response.defer()
        
        # İstenen şarkıya atla
        song = queue.jump_to(index)
        
        if song:
            # Mevcut şarkıyı durdur
            if voice_client.is_playing():
                voice_client.stop()
            
            # Yeni şarkıyı çal
            player = await YTDLSource.from_url(song['url'], loop=self.bot.loop, stream=True)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction.guild), self.bot.loop
            ))
            
            duration_str = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song.get('duration') else "Bilinmiyor"
            
            embed = discord.Embed(
                title=f"⏭️ {sira}. Şarkıya Atlandı",
                description=f"[{song['title']}]({song.get('webpage_url', 'https://youtube.com')})",
                color=0x00FF00
            )
            embed.add_field(name="⏱️ Süre", value=duration_str, inline=True)
            embed.add_field(name="📊 Kalan Kuyruk", value=f"{len(queue.queue)} şarkı", inline=True)
            
            if song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Şarkıya atlanamadı!", ephemeral=True)
    
    @app_commands.command(name="remove", description="Kuyruktan belirli bir şarkıyı kaldırır")
    @app_commands.describe(sira="Kaldırılacak şarkının sıra numarası (1'den başlar)")
    async def remove(self, interaction: discord.Interaction, sira: int):
        queue = self.get_queue(interaction.guild.id)
        
        if not queue.queue:
            return await interaction.response.send_message("❌ Kuyruk boş!", ephemeral=True)
        
        index = sira - 1
        
        if index < 0 or index >= len(queue.queue):
            return await interaction.response.send_message(
                f"❌ Geçersiz sıra numarası! Kuyrukta 1-{len(queue.queue)} arası şarkı var.",
                ephemeral=True
            )
        
        removed_song = queue.queue.pop(index)
        
        embed = discord.Embed(
            title="🗑️ Şarkı Kuyruktan Kaldırıldı",
            description=f"**{removed_song['title']}**",
            color=0xFF0000
        )
        embed.add_field(name="📊 Kalan Kuyruk", value=f"{len(queue.queue)} şarkı", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stay", description="Bot seste inaktif olsa bile kanalda kalır")
    async def stay(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            return await interaction.response.send_message("❌ Bot ses kanalında değil!", ephemeral=True)
        
        queue = self.get_queue(interaction.guild.id)
        queue.stay_in_channel = not queue.stay_in_channel
        
        if queue.stay_in_channel:
            # Timer'ı iptal et
            if queue.timeout_task:
                queue.timeout_task.cancel()
                queue.timeout_task = None
            
            embed = discord.Embed(
                title="🔒 Stay Modu Açık",
                description=f"Bot artık {voice_client.channel.mention} kanalında kalacak!\n\nİnaktif olsam bile otomatik çıkmayacağım.",
                color=0x00FF00
            )
            embed.set_footer(text="💡 Kapatmak için tekrar /stay kullanın")
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="🔓 Stay Modu Kapalı",
                description=f"Bot artık inaktif olduğunda **{self.inactivity_timeout // 60} dakika** sonra otomatik çıkacak.",
                color=0xFFA500
            )
            await interaction.response.send_message(embed=embed)
            
            # Eğer şu an inaktifse timer'ı başlat
            if not voice_client.is_playing():
                await self.start_inactivity_timer(interaction.guild)
    
    @app_commands.command(name="disconnect", description="Botu ses kanalından çıkarır")
    async def disconnect(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)
        
        if not voice_client:
            return await interaction.response.send_message("❌ Bot zaten ses kanalında değil!", ephemeral=True)
        
        channel_name = voice_client.channel.name
        
        # Kuyruğu temizle
        queue.clear()
        queue.stay_in_channel = False
        
        # Timer'ı iptal et
        if queue.timeout_task:
            queue.timeout_task.cancel()
            queue.timeout_task = None
        
        # Bağlantıyı kes
        await voice_client.disconnect()
        
        embed = discord.Embed(
            title="👋 Ses Kanalından Ayrıldım",
            description=f"**#{channel_name}** kanalından ayrıldım.\n\nKuyruk temizlendi.",
            color=0xFF6B6B
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leave", description="Botu ses kanalından çıkarır")
    async def leave(self, interaction: discord.Interaction):
        """Disconnect komutunun alias'ı - aynı kodu çalıştırır"""
        voice_client = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)
        
        if not voice_client:
            return await interaction.response.send_message("❌ Bot zaten ses kanalında değil!", ephemeral=True)
        
        channel_name = voice_client.channel.name
        
        # Kuyruğu temizle
        queue.clear()
        queue.stay_in_channel = False
        
        # Timer'ı iptal et
        if queue.timeout_task:
            queue.timeout_task.cancel()
            queue.timeout_task = None
        
        # Bağlantıyı kes
        await voice_client.disconnect()
        
        embed = discord.Embed(
            title="👋 Ses Kanalından Ayrıldım",
            description=f"**#{channel_name}** kanalından ayrıldım.\n\nKuyruk temizlendi.",
            color=0xFF6B6B
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="musictimeout", description="Müzik inaktivite zaman aşımı süresini ayarlar (Admin)")
    @app_commands.describe(dakika="Dakika cinsinden süre (0=kapalı, 1-60 arası)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_timeout(self, interaction: discord.Interaction, dakika: int):
        if dakika < 0 or dakika > 60:
            return await interaction.response.send_message("❌ Süre 0-60 dakika arası olmalı!", ephemeral=True)
        
        if dakika == 0:
            self.inactivity_timeout = 999999999  # Çok uzun süre (pratikte kapalı)
            await interaction.response.send_message("✅ İnaktivite zaman aşımı **kapatıldı**!")
        else:
            self.inactivity_timeout = dakika * 60
            await interaction.response.send_message(
                f"✅ İnaktivite zaman aşımı **{dakika} dakika** olarak ayarlandı!"
            )

async def setup(bot):
    await bot.add_cog(Music(bot))
