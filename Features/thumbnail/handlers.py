from core.database import conn, c
from core.helpers import is_admin


def set_thumbnail(update, context):
    """Set thumbnail - REPLY ke gambar yang sudah dikirim"""
    user = update.effective_user

    if not is_admin(user.id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if not update.message.reply_to_message:
        update.message.reply_text(
            "❌ **Salah!**\n\n"
            "Cara yang benar:\n"
            "1. Kirim gambar\n"
            "2. Klik gambar -> Reply\n"
            "3. Ketik /setthumb"
        )
        return

    replied = update.message.reply_to_message

    if replied.photo:
        photo = replied.photo[-1]
        file_id = photo.file_id

        c.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('thumbnail_id', ?)", (file_id,))
        conn.commit()

        update.message.reply_text("✅ Thumbnail saved!")
    elif replied.document and replied.document.mime_type.startswith('image/'):
        file_id = replied.document.file_id
        c.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('thumbnail_id', ?)", (file_id,))
        conn.commit()
        update.message.reply_text("✅ Thumbnail saved!")
    else:
        update.message.reply_text("❌ Reply harus ke GAMBAR, bukan ke teks!")


def get_thumbnail(update, context):
    """Lihat thumbnail yang sedang aktif"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Anda bukan admin!")
        return

    c.execute("SELECT value FROM config WHERE key = 'thumbnail_id'")
    result = c.fetchone()

    if result:
        thumbnail_id = result[0]
        update.message.reply_photo(
            photo=thumbnail_id,
            caption="🖼️ Thumbnail saat ini\n\nGunakan /setthumb untuk mengganti"
        )
    else:
        update.message.reply_text("❌ Belum ada thumbnail yang diset!\n\nKirim gambar lalu reply dengan /setthumb")
