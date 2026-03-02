import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Role add komutu
    role_group = app_commands.Group(name="role", description="Rol yönetimi komutları")
    
    @role_group.command(name="add", description="Kullanıcıya rol verir")
    @app_commands.describe(
        kullanici="Rol verilecek kullanıcı",
        rol="Verilecek rol"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_add(self, interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if rol >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ Bu rolü veremem, rol hiyerarşim yeterli değil!", ephemeral=True)
        
        if rol >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Bu rolü veremezsiniz, rol hiyerarşiniz yeterli değil!", ephemeral=True)
        
        if rol in kullanici.roles:
            return await interaction.response.send_message(f"❌ {kullanici.mention} zaten {rol.mention} rolüne sahip!", ephemeral=True)
        
        try:
            await kullanici.add_roles(rol, reason=f"{interaction.user} tarafından verildi")
            
            embed = discord.Embed(
                title="✅ Rol Verildi",
                description=f"{kullanici.mention} kullanıcısına {rol.mention} rolü verildi.",
                color=rol.color,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Yetkili: {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Role remove komutu
    @role_group.command(name="remove", description="Kullanıcıdan rol alır")
    @app_commands.describe(
        kullanici="Rolü alınacak kullanıcı",
        rol="Alınacak rol"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if rol >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ Bu rolü alamam, rol hiyerarşim yeterli değil!", ephemeral=True)
        
        if rol >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Bu rolü alamazsınız, rol hiyerarşiniz yeterli değil!", ephemeral=True)
        
        if rol not in kullanici.roles:
            return await interaction.response.send_message(f"❌ {kullanici.mention} zaten {rol.mention} rolüne sahip değil!", ephemeral=True)
        
        try:
            await kullanici.remove_roles(rol, reason=f"{interaction.user} tarafından alındı")
            
            embed = discord.Embed(
                title="✅ Rol Alındı",
                description=f"{kullanici.mention} kullanıcısından {rol.mention} rolü alındı.",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Yetkili: {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    # Roleinfo komutu
    @role_group.command(name="info", description="Rol hakkında bilgi gösterir")
    @app_commands.describe(rol="Bilgisi görüntülenecek rol")
    async def roleinfo(self, interaction: discord.Interaction, rol: discord.Role):
        embed = discord.Embed(
            title=f"🎭 {rol.name}",
            color=rol.color
        )
        
        embed.add_field(name="🆔 ID", value=f"`{rol.id}`", inline=True)
        embed.add_field(name="🎨 Renk", value=str(rol.color), inline=True)
        embed.add_field(name="📊 Pozisyon", value=str(rol.position), inline=True)
        
        embed.add_field(name="👥 Üye Sayısı", value=str(len(rol.members)), inline=True)
        embed.add_field(name="🏷️ Mention", value=rol.mention if rol.mentionable else "Bahsedilemez", inline=True)
        embed.add_field(name="🔧 Yönetilen", value="Evet" if rol.managed else "Hayır", inline=True)
        
        embed.add_field(name="📅 Oluşturulma", value=f"<t:{int(rol.created_at.timestamp())}:R>", inline=False)
        
        # İzinler
        perms = []
        if rol.permissions.administrator:
            perms.append("👑 Administrator")
        if rol.permissions.manage_guild:
            perms.append("⚙️ Sunucu Yönetimi")
        if rol.permissions.manage_roles:
            perms.append("🎭 Rol Yönetimi")
        if rol.permissions.manage_channels:
            perms.append("📢 Kanal Yönetimi")
        if rol.permissions.kick_members:
            perms.append("🚪 Üye Atma")
        if rol.permissions.ban_members:
            perms.append("🔨 Üye Yasaklama")
        
        if perms:
            embed.add_field(name="🔑 Önemli İzinler", value="\n".join(perms), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    # Member count komutu
    @app_commands.command(name="membercount", description="Sunucunun üye sayısını gösterir")
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        embed = discord.Embed(
            title=f"📊 {guild.name} - Üye Sayısı",
            color=0x5865F2
        )
        
        embed.add_field(name="👥 Toplam Üye", value=f"```{total:,}```", inline=True)
        embed.add_field(name="👤 İnsan", value=f"```{humans:,}```", inline=True)
        embed.add_field(name="🤖 Bot", value=f"```{bots:,}```", inline=True)
        embed.add_field(name="🟢 Çevrimiçi", value=f"```{online:,}```", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.response.send_message(embed=embed)
    
    # Server icon komutu
    @app_commands.command(name="servericon", description="Sunucunun ikonunu gösterir")
    async def servericon(self, interaction: discord.Interaction):
        if not interaction.guild.icon:
            return await interaction.response.send_message("❌ Bu sunucunun ikonu yok!", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🖼️ {interaction.guild.name} - Sunucu İkonu",
            color=0x5865F2
        )
        embed.set_image(url=interaction.guild.icon.url)
        
        # İndirme linkleri
        formats = []
        if interaction.guild.icon.is_animated():
            formats.append(f"[GIF]({interaction.guild.icon.replace(format='gif', size=1024).url})")
        formats.append(f"[PNG]({interaction.guild.icon.replace(format='png', size=1024).url})")
        formats.append(f"[WEBP]({interaction.guild.icon.replace(format='webp', size=1024).url})")
        
        embed.add_field(name="📥 İndir", value=" | ".join(formats))
        
        await interaction.response.send_message(embed=embed)
    
    # Server banner komutu
    @app_commands.command(name="serverbanner", description="Sunucunun banner'ını gösterir")
    async def serverbanner(self, interaction: discord.Interaction):
        if not interaction.guild.banner:
            return await interaction.response.send_message("❌ Bu sunucunun banner'ı yok!", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🎨 {interaction.guild.name} - Sunucu Banner",
            color=0x5865F2
        )
        embed.set_image(url=interaction.guild.banner.url)
        
        formats = [
            f"[PNG]({interaction.guild.banner.replace(format='png', size=1024).url})",
            f"[WEBP]({interaction.guild.banner.replace(format='webp', size=1024).url})"
        ]
        
        embed.add_field(name="📥 İndir", value=" | ".join(formats))
        
        await interaction.response.send_message(embed=embed)
    
    # Emojis komutu
    @app_commands.command(name="emojis", description="Sunucudaki tüm emojileri gösterir")
    async def emojis(self, interaction: discord.Interaction):
        # Önce yanıt verelim - zaman aşımını önler
        await interaction.response.defer()
        
        emojis = interaction.guild.emojis
        
        if not emojis:
            return await interaction.followup.send("❌ Bu sunucuda emoji yok!")
        
        # Normal ve animasyonlu emojileri ayır
        normal = [e for e in emojis if not e.animated]
        animated = [e for e in emojis if e.animated]
        
        embed = discord.Embed(
            title=f"😄 {interaction.guild.name} - Emojiler ({len(emojis)})",
            color=0x5865F2
        )
        
        if normal:
            # İlk 50 emoji
            emoji_text = " ".join([str(e) for e in normal[:50]])
            if len(normal) > 50:
                emoji_text += f"\n... ve {len(normal) - 50} emoji daha"
            embed.add_field(name=f"📝 Normal Emojiler ({len(normal)})", value=emoji_text or "Yok", inline=False)
        
        if animated:
            # İlk 50 animasyonlu emoji
            emoji_text = " ".join([str(e) for e in animated[:50]])
            if len(animated) > 50:
                emoji_text += f"\n... ve {len(animated) - 50} emoji daha"
            embed.add_field(name=f"🎬 Animasyonlu Emojiler ({len(animated)})", value=emoji_text or "Yok", inline=False)
        
        max_emojis = interaction.guild.emoji_limit
        embed.set_footer(text=f"Emoji Limiti: {len(emojis)}/{max_emojis}")
        
        await interaction.followup.send(embed=embed)
    
    # Botinfo komutu
    @app_commands.command(name="botinfo", description="Bot hakkında bilgi gösterir")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name}",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="📊 Sunucu Sayısı", value=f"```{len(self.bot.guilds):,}```", inline=True)
        embed.add_field(name="👥 Toplam Üye", value=f"```{len(self.bot.users):,}```", inline=True)
        embed.add_field(name="⚡ Gecikme", value=f"```{round(self.bot.latency * 1000)}ms```", inline=True)
        
        embed.add_field(name="🆔 Bot ID", value=f"`{self.bot.user.id}`", inline=False)
        embed.add_field(name="📅 Oluşturulma", value=f"<t:{int(self.bot.user.created_at.timestamp())}:R>", inline=False)
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="👑 #1473 Supremacy")
        
        await interaction.response.send_message(embed=embed)
    
    # Invites komutu
    @app_commands.command(name="invites", description="Kullanıcının davet sayısını gösterir")
    @app_commands.describe(kullanici="Davet sayısı görüntülenecek kullanıcı")
    async def invites(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        
        await interaction.response.defer()
        
        try:
            invites = await interaction.guild.invites()
            user_invites = [inv for inv in invites if inv.inviter and inv.inviter.id == kullanici.id]
            
            total_uses = sum(inv.uses for inv in user_invites)
            
            embed = discord.Embed(
                title=f"📨 {kullanici} - Davetler",
                color=0x5865F2
            )
            
            embed.add_field(name="📊 Toplam Davet", value=f"```{total_uses}```", inline=True)
            embed.add_field(name="🔗 Davet Linki Sayısı", value=f"```{len(user_invites)}```", inline=True)
            
            if user_invites:
                invite_list = "\n".join([
                    f"`{inv.code}` - {inv.uses} kullanım"
                    for inv in sorted(user_invites, key=lambda x: x.uses, reverse=True)[:10]
                ])
                embed.add_field(name="🔝 En Çok Kullanılan Davetler", value=invite_list, inline=False)
            
            embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else None)
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Davet bilgilerini görüntüleme yetkim yok!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
