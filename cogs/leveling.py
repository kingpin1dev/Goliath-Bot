import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # XP spam önleme
    
    def calculate_xp_for_level(self, level):
        """Bir seviye için gereken toplam XP'yi hesapla"""
        return 5 * (level ** 2) + 50 * level + 100
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Cooldown kontrolü (60 saniye)
        user_key = f"{message.author.id}_{message.guild.id}"
        current_time = datetime.now().timestamp()
        
        if user_key in self.cooldowns:
            if current_time - self.cooldowns[user_key] < 60:
                return
        
        self.cooldowns[user_key] = current_time
        
        # Random XP ver (15-25 arası)
        xp_gain = random.randint(15, 25)
        
        # Kullanıcının mevcut XP ve seviyesini al
        async with self.bot.db.execute(
            'SELECT xp, level, messages FROM levels WHERE user_id = ? AND guild_id = ?',
            (message.author.id, message.guild.id)
        ) as cursor:
            data = await cursor.fetchone()
        
        if data:
            current_xp, current_level, messages = data
            new_xp = current_xp + xp_gain
            new_messages = messages + 1
        else:
            current_xp = 0
            current_level = 0
            new_xp = xp_gain
            new_messages = 1
        
        # Seviye atladı mı kontrol et
        required_xp = self.calculate_xp_for_level(current_level + 1)
        leveled_up = False
        new_level = current_level
        
        while new_xp >= required_xp:
            new_level += 1
            new_xp -= required_xp
            required_xp = self.calculate_xp_for_level(new_level + 1)
            leveled_up = True
        
        # Veritabanını güncelle
        await self.bot.db.execute('''
            INSERT INTO levels (user_id, guild_id, xp, level, messages)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                xp = ?,
                level = ?,
                messages = ?
        ''', (message.author.id, message.guild.id, new_xp, new_level, new_messages,
              new_xp, new_level, new_messages))
        await self.bot.db.commit()
        
        # Seviye atlama mesajı
        if leveled_up:
            embed = discord.Embed(
                title="🎉 Seviye Atladı!",
                description=f"{message.author.mention} **Seviye {new_level}** oldu!",
                color=0xFFD700
            )
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else None)
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
    
    @app_commands.command(name="rank", description="Seviye ve XP bilgilerinizi gösterir")
    @app_commands.describe(kullanici="Rank'i görüntülenecek kullanıcı")
    async def rank(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        
        async with self.bot.db.execute(
            'SELECT xp, level, messages FROM levels WHERE user_id = ? AND guild_id = ?',
            (kullanici.id, interaction.guild.id)
        ) as cursor:
            data = await cursor.fetchone()
        
        if not data:
            return await interaction.response.send_message(
                f"❌ {kullanici.mention} henüz XP kazanmamış!",
                ephemeral=True
            )
        
        xp, level, messages = data
        
        # Sıralama
        async with self.bot.db.execute(
            'SELECT COUNT(*) FROM levels WHERE guild_id = ? AND (level > ? OR (level = ? AND xp > ?))',
            (interaction.guild.id, level, level, xp)
        ) as cursor:
            rank = (await cursor.fetchone())[0] + 1
        
        # Bir sonraki seviye için gereken XP
        next_level_xp = self.calculate_xp_for_level(level + 1)
        
        embed = discord.Embed(
            title=f"📊 {kullanici.name} - Seviye Bilgisi",
            color=0x5865F2
        )
        
        embed.add_field(name="🎖️ Seviye", value=f"```{level}```", inline=True)
        embed.add_field(name="⭐ XP", value=f"```{xp}/{next_level_xp}```", inline=True)
        embed.add_field(name="🏆 Sıralama", value=f"```#{rank}```", inline=True)
        embed.add_field(name="💬 Mesajlar", value=f"```{messages:,}```", inline=True)
        
        # Progress bar
        progress = int((xp / next_level_xp) * 20)
        bar = "▰" * progress + "▱" * (20 - progress)
        embed.add_field(name="📈 İlerleme", value=f"`{bar}` {int((xp/next_level_xp)*100)}%", inline=False)
        
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else None)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Sunucunun seviye sıralamasını gösterir")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.bot.db.execute(
            'SELECT user_id, xp, level, messages FROM levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10',
            (interaction.guild.id,)
        ) as cursor:
            top_users = await cursor.fetchall()
        
        if not top_users:
            return await interaction.response.send_message("❌ Henüz kimse XP kazanmamış!", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} - Liderlik Tablosu",
            color=0xFFD700
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, xp, level, messages) in enumerate(top_users, 1):
            user = interaction.guild.get_member(user_id)
            if not user:
                continue
            
            medal = medals[i-1] if i <= 3 else f"**#{i}**"
            
            embed.add_field(
                name=f"{medal} {user.name}",
                value=f"Seviye: `{level}` • XP: `{xp}` • Mesajlar: `{messages:,}`",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Toplam {len(top_users)} kullanıcı listelendi")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setlevel", description="Kullanıcının seviyesini ayarlar (Admin)")
    @app_commands.describe(
        kullanici="Seviyesi ayarlanacak kullanıcı",
        seviye="Yeni seviye"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setlevel(self, interaction: discord.Interaction, kullanici: discord.Member, seviye: int):
        if seviye < 0 or seviye > 1000:
            return await interaction.response.send_message("❌ Seviye 0-1000 arası olmalı!", ephemeral=True)
        
        await self.bot.db.execute('''
            INSERT INTO levels (user_id, guild_id, xp, level, messages)
            VALUES (?, ?, 0, ?, 0)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                level = ?,
                xp = 0
        ''', (kullanici.id, interaction.guild.id, seviye, seviye))
        await self.bot.db.commit()
        
        embed = discord.Embed(
            title="✅ Seviye Ayarlandı",
            description=f"{kullanici.mention} artık **Seviye {seviye}**!",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Yetkili: {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
