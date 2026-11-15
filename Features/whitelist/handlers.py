from core.helpers import is_admin
from features.whitelist.queries import add_to_whitelist, get_whitelist, remove_from_whitelist


def whitelist_command(update, context):
    """Tambah user ke whitelist - /whitelist user_id [notes]"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/whitelist user_id [catatan]\n\n"
            "Contoh: /whitelist 123456789\n"
            "/whitelist 123456789 User premium\n\n"
            "Gunakan /unwhitelist user_id untuk menghapus.\n"
            "Gunakan /whitelistlist untuk melihat daftar."
        )
        return

    try:
        target_id = int(context.args[0])
        notes = " ".join(context.args[1:]) if len(context.args) > 1 else ""

        try:
            user = context.bot.get_chat(target_id)
            user_name = user.first_name or str(target_id)
        except:
            user_name = str(target_id)

        add_to_whitelist(target_id, user_id, notes)

        update.message.reply_text(
            f"✅ **User berhasil ditambahkan ke whitelist!**\n\n"
            f"👤 User: {user_name}\n"
            f"🆔 ID: `{target_id}`\n"
            f"📝 Catatan: {notes if notes else '-'}"
        )
    except ValueError:
        update.message.reply_text("❌ User ID harus berupa angka!")


def unwhitelist_command(update, context):
    """Hapus user dari whitelist - /unwhitelist user_id"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /unwhitelist user_id")
        return

    try:
        target_id = int(context.args[0])
        remove_from_whitelist(target_id)
        update.message.reply_text(f"✅ User `{target_id}` berhasil dihapus dari whitelist!", parse_mode="Markdown")
    except ValueError:
        update.message.reply_text("❌ User ID harus berupa angka!")


def whitelist_list_command(update, context):
    """Lihat daftar whitelist - /whitelistlist"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    whitelist = get_whitelist()

    if not whitelist:
        update.message.reply_text("📭 Belum ada user di whitelist.")
        return

    text = "✅ **DAFTAR WHITELIST UPLOAD**\n\n"
    for i, (uid, username, added_at, notes) in enumerate(whitelist, 1):
        display_name = username if username else str(uid)
        text += f"{i}. `{uid}` - {display_name}\n"
        text += f"   📅 {added_at[:10]}\n"
        if notes:
            text += f"   📝 {notes}\n"
        text += "\n"

    update.message.reply_text(text, parse_mode="Markdown")
