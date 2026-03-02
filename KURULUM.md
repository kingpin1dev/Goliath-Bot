# 🚀 Goliath Bot - Kurulum Kılavuzu

## ✅ 1. ADIM: FFmpeg Kur (Müzik İçin Gerekli!)

**FFmpeg müzik sistemi için zorunludur!**

### Windows için:

1. **FFmpeg'i İndir:**
   - https://www.gyan.dev/ffmpeg/builds/
   - "ffmpeg-release-essentials.zip" indir

2. **Çıkart:**
   - ZIP'i çıkart (örn: `C:\ffmpeg`)

3. **PATH'e Ekle:**
   - Windows tuşu → "environment variables" ara
   - "Sistem ortam değişkenlerini düzenle" aç
   - "Ortam Değişkenleri" butonu
   - "Path" seç → "Düzenle"
   - "Yeni" → `C:\ffmpeg\bin` ekle
   - Tümünü kaydet

4. **Test Et:**
   ```cmd
   ffmpeg -version
   ```
   Versiyon gösterirse başarılı! ✅

### Alternatif (Kolay):
**Chocolatey varsa:**
```cmd
choco install ffmpeg
```

---

## ✅ 2. ADIM: Gerekli Paketleri Kur

**Komut İstemi'ni (CMD) Yönetici olarak açın:**
- Windows tuşu → "cmd" yaz → Sağ tık → "Yönetici olarak çalıştır"

**Bot klasörüne gidin:**
```cmd
cd "C:\Program Files (x86)\Goliath Bot by Kingpindev"
```

**Gerekli paketleri kurun:**
```cmd
python -m pip install -r requirements.txt
```

**Eğer hata alırsanız:**
```cmd
python -m pip install discord.py aiohttp aiosqlite googletrans==4.0.0rc1 wikipedia pyshorteners --break-system-packages
```

---

## ✅ 2. ADIM: Discord Bot Token Al

1. **Discord Developer Portal'a git:**
   https://discord.com/developers/applications

2. **Yeni Uygulama Oluştur:**
   - "New Application" butonuna tıkla
   - İsim ver (örn: Goliath Bot)
   - "Create" tıkla

3. **Bot Oluştur:**
   - Sol menüden "Bot" sekmesine tıkla
   - "Reset Token" butonu → Token'ı kopyala
   - **ÖNEMLİ:** Bu token'ı kimseyle paylaşma!

4. **Intents'leri Aç (ÇOK ÖNEMLİ!):**
   Aşağı kaydır → "Privileged Gateway Intents" bölümü:
   - ✅ **PRESENCE INTENT** - Aç
   - ✅ **SERVER MEMBERS INTENT** - Aç
   - ✅ **MESSAGE CONTENT INTENT** - Aç
   - "Save Changes" tıkla

5. **Botu Davet Et:**
   - Sol menü → "OAuth2" → "URL Generator"
   - Scopes:
     - ✅ `bot`
     - ✅ `applications.commands`
   - Bot Permissions:
     - ✅ `Administrator` (en kolayı)
   - Oluşan URL'yi kopyala
   - Tarayıcıda aç
   - Sunucunu seç → "Authorize"

---

## ✅ 3. ADIM: Token'ı .env Dosyasına Ekle

1. **Bot klasöründe `.env` dosyası oluştur** (Notepad++ veya herhangi bir metin editörü)

2. **Aşağıdaki satırı yaz:**
   ```
   DISCORD_TOKEN=BURAYA_TOKENINI_YAPISTIR
   ```

3. **Token'ını yapıştır ve dosyayı kaydet** (Ctrl + S)

---

## ✅ 4. ADIM: Botu Çalıştır

### Yöntem 1: Normal Çalıştırma (Test için)

**CMD'de:**
```cmd
cd "C:\Program Files (x86)\Goliath Bot by Kingpindev"
python bot.py
```

**Başarılı olursa şöyle yazmalı:**
```
✅ Goliath#3964 olarak giriş yapıldı!
📊 Bot 1 sunucuda aktif
✅ Veritabanı başlatıldı!
✅ basic yüklendi!
✅ moderation yüklendi!
... (diğer cog'lar)
✅ 50 slash komutu senkronize edildi!
✅ Etkinlik ayarlandı: Streaming 👑 #1473 Supremacy
```

### Yöntem 2: Gizli Çalıştırma (Arka Plan)

**start_bot.vbs dosyasına çift tıkla**

- Hiçbir pencere açılmaz
- Arka planda çalışır
- Task Manager'da `pythonw.exe` olarak görünür

---

## ✅ 5. ADIM: Startup'a Ekle (Otomatik Başlatma)

1. **Windows + R** → `shell:startup` → Enter

2. **start_bot.vbs** dosyasının kısayolunu oluştur:
   - `start_bot.vbs` dosyasına sağ tık
   - "Kısayol oluştur" veya "Create shortcut"
   - Oluşan kısayolu Startup klasörüne sürükle

3. **Bilgisayarı yeniden başlat**
   - Bot otomatik çalışmalı!

---

## ✅ 6. ADIM: Discord'da Test Et

Discord'da şu komutları dene:

```
/ping              → Gecikme testi
/stats             → Sunucu bilgisi
/userinfo          → Profilin
/avatar get        → Avatarın
/rank              → Seviyen
/help              → Tüm komutlar (yakında)
```

---

## 🐛 Sorun Giderme

### ❌ "pip is not recognized"
**Çözüm:**
```cmd
python -m pip install -r requirements.txt
```

### ❌ Bot çevrimiçi olmuyor
**Kontrol Et:**
1. Token doğru mu?
2. Tüm Intents açık mı? (3 tane)
3. Bot sunucuya davet edildi mi?

### ❌ "discord.py not found"
**Çözüm:**
```cmd
python -m pip install discord.py --upgrade
```

### ❌ Slash komutlar görünmüyor
**Bekle:** 1-5 dakika (Discord senkronizasyonu)
**Sonra:** Botu yeniden başlat

### ❌ "Intents error"
**Çözüm:** Developer Portal → Bot → Tüm Intents'leri aç

### ❌ Veritabanı hatası
**Çözüm:** `database.db` dosyasını sil, bot yeniden oluşturur

---

## 🛑 Botu Durdurma

### Normal mod:
- CMD penceresinde **Ctrl + C**

### Gizli mod:
- **Task Manager** (Ctrl + Shift + Esc)
- **Details** sekmesi
- `pythonw.exe` bul
- Sağ tık → **End Task**

---

## 📝 Önemli Notlar

- ✅ Token'ı kimseyle paylaşma!
- ✅ `database.db` dosyasını silme (tüm veriler kaybolur)
- ✅ Bot 7/24 çalışması için VPS gerekir (opsiyonel)
- ✅ Ücretsiz hosting: Railway.app, Render.com

---

## 🎯 Sonraki Adımlar

1. **Log Sistemini Aktifleştir:**
   ```
   /setlog tip:Mesaj_Logları kanal:#logs
   /setlog tip:Üye_Logları kanal:#logs
   ```

2. **Seviye Sistemini Test Et:**
   - Mesaj yaz → XP kazan
   - `/rank` ile kontrol et

3. **Moderasyon Komutlarını Dene:**
   ```
   /kick @kullanıcı sebep:Test
   /warn @kullanıcı sebep:Uyarı testi
   ```

---

**Başarılar! 🎉**

Sorun yaşarsan Discord'da **kingpindev** ile iletişime geç!

---

**Geliştirici:** kingpindev
**Discord:** kingpindev
