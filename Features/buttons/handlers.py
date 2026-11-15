from config import CHANNEL_ID
from core.helpers import is_admin
from features.buttons.queries import add_channel_button, clear_channel_buttons, get_channel_buttons


def add_button_command(update, context):
    """Tambah custom button di channel - /addbutton text url"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 2:
        text = (
            "❌ *Cara penggunaan :*\n"
            "/addbutton TEKS_URL\n\n"
            "Contoh: `/addbutton Nama Channel https://t.me/zensvoidd`"
        )
        update.message.reply_text(text, parse_mode="Markdown")
        return

    button_text = " ".join(context.args[:-1])
    button_url = context.args[-1]

    if not button_url.startswith(("http://", "https://", "t.me/")):
        button_url = f"https://{button_url}"

    existing_buttons = get_channel_buttons(CHANNEL_ID)
    position = len(existing_buttons)

    add_channel_button(CHANNEL_ID, button_text, button_url, position)
    update.message.reply_text(f"✅ Button '{button_text}' berhasil ditambahkan!")


def remove_buttons_command(update, context):
    """Hapus semua custom button - /rmbuttons"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    clear_channel_buttons(CHANNEL_ID)
    update.message.reply_text("✅ Semua custom button telah dihapus!")


def list_buttons_command(update, context):
    """Lihat daftar custom button - /listbuttons"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    buttons = get_channel_buttons(CHANNEL_ID)

    if not buttons:
        update.message.reply_text("📭 Belum ada custom button yang diset.")
        return

    text = "🔘 *DAFTAR CUSTOM BUTTON*\n\n"
    for i, (btn_text, btn_url, position) in enumerate(buttons, 1):
        text += f"{i}. {btn_text}\n"
        text += f"   🔗 {btn_url}\n\n"

    update.message.reply_text(text, parse_mode="Markdown")
