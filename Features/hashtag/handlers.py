from core.database import c
from core.logger import get_logger
from core.helpers import download_file, is_admin
from features.hashtag.queries import add_hashtag, get_all_hashtag_images, get_available_hashtags, remove_hashtag, remove_hashtag_image, set_hashtag_image

log = get_logger(__name__)


def add_hashtag_command(update, context):
    """Tambah hashtag baru - /settag (🫦namatag)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /settag (🫦namatag)\n\nContoh: /settag (🫦cewe)")
        return

    tag = " ".join(context.args)

    add_hashtag(tag)
    update.message.reply_text(f"✅ Hashtag {tag} berhasil ditambahkan!")


def list_hashtags_command(update, context):
    """Lihat daftar hashtag - /listtags"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    tags = get_available_hashtags()

    if not tags:
        update.message.reply_text("📭 Belum ada hashtag yang tersedia.")
        return

    text = "🏷️ **DAFTAR HASHTAG**\n\n"
    for i, tag in enumerate(tags, 1):
        text += f"{i}. `{tag}`\n"

    update.message.reply_text(text, parse_mode="Markdown")


def remove_hashtag_command(update, context):
    """Hapus hashtag - /rmtag (🫦tag)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /rmtag (🫦namatag)\n\nContoh: /rmtag (🫦cewe)")
        return

    tag = " ".join(context.args)

    remove_hashtag(tag)
    update.message.reply_text(f"✅ Hashtag {tag} berhasil dihapus!")


def set_hashtag_image_command(update, context):
    """Set gambar untuk hashtag - /setimg hashtag (reply ke gambar atau video)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa mengatur gambar hashtag!")
        return

    if len(context.args) < 1:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/setimg hashtag (reply ke gambar atau video)\n\n"
            "Contoh: Kirim gambar/video, lalu reply dengan `/setimg 📬 Boys`\n\n"
            "📌 Gambar ini akan muncul di channel untuk postingan dengan hashtag tersebut.",
            parse_mode="Markdown"
        )
        return

    tag = " ".join(context.args)

    available_tags = get_available_hashtags()

    if tag not in available_tags:
        update.message.reply_text(
            f"❌ Hashtag `{tag}` tidak tersedia!\n\n"
            f"Hashtag yang tersedia:\n" + "\n".join([f"• {t}" for t in available_tags]),
            parse_mode="Markdown"
        )
        return

    replied = update.message.reply_to_message
    if not replied:
        update.message.reply_text(
            "❌ **Salah!**\n\n"
            "Cara yang benar:\n"
            "1. Kirim gambar atau video\n"
            "2. Klik media -> Reply\n"
            "3. Ketik `/setimg 📬 Boys`"
        )
        return

    media_type = None
    file_id = None
    caption = replied.caption or ""

    if replied.photo:
        photo = replied.photo[-1]
        file_id = photo.file_id
        media_type = "photo"
    elif replied.video:
        video = replied.video
        file_id = video.file_id
        media_type = "video"

        try:
            update.message.reply_text(
                f"⚠️ Untuk video, gambar hashtag akan menggunakan thumbnail video.\n"
                f"Pastikan video memiliki thumbnail yang bagus.",
                parse_mode="Markdown"
            )
        except Exception as e:
            log.error(f"Error getting video thumbnail: {e}", exc_info=True)
    else:
        update.message.reply_text(
            "❌ **Reply harus ke GAMBAR atau VIDEO!**\n\n"
            "Kirim gambar atau video, lalu reply dengan `/setimg 📬 Boys`"
        )
        return

    processing_msg = update.message.reply_text("⏳ Memproses media...")
    file_data = download_file(context.bot, file_id)

    if file_data:
        success = set_hashtag_image(tag, file_id, file_data, caption, user_id)

        if success:
            processing_msg.edit_text(
                f"✅ **Gambar untuk hashtag `{tag}` berhasil diset!**\n\n"
                f"📂 **Tipe:** {'📸 Gambar' if media_type == 'photo' else '🎬 Video (thumbnail)'}\n"
                f"📝 **Caption:** {caption if caption else '(kosong)'}\n\n"
                f"📌 Gambar ini akan muncul di channel untuk postingan dengan hashtag `{tag}`.",
                parse_mode="Markdown"
            )
        else:
            processing_msg.edit_text(
                f"❌ **Gagal menyimpan gambar untuk hashtag `{tag}`!**\n\n"
                f"Silakan coba lagi.",
                parse_mode="Markdown"
            )
    else:
        processing_msg.edit_text("❌ Gagal mengunduh media!")


def remove_hashtag_image_command(update, context):
    """Hapus gambar hashtag - /rmimg hashtag"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa menghapus gambar hashtag!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /rmimg hashtag\n\nContoh: /rmimg (🫦cewe)")
        return

    tag = " ".join(context.args)

    if remove_hashtag_image(tag):
        update.message.reply_text(f"✅ Gambar untuk hashtag `{tag}` berhasil dihapus!", parse_mode="Markdown")
    else:
        update.message.reply_text(f"❌ Gambar untuk hashtag `{tag}` tidak ditemukan!", parse_mode="Markdown")


def list_hashtag_images_command(update, context):
    """Lihat daftar gambar hashtag - /listimg"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa melihat daftar gambar hashtag!")
        return

    images = get_all_hashtag_images()

    if not images:
        update.message.reply_text("📭 Belum ada gambar yang diset untuk hashtag.")
        return

    text = "🖼️ **DAFTAR GAMBAR HASHTAG**\n\n"
    for tag, file_id, caption, set_at in images:
        text += f"🏷️ {tag}\n"
        text += f"   📝 {caption[:50] if caption else '(kosong)'}\n\n"

    text += "💡 Gunakan /rmimg hashtag untuk menghapus gambar."

    update.message.reply_text(text, parse_mode="Markdown")


def check_hashtag_image_command(update, context):
    """Cek apakah hashtag punya gambar - /checkimg hashtag"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /checkimg hashtag\n\nContoh: /checkimg 📬 Girls")
        return

    tag = " ".join(context.args)

    c.execute('SELECT tag, file_id, is_active FROM hashtag_images WHERE tag = ?', (tag,))
    result = c.fetchone()

    if result:
        tag_db, file_id, is_active = result
        update.message.reply_text(
            f"<b>Hashtag:</b> {tag_db}\n"
            f"<b>File ID:</b> <code>{file_id}</code>\n"
            f"<b>Status:</b> {'✅ Aktif' if is_active == 1 else '❌ Nonaktif'}",
            parse_mode="HTML"
        )
    else:
        c.execute('SELECT tag, file_id, is_active FROM hashtag_images WHERE tag LIKE ? AND is_active = 1', (f'%{tag}%',))
        result = c.fetchone()
        if result:
            tag_db, file_id, is_active = result
            update.message.reply_text(
                f"<b>Hashtag:</b> {tag_db} (ditemukan dengan LIKE)\n"
                f"<b>File ID:</b> <code>{file_id}</code>\n"
                f"<b>Status:</b> {'✅ Aktif' if is_active == 1 else '❌ Nonaktif'}",
                parse_mode="HTML"
            )
        else:
            c.execute('SELECT tag, is_active FROM hashtag_images')
            all_tags = c.fetchall()
            if all_tags:
                tag_list = "\n".join([f"• {t[0]} ({'✅ Aktif' if t[1] == 1 else '❌ Nonaktif'})" for t in all_tags])
                update.message.reply_text(
                    f"<b>Tidak ada gambar untuk hashtag:</b> <code>{tag}</code>\n\n"
                    f"<b>Daftar hashtag di database:</b>\n{tag_list}",
                    parse_mode="HTML"
                )
            else:
                update.message.reply_text(
                    f"<b>Tidak ada gambar untuk hashtag:</b> <code>{tag}</code>\n\n"
                    f"Database hashtag_images kosong.",
                    parse_mode="HTML"
                )
