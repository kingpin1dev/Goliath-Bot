import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="memberstats", description="Kullanıcı istatistiklerini gösterir")
    @app_commands.describe(kullanici="İstatistikleri görüntülenecek kullanıcı")
    async def memberstats(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        
        # Member stats al
        async with self.bot.db.execute(
            'SELECT messages_sent, voice_time, joins FROM member_stats WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            stats_data = await cursor.fetchone()
        
        if stats_data:
            messages, voice_time, joins = stats_data
        else:
            messages, voice_time, joins = 0, 0, 0
        
        # Level bilgisi al
        async with self.bot.db.execute(
            'SELECT level, xp FROM levels WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            level_data = await cursor.fetchone()
        
        if level_data:
            level, xp = level_data
        else:
            level, xp = 0, 0
        
        # Uyarı sayısı
        async with self.bot.db.execute(
            'SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            warnings = (await cursor.fetchone())[0]
        
        embed = discord.Embed(
            title=f"📊 {kullanici} - Üye İstatistikleri",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        # Genel bilgiler
        embed.add_field(name="🆔 ID", value=f"`{kullanici.id}`", inline=True)
        embed.add_field(name="📅 Katılma Tarihi", value=f"<t:{int(kullanici.joined_at.timestamp())}:R>" if kullanici.joined_at else "Bilinmiyor", inline=True)
        embed.add_field(name="🎂 Hesap Yaşı", value=f"<t:{int(kullanici.created_at.timestamp())}:R>", inline=True)
        
        # İstatistikler
        embed.add_field(name="💬 Gönderilen Mesajlar", value=f"```{messages:,}```", inline=True)
        embed.add_field(name="🎖️ Seviye", value=f"```{level}```", inline=True)
        embed.add_field(name="⭐ XP", value=f"```{xp:,}```", inline=True)
        
        # Ses süresi (saniyeyi saate çevir)
        hours = voice_time // 3600
        minutes = (voice_time % 3600) // 60
        voice_text = f"{hours}s {minutes}d" if hours > 0 else f"{minutes}d"
        
        embed.add_field(name="🎤 Ses Kanalı Süresi", value=f"```{voice_text}```", inline=True)
        embed.add_field(name="⚠️ Uyarılar", value=f"```{warnings}```", inline=True)
        embed.add_field(name="🔄 Sunucuya Katılma Sayısı", value=f"```{joins}```", inline=True)
        
        # Roller
        roles = [role.mention for role in sorted(kullanici.roles[1:], reverse=True)][:10]
        if roles:
            embed.add_field(name=f"🎭 Roller ({len(kullanici.roles)-1})", value=" ".join(roles), inline=False)
        
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else None)
        embed.set_footer(text=f"Sunucu: {interaction.guild.name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
