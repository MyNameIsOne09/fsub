```markdown
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

```

### Apa yang diubah?
1. **Ikon Emoji:** Menambahkan emoji pada judul (heading) agar tampilan lebih menarik.
2. **Garis Pemisah (`---`):** Memberikan jarak visual antar bagian utama.
3. **Blockquote (`>`):** Mengubah teks catatan (Database dan Pengembangan) menjadi *blockquote* agar menonjol dan mudah dibaca.
4. **Formatting Kode:** Memastikan perintah terminal dan struktur folder berada di dalam *code block* yang rapi.
5. **Penomoran:** Menambahkan komentar `# 1`, `# 2` pada langkah instalasi agar lebih jelas.
