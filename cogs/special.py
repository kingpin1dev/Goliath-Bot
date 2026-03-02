import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

class Special(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="afk", description="AFK moduna geçer")
    @app_commands.describe(sebep="AFK sebebi")
    async def afk(self, interaction: discord.Interaction, sebep: str = "AFK"):
        timestamp = int(datetime.now().timestamp())
        
        await self.bot.db.execute(
            'INSERT OR REPLACE INTO afk (user_id, reason, timestamp) VALUES (?, ?, ?)',
            (interaction.user.id, sebep, timestamp)
        )
        await self.bot.db.commit()
        
        embed = discord.Embed(
            title="💤 AFK Modu",
            description=f"{interaction.user.mention} artık AFK!\n**Sebep:** {sebep}",
            color=0xFFA500,
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="reminder", description="Hatırlatıcı ayarlar")
    @app_commands.describe(
        sure="Süre (örn: 5m, 1h, 2d)",
        mesaj="Hatırlatıcı mesajı"
    )
    async def reminder(self, interaction: discord.Interaction, sure: str, mesaj: str):
        # Süre hesaplama
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = sure[-1]
            amount = int(sure[:-1])
            seconds = amount * time_dict[unit]
            
            if seconds < 60:
                return await interaction.response.send_message(
                    "❌ Hatırlatıcı süresi en az 1 dakika olmalı!",
                    ephemeral=True
                )
            
            if seconds > 2592000:  # 30 gün
                return await interaction.response.send_message(
                    "❌ Hatırlatıcı süresi en fazla 30 gün olabilir!",
                    ephemeral=True
                )
            
            end_time = int((datetime.now() + timedelta(seconds=seconds)).timestamp())
            
            await self.bot.db.execute(
                'INSERT INTO reminders (user_id, channel_id, message, end_time) VALUES (?, ?, ?, ?)',
                (interaction.user.id, interaction.channel.id, mesaj, end_time)
            )
            await self.bot.db.commit()
            
            # Süre gösterimi
            sure_text = f"{amount} {'saniye' if unit == 's' else 'dakika' if unit == 'm' else 'saat' if unit == 'h' else 'gün'}"
            
            embed = discord.Embed(
                title="⏰ Hatırlatıcı Ayarlandı",
                color=0xFFD700
            )
            embed.add_field(name="⏱️ Süre", value=sure_text, inline=True)
            embed.add_field(name="📝 Mesaj", value=mesaj, inline=False)
            embed.add_field(name="🕒 Hatırlanacak Zaman", value=f"<t:{end_time}:R>", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except (KeyError, ValueError):
            await interaction.response.send_message(
                "❌ Geçersiz süre formatı! Örnek: 5m, 1h, 2d",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Special(bot))
