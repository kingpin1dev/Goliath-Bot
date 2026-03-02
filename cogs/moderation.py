import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Kick komutu
    @app_commands.command(name="kick", description="Bir kullanıcıyı sunucudan atar")
    @app_commands.describe(
        kullanici="Atılacak kullanıcı",
        sebep="Atılma sebebi"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if kullanici.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Bu kullanıcıyı atamazsınız!", ephemeral=True)
        
        try:
            # DM gönder
            try:
                embed = discord.Embed(
                    title="🚪 Sunucudan Atıldınız",
                    description=f"**Sunucu:** {interaction.guild.name}\n**Sebep:** {sebep}\n**Yetkili:** {interaction.user}",
                    color=0xFF6B6B,
                    timestamp=datetime.now()
                )
                await kullanici.send(embed=embed)
            except:
                pass
            
            await kullanici.kick(reason=f"{interaction.user}: {sebep}")
            
            embed = discord.Embed(
                title="✅ Kullanıcı Atıldı",
                color=0x00FF00
            )
            embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention} (`{kullanici.id}`)", inline=False)
            embed.add_field(name="📝 Sebep", value=sebep, inline=False)
            embed.add_field(name="👮 Yetkili", value=interaction.user.mention, inline=False)
            embed.timestamp = datetime.now()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Ban komutu
    @app_commands.command(name="ban", description="Bir kullanıcıyı sunucudan yasaklar")
    @app_commands.describe(
        kullanici="Yasaklanacak kullanıcı",
        sebep="Yasaklanma sebebi",
        mesaj_sil="Kaç günlük mesajları silinsin (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi", mesaj_sil: int = 0):
        if kullanici.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Bu kullanıcıyı yasaklayamazsınız!", ephemeral=True)
        
        if mesaj_sil < 0 or mesaj_sil > 7:
            return await interaction.response.send_message("❌ Mesaj silme süresi 0-7 gün arası olmalı!", ephemeral=True)
        
        try:
            # DM gönder
            try:
                embed = discord.Embed(
                    title="🔨 Sunucudan Yasaklandınız",
                    description=f"**Sunucu:** {interaction.guild.name}\n**Sebep:** {sebep}\n**Yetkili:** {interaction.user}",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                await kullanici.send(embed=embed)
            except:
                pass
            
            await kullanici.ban(reason=f"{interaction.user}: {sebep}", delete_message_days=mesaj_sil)
            
            embed = discord.Embed(
                title="✅ Kullanıcı Yasaklandı",
                color=0xFF0000
            )
            embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention} (`{kullanici.id}`)", inline=False)
            embed.add_field(name="📝 Sebep", value=sebep, inline=False)
            embed.add_field(name="🗑️ Silinen Mesajlar", value=f"Son {mesaj_sil} gün", inline=False)
            embed.add_field(name="👮 Yetkili", value=interaction.user.mention, inline=False)
            embed.timestamp = datetime.now()
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Unban komutu
    @app_commands.command(name="unban", description="Bir kullanıcının yasağını kaldırır")
    @app_commands.describe(kullanici_id="Yasağı kaldırılacak kullanıcının ID'si")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, kullanici_id: str):
        try:
            user_id = int(kullanici_id)
            user = await self.bot.fetch_user(user_id)
            
            await interaction.guild.unban(user, reason=f"{interaction.user} tarafından yasak kaldırıldı")
            
            embed = discord.Embed(
                title="✅ Yasak Kaldırıldı",
                description=f"**{user}** (`{user.id}`) artık sunucuya girebilir.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Yetkili: {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Geçersiz kullanıcı ID'si!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ Bu kullanıcı yasaklı değil!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Timeout komutu
    @app_commands.command(name="timeout", description="Bir kullanıcıyı geçici olarak susturur")
    @app_commands.describe(
        kullanici="Susturulacak kullanıcı",
        sure="Süre (örn: 5m, 1h, 1d)",
        sebep="Susturma sebebi"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, kullanici: discord.Member, sure: str, sebep: str = "Sebep belirtilmedi"):
        if kullanici.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Bu kullanıcıyı susturamazsınız!", ephemeral=True)
        
        # Süre hesaplama
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = sure[-1]
            amount = int(sure[:-1])
            seconds = amount * time_dict[unit]
            
            if seconds > 2419200:  # Max 28 gün
                return await interaction.response.send_message("❌ Maximum timeout süresi 28 gündür!", ephemeral=True)
            
            duration = timedelta(seconds=seconds)
            
            await kullanici.timeout(duration, reason=f"{interaction.user}: {sebep}")
            
            # Süre gösterimi
            sure_text = f"{amount} {'saniye' if unit == 's' else 'dakika' if unit == 'm' else 'saat' if unit == 'h' else 'gün'}"
            
            embed = discord.Embed(
                title="🔇 Kullanıcı Susturuldu",
                color=0xFFA500
            )
            embed.add_field(name="👤 Kullanıcı", value=kullanici.mention, inline=False)
            embed.add_field(name="⏱️ Süre", value=sure_text, inline=False)
            embed.add_field(name="📝 Sebep", value=sebep, inline=False)
            embed.add_field(name="👮 Yetkili", value=interaction.user.mention, inline=False)
            embed.timestamp = datetime.now()
            
            await interaction.response.send_message(embed=embed)
            
        except (KeyError, ValueError):
            await interaction.response.send_message("❌ Geçersiz süre formatı! Örnek: 5m, 1h, 1d", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Untimeout komutu
    @app_commands.command(name="untimeout", description="Bir kullanıcının timeout'unu kaldırır")
    @app_commands.describe(kullanici="Timeout'u kaldırılacak kullanıcı")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, kullanici: discord.Member):
        try:
            await kullanici.timeout(None, reason=f"{interaction.user} tarafından timeout kaldırıldı")
            
            embed = discord.Embed(
                title="✅ Timeout Kaldırıldı",
                description=f"{kullanici.mention} artık konuşabilir.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Clear komutu
    @app_commands.command(name="clear", description="Belirtilen sayıda mesajı siler")
    @app_commands.describe(miktar="Silinecek mesaj sayısı (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, miktar: int):
        if miktar < 1 or miktar > 100:
            return await interaction.response.send_message("❌ Mesaj sayısı 1-100 arası olmalı!", ephemeral=True)
        
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=miktar)
            
            await interaction.followup.send(f"✅ {len(deleted)} mesaj silindi!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}", ephemeral=True)
    
    # Slowmode komutu
    @app_commands.command(name="slowmode", description="Yavaş modu ayarlar")
    @app_commands.describe(saniye="Yavaş mod süresi (0-21600 saniye, 0=kapat)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, saniye: int):
        if saniye < 0 or saniye > 21600:
            return await interaction.response.send_message("❌ Yavaş mod 0-21600 saniye (6 saat) arası olmalı!", ephemeral=True)
        
        try:
            await interaction.channel.edit(slowmode_delay=saniye)
            
            if saniye == 0:
                await interaction.response.send_message("✅ Yavaş mod kapatıldı!")
            else:
                await interaction.response.send_message(f"✅ Yavaş mod {saniye} saniye olarak ayarlandı!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Lock komutu
    @app_commands.command(name="lock", description="Kanalı kilitler")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔒 Kanal Kilitlendi",
                description=f"{interaction.channel.mention} kanalı kilitlendi.",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Yetkili: {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Unlock komutu
    @app_commands.command(name="unlock", description="Kanal kilidini açar")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = True
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔓 Kanal Kilidi Açıldı",
                description=f"{interaction.channel.mention} kanalı açıldı.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Yetkili: {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Nuke komutu
    @app_commands.command(name="nuke", description="Kanalı siler ve yeniden oluşturur")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        channel = interaction.channel
        position = channel.position
        
        await interaction.response.send_message("💣 Kanal yeniden oluşturuluyor...", ephemeral=True)
        
        new_channel = await channel.clone()
        await new_channel.edit(position=position)
        await channel.delete()
        
        embed = discord.Embed(
            title="💥 Kanal Temizlendi!",
            description=f"Kanal {interaction.user.mention} tarafından yeniden oluşturuldu.",
            color=0xFF6B6B
        )
        await new_channel.send(embed=embed)
    
    # Warn komutu
    @app_commands.command(name="warn", description="Kullanıcıya uyarı verir")
    @app_commands.describe(
        kullanici="Uyarılacak kullanıcı",
        sebep="Uyarı sebebi"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
        timestamp = int(datetime.now().timestamp())
        
        await self.bot.db.execute(
            'INSERT INTO warnings (user_id, guild_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)',
            (kullanici.id, interaction.guild.id, interaction.user.id, sebep, timestamp)
        )
        await self.bot.db.commit()
        
        # Toplam uyarı sayısı
        async with self.bot.db.execute(
            'SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            count = (await cursor.fetchone())[0]
        
        # DM gönder
        try:
            dm_embed = discord.Embed(
                title="⚠️ Uyarı Aldınız",
                description=f"**Sunucu:** {interaction.guild.name}\n**Sebep:** {sebep}\n**Toplam Uyarı:** {count}",
                color=0xFFAA00,
                timestamp=datetime.now()
            )
            dm_embed.set_footer(text=f"Yetkili: {interaction.user}")
            await kullanici.send(embed=dm_embed)
        except:
            pass
        
        embed = discord.Embed(
            title="⚠️ Uyarı Verildi",
            color=0xFFAA00
        )
        embed.add_field(name="👤 Kullanıcı", value=kullanici.mention, inline=False)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.add_field(name="🔢 Toplam Uyarı", value=str(count), inline=False)
        embed.add_field(name="👮 Yetkili", value=interaction.user.mention, inline=False)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
    
    # Warnings komutu
    @app_commands.command(name="warnings", description="Kullanıcının uyarılarını gösterir")
    @app_commands.describe(kullanici="Uyarıları görüntülenecek kullanıcı")
    async def warnings(self, interaction: discord.Interaction, kullanici: discord.Member):
        async with self.bot.db.execute(
            'SELECT id, moderator_id, reason, timestamp FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            warnings = await cursor.fetchall()
        
        if not warnings:
            return await interaction.response.send_message(f"✅ {kullanici.mention} hiç uyarı almamış!", ephemeral=True)
        
        embed = discord.Embed(
            title=f"⚠️ {kullanici} - Uyarılar ({len(warnings)})",
            color=0xFFAA00
        )
        
        for i, (warn_id, mod_id, reason, timestamp) in enumerate(warnings[:10], 1):
            moderator = interaction.guild.get_member(mod_id)
            mod_name = moderator.mention if moderator else f"ID: {mod_id}"
            
            warn_time = datetime.fromtimestamp(timestamp)
            
            embed.add_field(
                name=f"#{i} - ID: {warn_id}",
                value=f"**Sebep:** {reason}\n**Yetkili:** {mod_name}\n**Tarih:** <t:{timestamp}:R>",
                inline=False
            )
        
        if len(warnings) > 10:
            embed.set_footer(text=f"Ve {len(warnings) - 10} uyarı daha...")
        
        await interaction.response.send_message(embed=embed)
    
    # Clear warnings komutu
    @app_commands.command(name="clearwarnings", description="Kullanıcının tüm uyarılarını siler")
    @app_commands.describe(kullanici="Uyarıları silinecek kullanıcı")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarnings(self, interaction: discord.Interaction, kullanici: discord.Member):
        await self.bot.db.execute(
            'DELETE FROM warnings WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        )
        await self.bot.db.commit()
        
        await interaction.response.send_message(f"✅ {kullanici.mention} adlı kullanıcının tüm uyarıları silindi!")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
