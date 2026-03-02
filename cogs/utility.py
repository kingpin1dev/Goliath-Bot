import discord
from discord import app_commands
from discord.ext import commands
import wikipedia
import pyshorteners
import re
import aiohttp

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shortener = pyshorteners.Shortener()
    
    @app_commands.command(name="translate", description="Metni çevirir")
    @app_commands.describe(
        dil="Hedef dil (tr, en, es, fr, de, it, ja vb.)",
        metin="Çevrilecek metin"
    )
    async def translate(self, interaction: discord.Interaction, dil: str, metin: str):
        await interaction.response.defer()
        
        try:
            # MyMemory Translation API (ücretsiz, limit: 1000 karakter/gün)
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': metin,
                'langpair': f'auto|{dil}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        translated_text = data['responseData']['translatedText']
                        
                        embed = discord.Embed(
                            title="🌐 Çeviri",
                            color=0x5865F2
                        )
                        embed.add_field(name="📝 Orijinal", value=metin[:1024], inline=False)
                        embed.add_field(name=f"📝 Çeviri ({dil})", value=translated_text[:1024], inline=False)
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ Çeviri API'sine erişilemedi!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Çeviri hatası: {str(e)[:100]}", ephemeral=True)
    
    @app_commands.command(name="weather", description="Hava durumu bilgisi (yakında)")
    @app_commands.describe(sehir="Şehir adı")
    async def weather(self, interaction: discord.Interaction, sehir: str):
        await interaction.response.send_message(
            "🌤️ Hava durumu özelliği yakında eklenecek!\n"
            "**Not:** OpenWeatherMap API key gereklidir.",
            ephemeral=True
        )
    
    @app_commands.command(name="wiki", description="Wikipedia'da arama yapar")
    @app_commands.describe(konu="Aranacak konu")
    async def wiki(self, interaction: discord.Interaction, konu: str):
        try:
            wikipedia.set_lang("tr")
            
            try:
                page = wikipedia.page(konu, auto_suggest=True)
            except:
                # Türkçe bulamazsa İngilizce dene
                wikipedia.set_lang("en")
                page = wikipedia.page(konu, auto_suggest=True)
            
            summary = wikipedia.summary(page.title, sentences=3)
            
            embed = discord.Embed(
                title=f"📚 {page.title}",
                description=summary,
                url=page.url,
                color=0x5865F2
            )
            embed.set_footer(text="Wikipedia")
            
            await interaction.response.send_message(embed=embed)
        except wikipedia.exceptions.DisambiguationError as e:
            await interaction.response.send_message(
                f"❌ Çok fazla sonuç bulundu! Daha spesifik olun:\n{', '.join(e.options[:5])}",
                ephemeral=True
            )
        except wikipedia.exceptions.PageError:
            await interaction.response.send_message(
                f"❌ '{konu}' hakkında bir sayfa bulunamadı!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
    
    @app_commands.command(name="calc", description="Matematiksel işlem yapar")
    @app_commands.describe(islem="Matematiksel işlem (örn: 2+2, 5*3, 10/2)")
    async def calc(self, interaction: discord.Interaction, islem: str):
        try:
            # Güvenlik için sadece sayılar ve operatörlere izin ver
            if not re.match(r'^[\d+\-*/().% ]+$', islem):
                return await interaction.response.send_message(
                    "❌ Sadece sayılar ve temel operatörler (+, -, *, /, %, parantez) kullanabilirsiniz!",
                    ephemeral=True
                )
            
            result = eval(islem)
            
            embed = discord.Embed(
                title="🧮 Hesap Makinesi",
                color=0x5865F2
            )
            embed.add_field(name="📝 İşlem", value=f"`{islem}`", inline=False)
            embed.add_field(name="✅ Sonuç", value=f"`{result}`", inline=False)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Geçersiz işlem! Hata: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="shortenurl", description="URL'yi kısaltır")
    @app_commands.describe(link="Kısaltılacak URL")
    async def shortenurl(self, interaction: discord.Interaction, link: str):
        try:
            # URL geçerli mi kontrol et
            if not link.startswith(('http://', 'https://')):
                link = 'https://' + link
            
            short_url = self.shortener.tinyurl.short(link)
            
            embed = discord.Embed(
                title="🔗 URL Kısaltıcı",
                color=0x5865F2
            )
            embed.add_field(name="📝 Orijinal", value=link[:1024], inline=False)
            embed.add_field(name="✂️ Kısaltılmış", value=short_url, inline=False)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ URL kısaltma hatası: {e}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Utility(bot))
