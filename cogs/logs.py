import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_log_channel(self, guild_id, log_type):
        """Log kanalını al"""
        async with self.bot.db.execute(
            f'SELECT {log_type} FROM log_settings WHERE guild_id = ?',
            (guild_id,)
        ) as cursor:
            data = await cursor.fetchone()
        return data[0] if data and data[0] else None
    
    @app_commands.command(name="setlog", description="Log kanallarını ayarlar")
    @app_commands.describe(
        tip="Log tipi",
        kanal="Log kanalı (boş bırakırsanız kapatılır)"
    )
    @app_commands.choices(tip=[
        app_commands.Choice(name="Mesaj Logları", value="message_log"),
        app_commands.Choice(name="Üye Logları", value="member_log"),
        app_commands.Choice(name="Rol Logları", value="role_log"),
        app_commands.Choice(name="Kanal Logları", value="channel_log"),
        app_commands.Choice(name="Moderasyon Logları", value="moderation_log"),
        app_commands.Choice(name="Ses Kanalı Logları", value="voice_log"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def setlog(self, interaction: discord.Interaction, tip: str, kanal: discord.TextChannel = None):
        channel_id = kanal.id if kanal else None
        
        await self.bot.db.execute(f'''
            INSERT INTO log_settings (guild_id, {tip})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                {tip} = ?
        ''', (interaction.guild.id, channel_id, channel_id))
        await self.bot.db.commit()
        
        tip_names = {
            "message_log": "Mesaj Logları",
            "member_log": "Üye Logları",
            "role_log": "Rol Logları",
            "channel_log": "Kanal Logları",
            "moderation_log": "Moderasyon Logları",
            "voice_log": "Ses Kanalı Logları"
        }
        
        if kanal:
            await interaction.response.send_message(
                f"✅ **{tip_names[tip]}** {kanal.mention} kanalına ayarlandı!"
            )
        else:
            await interaction.response.send_message(
                f"✅ **{tip_names[tip]}** kapatıldı!"
            )
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        channel_id = await self.get_log_channel(message.guild.id, 'message_log')
        if not channel_id:
            return
        
        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🗑️ Mesaj Silindi",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Kullanıcı", value=message.author.mention, inline=True)
        embed.add_field(name="📢 Kanal", value=message.channel.mention, inline=True)
        if message.content:
            embed.add_field(name="💬 Mesaj", value=message.content[:1024], inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        
        channel_id = await self.get_log_channel(before.guild.id, 'message_log')
        if not channel_id:
            return
        
        log_channel = before.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="✏️ Mesaj Düzenlendi",
            color=0xFFA500,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Kullanıcı", value=before.author.mention, inline=True)
        embed.add_field(name="📢 Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="📝 Eski Mesaj", value=before.content[:512] or "Yok", inline=False)
        embed.add_field(name="📝 Yeni Mesaj", value=after.content[:512] or "Yok", inline=False)
        embed.add_field(name="🔗 Link", value=f"[Git]({after.jump_url})", inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = await self.get_log_channel(member.guild.id, 'member_log')
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="📥 Üye Katıldı",
            description=f"{member.mention} sunucuya katıldı!",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Hesap Oluşturulma", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Üye Sayısı", value=member.guild.member_count, inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id = await self.get_log_channel(member.guild.id, 'member_log')
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        roles = [role.mention for role in member.roles[1:]][:10]
        
        embed = discord.Embed(
            title="📤 Üye Ayrıldı",
            description=f"{member.mention} sunucudan ayrıldı.",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="👥 Üye Sayısı", value=member.guild.member_count, inline=True)
        if roles:
            embed.add_field(name="🎭 Rolleri", value=" ".join(roles), inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
        
        channel_id = await self.get_log_channel(before.guild.id, 'role_log')
        if not channel_id:
            return
        
        log_channel = before.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]
        
        if added_roles:
            embed = discord.Embed(
                title="➕ Rol Verildi",
                description=f"{after.mention} kullanıcısına rol verildi",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎭 Roller", value=" ".join([r.mention for r in added_roles]))
        elif removed_roles:
            embed = discord.Embed(
                title="➖ Rol Alındı",
                description=f"{after.mention} kullanıcısından rol alındı",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎭 Roller", value=" ".join([r.mention for r in removed_roles]))
        else:
            return
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass

async def setup(bot):
    await bot.add_cog(Logs(bot))
