import re
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from config import CHANNEL_ID
from core.database import c
from core.logger import get_logger
from features.buttons.queries import get_channel_buttons
from features.hashtag.queries import get_hashtag_image

log = get_logger(__name__)


def send_to_channel_with_thumbnail_only(bot, image_data, caption, sender_name, share_link, hashtag_text=""):
    """Kirim ke channel: Gunakan gambar hashtag jika ada, fallback ke thumbnail - HTML ONLY"""

    selected_hashtags = []

    if hashtag_text:
        matches = re.findall(r'📬\s*([^,\s]+)', hashtag_text)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    if not selected_hashtags and caption:
        matches = re.findall(r'📬\s*([^,\s]+)', caption)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    if not selected_hashtags and hashtag_text:
        parts = hashtag_text.split()
        for part in parts:
            if part.startswith('📬'):
                selected_hashtags.append(part)

    if not selected_hashtags and caption:
        parts = caption.split()
        for part in parts:
            if part.startswith('📬'):
                selected_hashtags.append(part)

    hashtag_image_data = None
    hashtag_image_file_id = None

    if selected_hashtags:
        for tag in selected_hashtags:
            img = get_hashtag_image(tag)
            if img:
                file_id, file_data, _ = img
                hashtag_image_data = file_data
                hashtag_image_file_id = file_id
                break

    if not hashtag_image_data and not hashtag_image_file_id:
        c.execute("SELECT value FROM config WHERE key = 'thumbnail_id'")
        result = c.fetchone()
        if result:
            hashtag_image_file_id = result[0]

    clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip() if caption else ""
    clean_caption = re.sub(r'#\w+', '', clean_caption).strip() if clean_caption else ""
    clean_caption = re.sub(r'\s+', ' ', clean_caption)

    clean_hashtag = " ".join(selected_hashtags) if selected_hashtags else ""

    safe_caption = clean_caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_caption else ""
    safe_hashtag = clean_hashtag.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_hashtag else ""

    text = ""

    if safe_hashtag:
        text += f"<blockquote>{safe_hashtag}</blockquote>\n\n"

    if safe_caption:
        text += f"{safe_caption}\n\n"

    text += f"◈ {share_link}\n\n"
    text += f"<blockquote>Jangan lupa untuk react & komen\nkirim pap ke @RATEDZBOT</blockquote>"

    custom_buttons = get_channel_buttons(CHANNEL_ID)
    reply_markup = None
    if custom_buttons:
        keyboard = []
        for btn_text, btn_url, position in custom_buttons:
            keyboard.append([InlineKeyboardButton(btn_text, url=btn_url)])
        reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if hashtag_image_data:
            sent_msg = bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=hashtag_image_data,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif hashtag_image_file_id:
            sent_msg = bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=hashtag_image_file_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            sent_msg = bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        return sent_msg.message_id
    except Exception as e:
        log.error(f"Gagal kirim ke channel: {e}", exc_info=True)
        try:
            if hashtag_image_data:
                sent_msg = bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=hashtag_image_data,
                    caption=text,
                    reply_markup=reply_markup
                )
            elif hashtag_image_file_id:
                sent_msg = bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=hashtag_image_file_id,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                sent_msg = bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    reply_markup=reply_markup
                )
            return sent_msg.message_id
        except:
            return None


def send_video_to_channel_with_thumbnail(bot, video, caption, sender_name, share_link, hashtag_text=""):
    """Kirim video ke channel dengan thumbnail - HTML ONLY"""

    selected_hashtags = []

    if hashtag_text:
        matches = re.findall(r'📬\s*([^,\s]+)', hashtag_text)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    if not selected_hashtags and caption:
        matches = re.findall(r'📬\s*([^,\s]+)', caption)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    if not selected_hashtags and hashtag_text:
        parts = hashtag_text.split()
        for part in parts:
            if part.startswith('📬'):
                selected_hashtags.append(part)

    if not selected_hashtags and caption:
        parts = caption.split()
        for part in parts:
            if part.startswith('📬'):
                selected_hashtags.append(part)

    hashtag_image_data = None
    hashtag_image_file_id = None

    if selected_hashtags:
        for tag in selected_hashtags:
            img = get_hashtag_image(tag)
            if img:
                file_id, file_data, _ = img
                hashtag_image_data = file_data
                hashtag_image_file_id = file_id
                break
            else:
                pass

    if not hashtag_image_data and not hashtag_image_file_id:
        c.execute("SELECT value FROM config WHERE key = 'thumbnail_id'")
        result = c.fetchone()
        if result:
            hashtag_image_file_id = result[0]

    clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip() if caption else ""
    clean_caption = re.sub(r'#\w+', '', clean_caption).strip() if clean_caption else ""
    clean_caption = re.sub(r'\s+', ' ', clean_caption)

    clean_hashtag = " ".join(selected_hashtags) if selected_hashtags else ""

    safe_caption_html = clean_caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_caption else ""
    safe_hashtag_html = clean_hashtag.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_hashtag else ""

    text_html = ""

    if safe_hashtag_html:
        text_html += f"<blockquote>{safe_hashtag_html}</blockquote>\n\n"

    if safe_caption_html:
        text_html += f"{safe_caption_html}\n\n"

    text_html += f"◈ {share_link}\n\n"
    text_html += f"<blockquote>Minimal banget nih react & komen kosyakk\nKirim pap ke @RATEDZBOT</blockquote>"

    custom_buttons = get_channel_buttons(CHANNEL_ID)
    reply_markup = None
    if custom_buttons:
        keyboard = []
        for btn_text, btn_url, position in custom_buttons:
            keyboard.append([InlineKeyboardButton(btn_text, url=btn_url)])
        reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if hashtag_image_data:
            sent_msg = bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=hashtag_image_data,
                caption=text_html,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        elif hashtag_image_file_id:
            sent_msg = bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=hashtag_image_file_id,
                caption=text_html,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        else:
            sent_msg = bot.send_message(
                chat_id=CHANNEL_ID,
                text=text_html,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        return sent_msg.message_id
    except Exception as e:
        log.error(f"Gagal kirim video thumbnail: {e}", exc_info=True)
        return None


def send_gif_to_channel_with_thumbnail(bot, file_id, caption, sender_name, share_link, hashtag_text=""):
    """Kirim ke channel: HANYA gambar hashtag + caption + link (GIF TIDAK DIKIRIM KE CHANNEL)"""

    selected_hashtags = []

    if hashtag_text:
        matches = re.findall(r'📬\s*([^,\s]+)', hashtag_text)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    if not selected_hashtags and caption:
        matches = re.findall(r'📬\s*([^,\s]+)', caption)
        if matches:
            for match in matches:
                selected_hashtags.append(f"📬 {match}")

    hashtag_image_file_id = None

    if selected_hashtags:
        for tag in selected_hashtags:
            c.execute('SELECT file_id FROM hashtag_images WHERE tag = ? AND is_active = 1', (tag,))
            result = c.fetchone()
            if result:
                hashtag_image_file_id = result[0]
                break

    if not hashtag_image_file_id:
        c.execute("SELECT value FROM config WHERE key = 'thumbnail_id'")
        result = c.fetchone()
        if result:
            hashtag_image_file_id = result[0]

    clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip() if caption else ""
    clean_caption = re.sub(r'#\w+', '', clean_caption).strip() if clean_caption else ""
    clean_caption = re.sub(r'\s+', ' ', clean_caption)
    clean_hashtag = " ".join(selected_hashtags) if selected_hashtags else ""

    safe_caption = clean_caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_caption else ""
    safe_hashtag = clean_hashtag.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if clean_hashtag else ""

    text = ""

    if safe_hashtag:
        text += f"<blockquote>{safe_hashtag}</blockquote>\n\n"

    if safe_caption:
        text += f"{safe_caption}\n\n"

    text += f"◈ {share_link}\n\n"
    text += f"<blockquote>Minimal banget nih react & komen kosyakk\nKirim pap ke @RATEDZBOT</blockquote>"

    custom_buttons = get_channel_buttons(CHANNEL_ID)
    reply_markup = None
    if custom_buttons:
        keyboard = []
        for btn_text, btn_url, position in custom_buttons:
            keyboard.append([InlineKeyboardButton(btn_text, url=btn_url)])
        reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if hashtag_image_file_id:
            sent_msg = bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=hashtag_image_file_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return sent_msg.message_id
        else:
            sent_msg = bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return sent_msg.message_id
    except Exception as e:
        log.error(f"Gagal kirim: {e}", exc_info=True)
        return None
