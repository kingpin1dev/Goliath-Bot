import discord
from discord.ext import commands
import aiosqlite
import asyncio
import os
from datetime import datetime

# Token - .env dosyasından okunur
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents
intents = discord.Intents.all()

# Bot oluştur
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None
)

# Veritabanı bağlantısı
async def init_db():
    """Veritabanını başlat"""
    bot.db = await aiosqlite.connect('database.db')
    
    # Leveling tablosu
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS levels (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    ''')
    
    # Warnings tablosu
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            timestamp INTEGER
        )
    ''')
    
    # AFK tablosu
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS afk (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            timestamp INTEGER
        )
    ''')
    
    # Reminders tablosu
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_id INTEGER,
            message TEXT,
            end_time INTEGER
        )
    ''')
    
    # Log ayarları
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS log_settings (
            guild_id INTEGER PRIMARY KEY,
            message_log INTEGER,
            member_log INTEGER,
            role_log INTEGER,
            channel_log INTEGER,
            moderation_log INTEGER,
            voice_log INTEGER
        )
    ''')
    
    # Member stats
    await bot.db.execute('''
        CREATE TABLE IF NOT EXISTS member_stats (
            user_id INTEGER,
            guild_id INTEGER,
            messages_sent INTEGER DEFAULT 0,
            voice_time INTEGER DEFAULT 0,
            joins INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    ''')
    
    await bot.db.commit()
    print("✅ Veritabanı başlatıldı!")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} olarak giriş yapıldı!')
    print(f'📊 Bot {len(bot.guilds)} sunucuda aktif')
    
    # Veritabanını başlat
    await init_db()
    
    # Cog'ları yükle
    await load_cogs()
    
    # Slash komutları senkronize et
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"❌ Slash komutları senkronize edilemedi: {e}")
    
    # Rich Presence
    activity = discord.Streaming(
        name="👑 #1473 Supremacy 👑",
        url="https://www.twitch.tv/kingpindev"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    print("✅ Etkinlik ayarlandı: Streaming 👑 #1473 Supremacy")
    
    # Reminder checker başlat
    bot.loop.create_task(check_reminders())

async def load_cogs():
    """Cog'ları yükle"""
    cogs = [
        'cogs.basic',
        'cogs.moderation',
        'cogs.servermanagement',
        'cogs.leveling',
        'cogs.music',  # Artık çalışır!
        'cogs.logs',
        'cogs.utility',
        'cogs.special',
        'cogs.stats'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog} yüklendi!")
        except Exception as e:
            print(f"❌ {cog} yüklenemedi: {e}")

async def check_reminders():
    """Hatırlatıcıları kontrol et"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            current_time = int(datetime.now().timestamp())
            async with bot.db.execute(
                'SELECT * FROM reminders WHERE end_time <= ?',
                (current_time,)
            ) as cursor:
                reminders = await cursor.fetchall()
            
            for reminder in reminders:
                reminder_id, user_id, channel_id, message, end_time = reminder
                
                try:
                    channel = bot.get_channel(channel_id)
                    user = bot.get_user(user_id)
                    
                    if channel and user:
                        embed = discord.Embed(
                            title="⏰ Hatırlatıcı!",
                            description=message,
                            color=0xFFD700,
                            timestamp=datetime.now()
                        )
                        embed.set_footer(text=f"Hatırlatıcı ID: {reminder_id}")
                        
                        await channel.send(user.mention, embed=embed)
                    
                    # Hatırlatıcıyı sil
                    await bot.db.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
                    await bot.db.commit()
                    
                except Exception as e:
                    print(f"Hatırlatıcı gönderilirken hata: {e}")
        
        except Exception as e:
            print(f"Hatırlatıcı kontrolünde hata: {e}")
        
        await asyncio.sleep(10)  # Her 10 saniyede bir kontrol et

# Mesaj dinleyicisi (Leveling için)
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # AFK kontrolü
    async with bot.db.execute('SELECT reason FROM afk WHERE user_id = ?', (message.author.id,)) as cursor:
        afk_data = await cursor.fetchone()
    
    if afk_data:
        await bot.db.execute('DELETE FROM afk WHERE user_id = ?', (message.author.id,))
        await bot.db.commit()
        await message.channel.send(f"👋 {message.author.mention} artık AFK değil!", delete_after=5)
    
    # Mention edilen kişi AFK mı kontrol et
    for mention in message.mentions:
        async with bot.db.execute('SELECT reason, timestamp FROM afk WHERE user_id = ?', (mention.id,)) as cursor:
            mentioned_afk = await cursor.fetchone()
        
        if mentioned_afk:
            reason, timestamp = mentioned_afk
            afk_time = datetime.fromtimestamp(timestamp)
            time_diff = datetime.now() - afk_time
            
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            time_str = f"{hours} saat {minutes} dakika" if hours > 0 else f"{minutes} dakika"
            
            embed = discord.Embed(
                description=f"💤 {mention.mention} AFK: **{reason}**\nSüre: {time_str}",
                color=0xFFA500
            )
            await message.channel.send(embed=embed, delete_after=10)
    
    # Member stats güncelle
    await bot.db.execute('''
        INSERT INTO member_stats (user_id, guild_id, messages_sent)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, guild_id) DO UPDATE SET
        messages_sent = messages_sent + 1
    ''', (message.author.id, message.guild.id))
    await bot.db.commit()
    
    await bot.process_commands(message)

# Bot kapatılırken
@bot.event
async def on_close():
    await bot.db.close()
    print("❌ Bot kapatıldı ve veritabanı bağlantısı kesildi!")

if __name__ == "__main__":
    bot.run(TOKEN)
