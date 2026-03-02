# 🤖 Goliath Discord Bot - Tam Özellikli Sürüm

## 📋 Özellikler

### 🛡️ Moderasyon Komutları
- `/kick` - Kullanıcı at
- `/ban` - Kullanıcı yasakla
- `/unban` - Yasağı kaldır
- `/timeout` - Geçici sustur
- `/untimeout` - Timeout kaldır
- `/clear` - Mesaj sil (1-100)
- `/slowmode` - Yavaş mod
- `/lock` - Kanalı kilitle
- `/unlock` - Kanalı aç
- `/nuke` - Kanalı yeniden oluştur
- `/warn` - Uyarı ver
- `/warnings` - Uyarıları göster
- `/clearwarnings` - Uyarıları temizle

### 📊 Sunucu Yönetimi
- `/role add` - Rol ver
- `/role remove` - Rol al
- `/role info` - Rol bilgisi
- `/membercount` - Üye sayısı
- `/servericon` - Sunucu ikonu
- `/serverbanner` - Sunucu banner
- `/emojis` - Tüm emojiler
- `/botinfo` - Bot bilgisi
- `/invites` - Davet sayısı

### 🎮 Leveling Sistemi
- `/rank` - Seviye/XP göster
- `/leaderboard` - Sıralama tablosu
- `/setlevel` - Seviye ayarla (Admin)
- Otomatik XP kazanma (mesaj başına)
- Seviye atlama bildirimleri

### 🎵 Müzik Sistemi (Tam Özellikli!)
- `/play` - YouTube'dan müzik çal veya **playlist ekle**
- `/pause` - Duraklat
- `/resume` - Devam et
- `/skip` - Şarkıyı atla
- `/seek` - **Şarkının belirli yerine atla**
- `/jump` - **Kuyruktaki belirli şarkıya atla**
- `/shuffle` - **Kuyruğu karıştır**
- `/remove` - **Kuyruktan şarkı kaldır**
- `/stay` - **Bot seste kalır (otomatik çıkmaz)** (Yeni!)
- `/disconnect` veya `/leave` - **Manuel çıkış** (Yeni!)
- `/musictimeout` - **İnaktivite süresini ayarla** (Yeni! - Admin)
- `/queue` - Kuyruğu göster
- `/nowplaying` - Şu an çalan
- `/volume` - Ses seviyesi (0-100)
- `/loop` - Tekrar modu
- `/stop` - Durdur ve kanaldan ayrıl
- **Özellikler:**
  - ✅ YouTube playlist desteği (max 50 şarkı)
  - ✅ Şarkı içinde ileri/geri sarma
  - ✅ Kuyruk karıştırma (shuffle)
  - ✅ Sıraya göre atlama
  - ✅ **Otomatik inaktivite çıkışı (varsayılan: 5 dakika)**
  - ✅ **Stay modu - seste kalma**
  - ✅ Akıllı hata yönetimi
  - **Gereksinim:** FFmpeg kurulu olmalı!

### 📝 Log Sistemi
- Mesaj silme/düzenleme logları
- Üye giriş/çıkış logları
- Rol değişikliği logları
- Kanal değişikliği logları
- Moderasyon logları
- Ses kanalı logları

### 🔔 Özel Sistemler
- `/afk` - AFK modu
- `/reminder` - Hatırlatıcı ayarla

### 📈 İstatistikler
- `/memberstats` - Detaylı üye istatistikleri

### 🔧 Yardımcı Araçlar
- `/translate` - Çeviri
- `/weather` - Hava durumu (yakında)
- `/wiki` - Wikipedia arama
- `/calc` - Hesap makinesi
- `/shortenurl` - Link kısaltma

### 💎 Temel Komutlar
- `/ping` - Gecikme testi
- `/stats` - Sunucu bilgileri
- `/userinfo` - Kullanıcı bilgileri
- `/avatar get` - Avatar göster

---

## 🚀 Kurulum

### 1. Gereksinimler

Python 3.10 veya üzeri gereklidir.

**Önce kurulum klasörüne gidin:**
```cmd
cd "C:\Program Files (x86)\Goliath Bot by Kingpindev"
```

**Sonra gerekli paketleri kurun:**
```cmd
pip install -r requirements.txt
```

veya 

```cmd
python -m pip install -r requirements.txt
```

### 2. Bot Token

1. https://discord.com/developers/applications adresine gidin
2. "New Application" → İsim verin
3. "Bot" sekmesi → "Reset Token" → Token'ı kopyalayın
4. **Privileged Gateway Intents** kısmından TÜM intents'leri açın:
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
5. Bot klasöründeki `.env` dosyasına `DISCORD_TOKEN=TOKEN_BURAYA` olarak yapıştırın

### 3. Botu Davet Etme

1. Developer Portal → "OAuth2" → "URL Generator"
2. Scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Bot Permissions:
   - ✅ `Administrator` (veya gerekli tüm yetkiler)
4. Oluşan URL'yi tarayıcıda açın
5. Sunucunuza ekleyin

### 4. Çalıştırma

#### Windows:
```cmd
python bot_full.py
```

#### Arka planda çalıştırma (Windows):
```cmd
pythonw bot_full.py
```

veya `start_bot.vbs` dosyasına çift tıklayın

#### Linux/Mac:
```bash
python3 bot_full.py
```

---

## 📁 Dosya Yapısı

```
Goliath Bot by Kingpindev/
├── bot.py               # Ana bot dosyası
├── requirements.txt     # Gerekli paketler
├── database.db          # SQLite veritabanı (otomatik oluşur)
├── start_bot.vbs        # Windows için gizli başlatma
├── README.md            # Bu dosya
└── cogs/
    ├── basic.py         # Temel komutlar
    ├── moderation.py    # Moderasyon
    ├── servermanagement.py  # Sunucu yönetimi
    ├── leveling.py      # Seviye sistemi
    ├── music.py         # Müzik (placeholder)
    ├── logs.py          # Log sistemi
    ├── utility.py       # Yardımcı araçlar
    ├── special.py       # AFK, Reminder
    └── stats.py         # İstatistikler
```

---

## ⚙️ Ayarlar

### Log Sistemini Aktifleştirme

```
/setlog tip:Mesaj_Logları kanal:#log-kanal
/setlog tip:Üye_Logları kanal:#log-kanal
/setlog tip:Rol_Logları kanal:#log-kanal
```

### Leveling Sistemi

- Mesaj göndererek otomatik XP kazanılır
- `/rank` ile seviyenizi kontrol edin
- `/leaderboard` ile sıralamayı görün

---

## 🐛 Sorun Giderme

### Bot çevrimiçi olmuyor
- Token'ı doğru kopyaladığınızdan emin olun
- Tüm Privileged Gateway Intents'lerin açık olduğunu kontrol edin

### Slash komutlar görünmüyor
- Bot'un `applications.commands` yetkisi olduğundan emin olun
- 1-5 dakika bekleyin (Discord senkronizasyonu zaman alabilir)
- Botu yeniden başlatın

### Müzik çalışmıyor
- Müzik sistemi için Lavalink sunucusu gereklidir
- Bu sürümde placeholder olarak eklenmiştir

### Veritabanı hataları
- `database.db` dosyasını silin ve botu yeniden başlatın
- Otomatik olarak yeniden oluşturulacaktır

---

## 📝 Notlar

- Bot 7/24 çalışması için VPS gereklidir
- Ücretsiz hosting: Replit, Railway.app, render.com
- Müzik için: Lavalink + Wavelink kurulumu gerekli
- Weather API için: OpenWeatherMap API key gerekli

---

## 🔒 Güvenlik

- Token'ınızı asla paylaşmayın!
- `.env` dosyası kullanarak token'ı saklayın (önerilir)
- GitHub'a yüklerken `.gitignore` ekleyin

---

## 📞 Destek

Sorunlarınız için Discord'da **kingpindev** ile iletişime geçin.

---

**Geliştirici:** kingpindev
**Discord:** kingpindev
**Versiyon:** 2.0
**Son Güncelleme:** 2026-02-14
