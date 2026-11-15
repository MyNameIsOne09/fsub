from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from config import ADMIN_IDS
from core.database import conn, c
from core.logger import get_logger
from features.approval.queries import get_approval_groups

log = get_logger(__name__)


def send_approval_notification(bot, approval_id, data):
    """Kirim notifikasi approval ke grup yang sudah diset (Support Gambar, Video & GIF)"""
    groups = get_approval_groups()

    if not groups:
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    chat_id=admin_id,
                    text=f"<blockquote>Belum ada database yang diset!\n\nGunakan /setgrup untuk database</blockquote>",
                    parse_mode="HTML"
                )
            except:
                pass
        return

    keyboard = [
        [
            InlineKeyboardButton("ACC", callback_data=f"approve_{approval_id}"),
            InlineKeyboardButton("TOLAK", callback_data=f"reject_{approval_id}")
        ],
        [InlineKeyboardButton("CAPTION", callback_data=f"setcaption_{approval_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    media_type = data.get('media_type', 'photo')
    sender_name = data.get('sender_name', 'Unknown')
    sender_id = data.get('sender_id', 0)
    caption = data.get('caption', '')
    file_data = data.get('file_data')
    file_id = data.get('file_id')
    duration = data.get('duration', 0)
    width = data.get('width', 0)
    height = data.get('height', 0)
    file_size = data.get('file_size', 0)

    safe_sender = sender_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    safe_caption = caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if caption else ''

    if media_type == 'photo':
        media_emoji = "Gambar"
        media_info = ""
    elif media_type == 'video':
        media_emoji = "Video"
        media_info = f"\nDurasi : {duration} detik"
        if width and height:
            media_info += f"\nResolusi : {width}x{height}"
        if file_size:
            media_info += f"\nUkuran : {file_size // (1024*1024)} MB"
    elif media_type == 'gif':
        media_emoji = "GIF"
        media_info = f"\nDurasi : {duration} detik"
        if width and height:
            media_info += f"\nResolusi : {width}x{height}"
    else:
        media_emoji = "Media"
        media_info = ""

    text = f"""<blockquote>🆕 ADA PAP BARU NIH GENK

ID : <code>{approval_id}</code>
Tipe : {media_emoji}
Pengirim : {safe_sender}
ID User : <code>{sender_id}</code>
Caption : {safe_caption[:200]}{'...' if len(safe_caption) > 200 else ''}{media_info}</blockquote>
<i>Created by : @zenstoreni</i>"""

    for chat_id, chat_title in groups:
        try:
            sent_msg = None

            if media_type == 'photo' and file_data:
                sent_msg = bot.send_photo(
                    chat_id=chat_id,
                    photo=file_data,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif media_type == 'gif' and file_id:
                sent_msg = bot.send_animation(
                    chat_id=chat_id,
                    animation=file_id,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    timeout=120
                )
            elif media_type == 'video' and file_id:
                sent_msg = bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    timeout=120,
                    supports_streaming=True
                )
            else:
                sent_msg = bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )

            if sent_msg:
                c.execute('''
                    UPDATE pending_approvals
                    SET message_id = ?, chat_id = ?
                    WHERE id = ?
                ''', (sent_msg.message_id, chat_id, approval_id))
                conn.commit()
        except Exception as e:
            log.error(f"Gagal kirim notifikasi ke {chat_title}: {e}", exc_info=True)
            try:
                sent_msg = bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                c.execute('''
                    UPDATE pending_approvals
                    SET message_id = ?, chat_id = ?
                    WHERE id = ?
                ''', (sent_msg.message_id, chat_id, approval_id))
                conn.commit()
            except Exception as e2:
                log.error(f"Gagal kirim fallback ke {chat_title}: {e2}", exc_info=True)
