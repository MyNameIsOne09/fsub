import re
from core.database import conn, c
from core.logger import get_logger
from features.fsub.service import check_joined_channel, send_join_channel_button
from features.menu.handlers import start_command

log = get_logger(__name__)


def send_image_from_db(chat_id, bot, image_id):
    """Kirim gambar dengan caption dari pengirim (tanpa hashtag)"""
    c.execute('SELECT file_data, sender_name, caption FROM images WHERE id = ?', (image_id,))
    result = c.fetchone()

    if result:
        file_data, sender_name, caption = result

        clean_caption = ""
        if caption:
            clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip()
            clean_caption = re.sub(r'#\w+', '', clean_caption).strip()
            clean_caption = re.sub(r'\s+', ' ', clean_caption)

        text = ""

        if clean_caption:
            text += f"{clean_caption}\n\n"

        text += f"""<blockquote>Kasih Apresiasi untuk pengirim gambar ini dengan cara react & komen di channel</blockquote>"""

        try:
            bot.send_photo(
                chat_id=chat_id,
                photo=file_data,
                caption=text,
                protect_content=True,
                parse_mode="HTML"
            )
            return True
        except Exception as e:
            log.error(f"Gagal kirim protected: {e}", exc_info=True)
            try:
                bot.send_photo(
                    chat_id=chat_id,
                    photo=file_data,
                    caption=text,
                    parse_mode="HTML"
                )
                return True
            except:
                return False
    return False


def send_video_from_db(chat_id, bot, video_id):
    """Kirim video dengan caption dari pengirim (tanpa hashtag)"""
    c.execute('SELECT file_id, sender_name, caption FROM videos WHERE id = ?', (video_id,))
    result = c.fetchone()

    if result:
        file_id, sender_name, caption = result

        clean_caption = ""
        if caption:
            clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip()
            clean_caption = re.sub(r'#\w+', '', clean_caption).strip()
            clean_caption = re.sub(r'\s+', ' ', clean_caption)

        text = ""

        if clean_caption:
            text += f"{clean_caption}\n\n"

        text += f"""<blockquote>Kasih Apresiasi untuk pengirim video ini dengan cara react & komen di channel</blockquote>"""

        try:
            bot.send_video(
                chat_id=chat_id,
                video=file_id,
                caption=text,
                protect_content=True,
                parse_mode="HTML",
                timeout=60
            )
            return True
        except Exception as e:
            log.error(f"Gagal kirim video: {e}", exc_info=True)
            try:
                bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=text,
                    parse_mode="HTML",
                    timeout=60
                )
                return True
            except:
                return False
    return False


def send_gif_from_db(chat_id, bot, gif_id):
    """Kirim GIF dengan caption dari pengirim (tanpa hashtag)"""
    c.execute('SELECT file_id, sender_name, caption FROM gifs WHERE id = ?', (gif_id,))
    result = c.fetchone()

    if result:
        file_id, sender_name, caption = result

        clean_caption = ""
        if caption:
            clean_caption = re.sub(r'📬\s*[^,\s]+', '', caption).strip()
            clean_caption = re.sub(r'#\w+', '', clean_caption).strip()
            clean_caption = re.sub(r'\s+', ' ', clean_caption)

        text = ""

        if clean_caption:
            text += f"{clean_caption}\n\n"

        text += f"""<blockquote>Kasih Apresiasi untuk pengirim GIF ini dengan cara react & komen di channel</blockquote>"""

        try:
            bot.send_animation(
                chat_id=chat_id,
                animation=file_id,
                caption=text,
                protect_content=True,
                parse_mode="HTML",
                timeout=60
            )
            return True
        except Exception as e:
            log.error(f"Gagal kirim GIF: {e}", exc_info=True)
            try:
                bot.send_animation(
                    chat_id=chat_id,
                    animation=file_id,
                    caption=text,
                    parse_mode="HTML",
                    timeout=60
                )
                return True
            except:
                return False
    return False


def handle_image_link(update, context):
    """Handler untuk link sharing gambar, video, dan GIF"""
    user = update.effective_user
    user_id = user.id

    if context.args and len(context.args) > 0:
        link_code = context.args[0]

        try:
            c.execute('SELECT image_id FROM image_links WHERE link_code = ?', (link_code,))
            result = c.fetchone()

            if not result:
                update.message.reply_text("❌ **Link tidak valid atau sudah kadaluarsa!**", parse_mode="Markdown")
                return

            media_id = result[0]

            c.execute('UPDATE image_links SET views = views + 1 WHERE link_code = ?', (link_code,))
            conn.commit()

            c.execute('SELECT id FROM gifs WHERE id = ?', (media_id,))
            is_gif = c.fetchone() is not None

            c.execute('SELECT id FROM videos WHERE id = ?', (media_id,))
            is_video = c.fetchone() is not None

            c.execute('SELECT id FROM images WHERE id = ?', (media_id,))
            is_image = c.fetchone() is not None

            if is_gif:
                c.execute("INSERT OR REPLACE INTO users (user_id, pending_gif_id) VALUES (?, ?)", (user_id, media_id))
                conn.commit()

                if check_joined_channel(context.bot, user_id):
                    send_gif_from_db(update.message.chat_id, context.bot, media_id)
                    c.execute("UPDATE users SET pending_gif_id = NULL WHERE user_id = ?", (user_id,))
                    conn.commit()
                else:
                    send_join_channel_button(update.message.chat_id, context.bot, link_code, user)
            elif is_video:
                c.execute("INSERT OR REPLACE INTO users (user_id, pending_video_id) VALUES (?, ?)", (user_id, media_id))
                conn.commit()

                if check_joined_channel(context.bot, user_id):
                    send_video_from_db(update.message.chat_id, context.bot, media_id)
                    c.execute("UPDATE users SET pending_video_id = NULL WHERE user_id = ?", (user_id,))
                    conn.commit()
                else:
                    send_join_channel_button(update.message.chat_id, context.bot, link_code, user)
            elif is_image:
                c.execute("INSERT OR REPLACE INTO users (user_id, pending_image_id) VALUES (?, ?)", (user_id, media_id))
                conn.commit()

                if check_joined_channel(context.bot, user_id):
                    send_image_from_db(update.message.chat_id, context.bot, media_id)
                    c.execute("UPDATE users SET pending_image_id = NULL WHERE user_id = ?", (user_id,))
                    conn.commit()
                else:
                    send_join_channel_button(update.message.chat_id, context.bot, link_code, user)
            else:
                update.message.reply_text("❌ Konten tidak ditemukan di database!", parse_mode="Markdown")
                return
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            update.message.reply_text("❌ Link tidak valid, Coba lagi", parse_mode="Markdown")
    else:
        start_command(update, context)


def process_content_by_link(update, context, link_code, query):
    """Proses konten berdasarkan link_code"""
    user_id = update.effective_user.id
    user = update.effective_user

    c.execute('SELECT image_id FROM image_links WHERE link_code = ?', (link_code,))
    result = c.fetchone()

    if result:
        media_id = result[0]

        c.execute('SELECT id FROM images WHERE id = ?', (media_id,))
        is_image = c.fetchone() is not None

        if is_image:
            send_image_from_db(query.message.chat_id, context.bot, media_id)
            query.edit_message_text("✅ BERHASIL! Gambar akan dikirim di bawah ini.")
            c.execute("UPDATE users SET pending_image_id = NULL WHERE user_id = ?", (user_id,))
        else:
            c.execute('SELECT id FROM videos WHERE id = ?', (media_id,))
            is_video = c.fetchone() is not None
            if is_video:
                send_video_from_db(query.message.chat_id, context.bot, media_id)
                query.edit_message_text("✅ BERHASIL! Video akan dikirim di bawah ini.")
                c.execute("UPDATE users SET pending_video_id = NULL WHERE user_id = ?", (user_id,))
            else:
                query.edit_message_text("❌ **Konten tidak ditemukan!**")
                return
        conn.commit()
    else:
        query.edit_message_text("❌ Link tidak valid, Coba Lagi")
