import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Basic(commands.Cog):
    """Temel komutlar (ping, stats, userinfo, avatar)"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Botun gecikmesini gösterir")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Pong! 🏓 Gecikme: {round(self.bot.latency * 1000)}ms')
    
    @app_commands.command(name="stats", description="Sunucu bilgilerini gösterir")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0
        
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        role_count = len(guild.roles)
        
        embed = discord.Embed(
            title=f"{guild.name} Sunucu Bilgileri",
            color=0x5865F2
        )
        
        embed.add_field(name="👑 Sahip", value=guild.owner.mention if guild.owner else "Bilinmiyor", inline=True)
        
        features_text = ""
        if "COMMUNITY" in guild.features:
            features_text += "✅ Topluluk\n"
        if "VERIFIED" in guild.features:
            features_text += "✅ Doğrulanmış\n"
        if "PARTNERED" in guild.features:
            features_text += "✅ Partner\n"
        
        embed.add_field(name="✨ Özellikler", value=features_text if features_text else "Yok", inline=True)
        
        boost_text = f"Seviye {boost_level}\n{boost_count} boost"
        embed.add_field(name="🚀 Boost", value=boost_text, inline=True)
        
        channel_text = f"📝 {text_channels} metin\n🔊 {voice_channels} ses"
        embed.add_field(name="📢 Kanallar", value=channel_text, inline=True)
        
        member_text = f"Toplam: {total_members}\nİnsan: {humans}\nBot: {bots}"
        embed.add_field(name="👥 Üyeler", value=member_text, inline=True)
        
        embed.add_field(name="🎭 Roller", value=f"{role_count} rol", inline=True)
        
        created_timestamp = int(guild.created_at.timestamp())
        embed.add_field(
            name="ℹ️ Bilgi",
            value=f"**ID:** {guild.id}\n**Oluşturulma:** <t:{created_timestamp}:R>",
            inline=False
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="userinfo", description="Kullanıcı bilgilerini gösterir")
    @app_commands.describe(kullanici="Bilgisi görüntülenecek kullanıcı")
    async def userinfo(self, interaction: discord.Interaction, kullanici: discord.User = None):
        user = kullanici or interaction.user
        member = interaction.guild.get_member(user.id) if interaction.guild else None
        
        embed = discord.Embed(
            title=f"👤 {user.name}",
            color=0x00FFFF
        )
        
        embed.add_field(name="🆔 Kullanıcı ID", value=f"`{user.id}`", inline=False)
        
        created_timestamp = int(user.created_at.timestamp())
        embed.add_field(
            name="📅 Hesap Oluşturulma Tarihi",
            value=f"<t:{created_timestamp}:F>\n(<t:{created_timestamp}:R>)",
            inline=False
        )
        
        if member and member.joined_at:
            joined_timestamp = int(member.joined_at.timestamp())
            embed.add_field(
                name="📥 Sunucuya Katılma Tarihi",
                value=f"<t:{joined_timestamp}:F>\n(<t:{joined_timestamp}:R>)",
                inline=False
            )
        
        if member and member.premium_since:
            boost_timestamp = int(member.premium_since.timestamp())
            embed.add_field(
                name="🚀 Sunucu Boost", 
                value=f"Evet (<t:{boost_timestamp}:R> beri)",
                inline=False
            )
        
        if member and len(member.roles) > 1:
            roles = [role.mention for role in sorted(member.roles[1:], reverse=True)][:10]
            roles_text = ", ".join(roles)
            embed.add_field(
                name=f"🎭 Roller ({len(member.roles)-1})", 
                value=roles_text,
                inline=False
            )
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        embed.set_footer(text=f"Kullanıcı Adı: {user}")
        
        await interaction.response.send_message(embed=embed)
    
    avatar_group = app_commands.Group(name="avatar", description="Avatar komutları")
    
    @avatar_group.command(name="get", description="Kullanıcının avatarını gösterir")
    @app_commands.describe(kullanici="Avatarı görüntülenecek kullanıcı")
    async def avatar_get(self, interaction: discord.Interaction, kullanici: discord.User = None):
        user = kullanici or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {user.name} - Avatar",
            color=0x5865F2
        )
        
        avatar_url = None
        avatar_type = "Global Avatar"
        
        if interaction.guild:
            member = interaction.guild.get_member(user.id)
            if member and member.guild_avatar:
                avatar_url = member.guild_avatar.url
                avatar_type = "Sunucu Avatarı"
        
        if not avatar_url:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"{user} • {avatar_type}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Basic(bot))
