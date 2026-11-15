# 🤖 dzbot

Bot Telegram untuk mengelola unggahan media dengan sistem persetujuan admin sebelum diposting ke channel. Dilengkapi dengan fitur **FSUB** (Force Subscribe).

---

## 🚀 Menjalankan (Server / Termux)

Ikuti langkah berikut untuk menjalankan bot:

```bash
# 1. Install dependensi
pip install -r requirements.txt

# 2. Salin file konfigurasi dan isi BOT_TOKEN
cp .env.example .env

# 3. Jalankan bot
python main.py
```

Catatan Database: 
Database database.db akan dibuat otomatis di folder ini. Jika kamu memiliki data lama, ganti nama file dzbotloini.db menjadi database.db.

---

📝 Logging

Sistem log dirancang untuk memudahkan debugging:

· Konsol (Server/Termux): Menampilkan semua log. Error ditandai dengan >>> ERROR <<< dan berwarna merah.
· logs/bot.log: Mencatat semua aktivitas log.
· logs/error.log: Hanya mencatat error beserta traceback lengkap.

Error dari handler Telegram ditangkap oleh core/errors.py, sedangkan error yang lolos (termasuk di dalam thread) akan ditangkap oleh hook di core/logger.py.

---

📁 Struktur Proyek

```text
main.py                  Daftar command/handler + start polling
config.py                Token (.env), channel, admin, path database/log

core/
  database.py            Koneksi, skema, migrasi (init_db)
  logger.py              Pengaturan log konsol + file
  errors.py              Error handler Telegram
  helpers.py             is_admin, download_file
  compat.py              Patch imghdr untuk Python 3.13+

features/
  menu/                  /start, panel admin, bantuan, /stats
  upload/                Kirim foto/video/gif, pilih hashtag
  approval/              ACC/TOLAK/caption, grup approval, /pending, /hapus, /listpost
  delivery/              Posting ke channel + kirim konten lewat link share
  fsub/                  Channel wajib join, invite link, teks subscription
  hashtag/               Daftar hashtag + gambar per hashtag
  buttons/               Tombol custom di postingan channel
  whitelist/             Whitelist upload
  thumbnail/             Thumbnail default channel
  broadcast/             /bc /bcfoto /bcvideo
```

Catatan Pengembangan: 
Setiap fitur di dalam folder features/ umumnya terdiri dari dua file: queries.py (untuk akses database) dan handlers.py (untuk command/callback).

---

📬 Kontak Developer

Platform Kontak Tautan
<img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="20" height="20" /> Telegram @zentokki t.me/zentokki
<img src="https://upload.wikimedia.org/wikipedia/commons/e/e7/Instagram_logo_2016.svg" width="20" height="20" /> Instagram @NicoMarchel instagram.com/NicoMarchel

---

<p align="center">
  Made with ❤️ by <a href="https://t.me/zentokki">Nico Marchel</a>
</p>
```
