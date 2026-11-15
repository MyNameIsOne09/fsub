# dzbot

Bot Telegram: upload media -> approval admin -> posting ke channel, dengan FSUB.

## Menjalankan (server / Termux)

```
pip install -r requirements.txt
cp .env.example .env        # isi BOT_TOKEN
python main.py
```

Database: `database.db` (dibuat otomatis di folder ini). Jika punya data lama, ganti nama `dzbotloini.db` menjadi `database.db`.

## Log

- Konsol (server/Termux): semua log, error ditandai `>>> ERROR <<<` dan berwarna merah
- `logs/bot.log`: semua log
- `logs/error.log`: hanya error + traceback lengkap

Error dari handler Telegram ditangkap `core/errors.py`; error yang lolos (termasuk di thread) ditangkap hook di `core/logger.py`.

## Struktur

```
main.py                  daftar command/handler + start polling
config.py                token (.env), channel, admin, path database/log
core/
  database.py            koneksi, skema, migrasi (init_db)
  logger.py              pengaturan log konsol + file
  errors.py              error handler Telegram
  helpers.py             is_admin, download_file
  compat.py              patch imghdr untuk Python 3.13+
features/
  menu/                  /start, panel admin, bantuan, /stats
  upload/                kirim foto/video/gif, pilih hashtag
  approval/              ACC/TOLAK/caption, grup approval, /pending, /hapus, /listpost
  delivery/              posting ke channel + kirim konten lewat link share
  fsub/                  channel wajib join, invite link, teks subscription
  hashtag/               daftar hashtag + gambar per hashtag
  buttons/               tombol custom di postingan channel
  whitelist/             whitelist upload
  thumbnail/             thumbnail default channel
  broadcast/             /bc /bcfoto /bcvideo
```

Tiap fitur: `queries.py` (akses database) dan `handlers.py` (command/callback).
