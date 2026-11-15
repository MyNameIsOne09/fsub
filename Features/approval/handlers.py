from datetime import datetime
import hashlib
import re
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from config import CHANNEL_USERNAME, CHANNEL_ID
from core.database import conn, c
from core.logger import get_logger
from core.helpers import is_admin
from features.approval.queries import add_approval_group, approve_content, clear_caption_state, delete_posted_content, get_all_pending_approvals, get_all_posted_content, get_approval_groups, get_approval_stats, get_caption_state, get_pending_approval, get_posted_content_by_approval, is_approval_group, reject_content, remove_approval_group, save_caption_state, save_posted_content
from features.delivery.channel import send_gif_to_channel_with_thumbnail, send_to_channel_with_thumbnail_only, send_video_to_channel_with_thumbnail

log = get_logger(__name__)


def handle_caption_input(update, context):
    """Handler untuk menerima caption dari admin setelah klik SET CAPTION"""
    user_id = update.effective_user.id

    approval_id, pending_data = get_caption_state(user_id)

    if not approval_id or not pending_data:
        if hasattr(handle_approval_callback, "awaiting_caption"):
            if user_id in handle_approval_callback.awaiting_caption:
                pending_data = handle_approval_callback.awaiting_caption[user_id]
                approval_id = pending_data['approval_id']
            else:
                return
        else:
            return

    caption_text = update.message.text

    if not caption_text or not caption_text.strip():
        update.message.reply_text(
            "❌ **Caption tidak boleh kosong!**\n\n"
            "Kirim ulang caption yang valid.",
            parse_mode="Markdown"
        )
        return

    try:
        c.execute('''
            UPDATE pending_approvals
            SET admin_caption = ?
            WHERE id = ?
        ''', (caption_text, approval_id))
        conn.commit()

        c.execute('SELECT admin_caption FROM pending_approvals WHERE id = ?', (approval_id,))
        result = c.fetchone()

        clear_caption_state(user_id)

        if hasattr(handle_approval_callback, "awaiting_caption"):
            if user_id in handle_approval_callback.awaiting_caption:
                del handle_approval_callback.awaiting_caption[user_id]

        update.message.reply_text(
            f"<blockquote>✅ Caption berhasil diset!\n\nSilahkan klik tombol ACC untuk post ke channel</blockquote>",
            parse_mode="HTML"
        )

        c.execute('SELECT chat_id, message_id FROM pending_approvals WHERE id = ?', (approval_id,))
        result = c.fetchone()
        if result:
            chat_id_db, message_id_db = result

            keyboard = [
                [
                    InlineKeyboardButton("ACC", callback_data=f"approve_{approval_id}"),
                    InlineKeyboardButton("TOLAK", callback_data=f"reject_{approval_id}")
                ],
                [InlineKeyboardButton("CAPTION SET", callback_data=f"setcaption_{approval_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            media_emoji = "Gambar" if pending_data.get('media_type') == 'photo' else "Video"
            safe_sender = pending_data.get('sender_name', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_caption = pending_data.get('caption', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if pending_data.get('caption') else ''

            text_baru = f"<blockquote>🆕 ADA PAP BARU NIH GENK\n\n"
            text_baru += f"ID : <code>{approval_id}</code>\n"
            text_baru += f"Tipe : {media_emoji}\n"
            text_baru += f"Pengirim : {safe_sender}\n"
            text_baru += f"ID User : <code>{pending_data.get('sender_id')}</code>\n"
            text_baru += f"Caption Admin : {caption_text}\n"
            text_baru += f"Caption Sender : {safe_caption[:200]}{'...' if len(safe_caption) > 200 else ''}</blockquote>\n"
            text_baru += f"<i>Created by : @zenstoreni</i>"

            try:
                context.bot.edit_message_caption(
                    chat_id=chat_id_db,
                    message_id=message_id_db,
                    caption=text_baru,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                log.error(f"Gagal edit caption: {e}", exc_info=True)
                try:
                    context.bot.edit_message_text(
                        chat_id=chat_id_db,
                        message_id=message_id_db,
                        text=text_baru,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                except Exception as e2:
                    log.error(f"Gagal edit text: {e2}", exc_info=True)
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
        log.error(f"Error di handle_caption_input: {e}", exc_info=True)


def handle_approval_callback(update, context):
    """Handler untuk tombol ACC/TOLAK dan Set Caption"""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if not is_admin(user_id):
        query.answer("❌ Hanya admin bot yang bisa acc!", show_alert=True)
        return

    if data.startswith("approve_"):
        try:
            approval_id = int(data.split("_")[1])

            pending = get_pending_approval(approval_id)

            if not pending:
                query.answer("❌ ID Gambar tidak ditemukan!", show_alert=True)
                try:
                    query.edit_message_text("❌ Approval ID tidak ditemukan atau sudah diproses!")
                except:
                    pass
                return

            (
                id, media_type, file_id, file_data, sender_id, sender_name,
                username, caption, file_size, duration, width, height,
                hashtags, status, admin_caption, approved_by, approved_at,
                created_at, message_id, chat_id
            ) = pending

            try:
                share_link = None
                channel_post_link = None
                media_id = None
                channel_message_id = None
                link_code = None

                if admin_caption and admin_caption.strip():
                    admin_caption_text = admin_caption
                else:
                    admin_caption_text = re.sub(r'📬\s*[^,\s]+', '', caption).strip() if caption else ""
                    admin_caption_text = re.sub(r'#\w+', '', admin_caption_text).strip() if admin_caption_text else ""
                    admin_caption_text = re.sub(r'\s+', ' ', admin_caption_text)

                raw = f"{id}_{datetime.now().timestamp()}"
                link_code = hashlib.md5(raw.encode()).hexdigest()[:10]

                if media_type == 'photo':
                    c.execute('''
                        INSERT INTO images (file_id, file_data, sender_id, sender_name, username, caption, file_size, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (file_id, file_data, sender_id, sender_name, username, caption, file_size, datetime.now().isoformat()))
                    conn.commit()
                    media_id = c.lastrowid

                    share_link = f"https://t.me/{context.bot.username}?start={link_code}"

                    channel_message_id = send_to_channel_with_thumbnail_only(
                        context.bot,
                        file_data,
                        admin_caption_text,
                        sender_name,
                        share_link,
                        hashtags
                    )
                elif media_type == 'video':
                    c.execute('''
                        INSERT INTO videos (file_id, file_data, sender_id, sender_name, username, caption, file_size, duration, width, height, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (file_id, None, sender_id, sender_name, username, caption, file_size, duration, width, height, datetime.now().isoformat()))
                    conn.commit()
                    media_id = c.lastrowid

                    share_link = f"https://t.me/{context.bot.username}?start={link_code}"

                    class SimpleVideo:
                        def __init__(self, dur):
                            self.duration = dur
                    simple_video = SimpleVideo(duration)
                    channel_message_id = send_video_to_channel_with_thumbnail(
                        context.bot,
                        simple_video,
                        admin_caption_text,
                        sender_name,
                        share_link,
                        hashtags
                    )
                elif media_type == 'gif':
                    c.execute('''
                        INSERT INTO gifs (file_id, sender_id, sender_name, username, caption, file_size, duration, width, height, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (file_id, sender_id, sender_name, username, caption, file_size, duration, width, height, datetime.now().isoformat()))
                    conn.commit()
                    media_id = c.lastrowid

                    share_link = f"https://t.me/{context.bot.username}?start={link_code}"

                    channel_message_id = send_gif_to_channel_with_thumbnail(
                        context.bot,
                        file_id,
                        admin_caption_text,
                        sender_name,
                        share_link,
                        hashtags
                    )

                c.execute('''
                    INSERT INTO image_links (image_id, link_code, created_at)
                    VALUES (?, ?, ?)
                ''', (media_id, link_code, datetime.now().isoformat()))
                conn.commit()

                if channel_message_id:
                    channel_username = CHANNEL_USERNAME.replace('@', '')
                    channel_post_link = f"https://t.me/{channel_username}/{channel_message_id}"

                approve_content(approval_id, user_id, admin_caption)

                try:
                    save_posted_content(
                        approval_id=approval_id,
                        media_type=media_type,
                        media_id=media_id,
                        channel_message_id=channel_message_id,
                        channel_chat_id=CHANNEL_ID,
                        link_code=link_code,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        admin_id=user_id
                    )
                except Exception as e:
                    log.error(f"Gagal simpan data postingan: {e}", exc_info=True)

                try:
                    if username:
                        mention = f"@{username}"
                    else:
                        mention = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

                    if media_type == 'photo':
                        media_emoji = "📸 Foto"
                    elif media_type == 'video':
                        media_emoji = "🎬 Video"
                    else:
                        media_emoji = "🎞️ GIF"

                    notif_text = f"<blockquote>{media_emoji} anda sudah disetujui dan diposting!</blockquote>\n"
                    notif_text += f"Caption : {admin_caption if admin_caption else caption}\n\n"
                    notif_text += f"<blockquote>Created by : @zenstoreni</blockquote>"

                    keyboard = []
                    if channel_post_link:
                        keyboard.append([InlineKeyboardButton("ᴄᴇᴋ ᴘᴏsᴛɪɴɢᴀɴ", url=channel_post_link)])
                    else:
                        keyboard.append([InlineKeyboardButton("ᴏᴘᴇɴ ʟɪɴᴋ", url=share_link)])

                    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

                    context.bot.send_message(
                        chat_id=sender_id,
                        text=notif_text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    log.error(f"Gagal kirim notifikasi ke pengirim: {e}", exc_info=True)

                try:
                    if chat_id and message_id:
                        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception as e:
                    log.error(f"Gagal hapus pesan approval: {e}", exc_info=True)

                try:
                    query.edit_message_text(
                        f"✅ KONTEN BERHASIL DI-APPROVE!\n\n"
                        f"📌 ID: {approval_id}\n"
                        f"👤 Pengirim: {mention if username else sender_name}\n"
                        f"📝 Caption: {admin_caption if admin_caption else caption}\n"
                        f"🔗 Link: {share_link}\n"
                        f"📢 Link Channel: {channel_post_link if channel_post_link else '-'}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    log.error(f"Gagal edit pesan konfirmasi: {e}", exc_info=True)
                    try:
                        query.message.reply_text(
                            f"<blockquote>KONTEN BERHASIL DI-ACC\n"
                            f"👤 Pengirim : {mention if username else sender_name}",
                            parse_mode="HTML"
                        )
                    except:
                        pass

                try:
                    query.message.edit_reply_markup(reply_markup=None)
                except:
                    pass
            except Exception as e:
                log.error(f"Error saat memproses ACC: {e}", exc_info=True)
                try:
                    query.edit_message_text(f"❌ Error: {e}")
                except:
                    query.message.reply_text(f"❌ Error: {e}")
        except Exception as e:
            log.error(f"Error di handler approve: {e}", exc_info=True)
            query.answer(f"Error: {e}", show_alert=True)
    elif data.startswith("reject_"):
        try:
            approval_id = int(data.split("_")[1])

            pending = get_pending_approval(approval_id)

            if not pending:
                query.answer("❌ ID Gambar tidak ditemukan!", show_alert=True)
                try:
                    query.edit_message_text("❌ ID Gambar tidak ditemukan atau sudah diproses!")
                except:
                    pass
                return

            (
                id, media_type, file_id, file_data, sender_id, sender_name,
                username, caption, file_size, duration, width, height,
                hashtags, status, admin_caption, approved_by, approved_at,
                created_at, message_id, chat_id
            ) = pending

            reject_content(approval_id, user_id)

            try:
                if username:
                    mention = f"@{username}"
                else:
                    mention = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

                context.bot.send_message(
                    chat_id=sender_id,
                    text=(
                        f"<blockquote>❌ Foto anda ditolak oleh admin</blockquote>"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                log.error(f"Gagal kirim notifikasi ke pengirim: {e}", exc_info=True)

            try:
                if chat_id and message_id:
                    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                log.error(f"Gagal hapus pesan approval: {e}", exc_info=True)

            try:
                query.edit_message_text(
                    f"❌ KONTEN DITOLAK!\n\n"
                    f"📌 ID: {approval_id}\n"
                    f"👤 Pengirim: {mention if username else sender_name}\n"
                    f"👤 Admin: {query.from_user.first_name}",
                    parse_mode="HTML"
                )
            except:
                pass

            try:
                query.message.edit_reply_markup(reply_markup=None)
            except:
                pass
        except Exception as e:
            log.error(f"Error di handler reject: {e}", exc_info=True)
            query.answer(f"Error: {e}", show_alert=True)
    elif data.startswith("setcaption_"):
        try:
            approval_id = int(data.split("_")[1])

            pending = get_pending_approval(approval_id)
            if not pending:
                query.answer("❌ ID Gambar tidak ditemukan!", show_alert=True)
                return

            (
                id, media_type, file_id, file_data, sender_id, sender_name,
                username, caption, file_size, duration, width, height,
                hashtags, status, admin_caption, approved_by, approved_at,
                created_at, message_id, chat_id
            ) = pending

            state_data = {
                'approval_id': approval_id,
                'media_type': media_type,
                'file_id': file_id,
                'sender_id': sender_id,
                'sender_name': sender_name,
                'username': username,
                'caption': caption,
                'file_size': file_size,
                'duration': duration,
                'width': width,
                'height': height,
                'hashtags': hashtags,
                'status': status,
                'admin_caption': admin_caption,
                'chat_id': chat_id,
                'message_id': message_id
            }

            save_caption_state(user_id, approval_id, state_data)

            if not hasattr(handle_approval_callback, "awaiting_caption"):
                handle_approval_callback.awaiting_caption = {}
            handle_approval_callback.awaiting_caption[user_id] = state_data

            keyboard = [
                [InlineKeyboardButton("BATAL", callback_data=f"cancel_caption_{approval_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if media_type == 'photo':
                media_emoji = "Gambar"
            elif media_type == 'video':
                media_emoji = "Video"
            else:
                media_emoji = "GIF"

            text = (
                f"<blockquote>"
                f"<b>SET CAPTION</b>\n"
                f"ID: {approval_id}\n"
                f"<b>Kirim caption baru dengan cara:</b>\n"
                f"1. Ketik caption yang diinginkan\n"
                f"2. <b>REPLY</b> ke pesan ini"
                f"</blockquote>"
                f"<b>Created by: @zenstoreni</b>"
            )

            sent_msg = query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

            state_data['prompt_message_id'] = sent_msg.message_id
            save_caption_state(user_id, approval_id, state_data)
        except Exception as e:
            log.error(f"Error di handler setcaption: {e}", exc_info=True)
            query.answer(f"Error: {e}", show_alert=True)
    elif data.startswith("caption_input_"):
        try:
            parts = data.split("_")
            approval_id = int(parts[2])
            admin_id = int(parts[3])

            if user_id != admin_id:
                query.answer("❌ Bukan Anda yang meminta caption!", show_alert=True)
                return

            _, state_data = get_caption_state(user_id)

            if not state_data:
                query.answer("❌ State tidak ditemukan!", show_alert=True)
                return

            context.user_data['caption_pending'] = {
                'approval_id': approval_id,
                'user_id': user_id
            }

            query.edit_message_text(
                f"Kirim caption untuk ID {approval_id}:\n\n"
                f"Ketik caption yang diinginkan dan kirim.",
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Error handle caption input: {e}", exc_info=True)
            query.answer(f"Error: {e}", show_alert=True)
    elif data.startswith("cancel_caption_"):
        try:
            approval_id = int(data.split("_")[2])

            clear_caption_state(user_id)

            if hasattr(handle_approval_callback, "awaiting_caption"):
                if user_id in handle_approval_callback.awaiting_caption:
                    del handle_approval_callback.awaiting_caption[user_id]

            pending = get_pending_approval(approval_id)

            if not pending:
                query.answer("❌ ID Gambar tidak ditemukan!", show_alert=True)
                return

            (
                id, media_type, file_id, file_data, sender_id, sender_name,
                username, caption, file_size, duration, width, height,
                hashtags, status, admin_caption, approved_by, approved_at,
                created_at, message_id, chat_id
            ) = pending

            keyboard = [
                [
                    InlineKeyboardButton("ACC", callback_data=f"approve_{approval_id}"),
                    InlineKeyboardButton("TOLAK", callback_data=f"reject_{approval_id}")
                ],
                [InlineKeyboardButton("CAPTION SET", callback_data=f"setcaption_{approval_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if media_type == 'photo':
                media_emoji = "Gambar"
            elif media_type == 'video':
                media_emoji = "Video"
            else:
                media_emoji = "GIF"

            text = f"<blockquote>🆕 ADA PAP BARU NIH GENK\n\n"
            text += f"ID : <code>{approval_id}</code>\n"
            text += f"Tipe : {media_emoji}\n"
            text += f"Pengirim : {sender_name}\n"
            text += f"ID User : <code>{sender_id}</code>\n"
            text += f"Caption : {caption[:200]}{'...' if len(caption) > 200 else ''}</blockquote>\n\n"
            text += f"<i>Created by : @zenstoreni</i>"

            try:
                query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
            except:
                query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception as e:
            log.error(f"Error cancel caption: {e}", exc_info=True)
            query.answer(f"Error: {e}", show_alert=True)


def handle_caption_reply(update, context):
    """Handler untuk menerima caption dari reply pesan"""
    user_id = update.effective_user.id

    approval_id, state_data = get_caption_state(user_id)

    if not approval_id or not state_data:
        return

    if not update.message.reply_to_message:
        return

    caption_text = update.message.text

    if not caption_text or not caption_text.strip():
        update.message.reply_text("❌ Caption tidak boleh kosong!")
        return

    try:
        c.execute('''
            UPDATE pending_approvals
            SET admin_caption = ?
            WHERE id = ?
        ''', (caption_text, approval_id))
        conn.commit()

        clear_caption_state(user_id)

        update.message.reply_text(
            f"<blockquote>Caption berhasil diset!\n"
            f"Caption: {caption_text}\n"
            f"Silahkan klik tombol ACC untuk post ke channel</blockquote>",
            parse_mode="HTML"
        )

        c.execute('SELECT chat_id, message_id FROM pending_approvals WHERE id = ?', (approval_id,))
        result = c.fetchone()
        if result:
            chat_id_db, message_id_db = result

            keyboard = [
                [
                    InlineKeyboardButton("ACC", callback_data=f"approve_{approval_id}"),
                    InlineKeyboardButton("TOLAK", callback_data=f"reject_{approval_id}")
                ],
                [InlineKeyboardButton("CAPTION SET", callback_data=f"setcaption_{approval_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            media_emoji = "Gambar" if state_data.get('media_type') == 'photo' else "Video"
            safe_sender = state_data.get('sender_name', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_caption = state_data.get('caption', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if state_data.get('caption') else ''

            text_baru = f"<blockquote>🆕 ADA PAP BARU NIH GENK\n\n"
            text_baru += f"ID : <code>{approval_id}</code>\n"
            text_baru += f"Tipe : {media_emoji}\n"
            text_baru += f"Pengirim : {safe_sender}\n"
            text_baru += f"ID User : <code>{state_data.get('sender_id')}</code>\n"
            text_baru += f"Caption Admin : {caption_text}\n"
            text_baru += f"Caption Sender : {safe_caption[:200]}{'...' if len(safe_caption) > 200 else ''}</blockquote>\n"
            text_baru += f"<i>Created by : @zenstoreni</i>"

            try:
                context.bot.edit_message_caption(
                    chat_id=chat_id_db,
                    message_id=message_id_db,
                    caption=text_baru,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except:
                try:
                    context.bot.edit_message_text(
                        chat_id=chat_id_db,
                        message_id=message_id_db,
                        text=text_baru,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    log.error(f"Gagal update pesan: {e}", exc_info=True)
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
        log.error(f"Error di handle_caption_reply: {e}", exc_info=True)


def set_admin_caption_command(update, context):
    """Set caption admin untuk approval tertentu"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa melakukan ini!")
        return

    if len(context.args) < 2:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/setadmincaption approval_id caption_anda\n\n"
            "Contoh: `/setadmincaption 123 Ini caption dari admin`",
            parse_mode="Markdown"
        )
        return

    try:
        approval_id = int(context.args[0])
        caption_text = " ".join(context.args[1:])

        pending = get_pending_approval(approval_id)

        if not pending:
            update.message.reply_text("❌ Approval ID tidak ditemukan atau sudah diproses!")
            return

        c.execute('''
            UPDATE pending_approvals
            SET admin_caption = ?
            WHERE id = ?
        ''', (caption_text, approval_id))
        conn.commit()

        update.message.reply_text(
            f"✅ **Caption admin berhasil diset!**\n\n"
            f"📌 ID Approval: `{approval_id}`\n"
            f"📝 Caption: {caption_text}\n\n"
            f"Sekarang klik tombol **ACC** untuk memposting.",
            parse_mode="Markdown"
        )

        c.execute('SELECT chat_id, message_id, media_type FROM pending_approvals WHERE id = ?', (approval_id,))
        result = c.fetchone()

        if result:
            chat_id, message_id, media_type = result

            keyboard = [
                [
                    InlineKeyboardButton("✅ ACC", callback_data=f"approve_{approval_id}"),
                    InlineKeyboardButton("❌ TOLAK", callback_data=f"reject_{approval_id}")
                ],
                [InlineKeyboardButton("📝 Set Caption", callback_data=f"setcaption_{approval_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            (
                _, _, _, _, sender_id, sender_name,
                username, caption, file_size, duration, width, height,
                hashtags, status, admin_caption, approved_by, approved_at,
                created_at, _, _
            ) = pending

            media_emoji = "📸" if media_type == 'photo' else "🎬"
            text_baru = f"🆕 **KONTEN BARU MENUNGGU APPROVAL**\n\n"
            text_baru += f"📌 **ID Approval:** `{approval_id}`\n"
            text_baru += f"📂 **Tipe:** {media_emoji}\n"
            text_baru += f"👤 **Pengirim:** {sender_name}\n"
            text_baru += f"🆔 **User ID:** `{sender_id}`\n"
            text_baru += f"📝 **Caption:** {caption[:200]}{'...' if len(caption) > 200 else ''}\n"
            text_baru += f"🏷️ **Hashtag:** {hashtags if hashtags else '-'}\n"
            text_baru += f"✏️ **Caption Admin:** {caption_text}\n\n"
            text_baru += f"⚠️ Klik tombol di bawah untuk menyetujui atau menolak."

            try:
                context.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=text_baru,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                log.error(f"Gagal edit caption: {e}", exc_info=True)
                try:
                    context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text_baru,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except Exception as e2:
                    log.error(f"Gagal edit text: {e2}", exc_info=True)
                    try:
                        context.bot.send_message(
                            chat_id=chat_id,
                            text=f"✏️ **Caption admin sudah diset!**\n\nID: `{approval_id}`\nCaption: {caption_text}\n\nKlik ACC untuk memposting.",
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    except:
                        pass
    except ValueError:
        update.message.reply_text("❌ Approval ID harus berupa angka!")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


def set_approval_group_command(update, context):
    """Set grup untuk notifikasi approval - /setapprovalgroup (reply ke pesan di grup)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa mengatur grup approval!")
        return

    chat = update.effective_chat

    if chat.type not in ['group', 'supergroup']:
        update.message.reply_text("❌ Perintah ini hanya bisa digunakan di GRUP!")
        return

    chat_id = chat.id
    chat_title = chat.title

    try:
        member = context.bot.get_chat_member(chat_id, context.bot.id)
        if member.status not in ['administrator', 'creator']:
            update.message.reply_text(
                f"❌ Bot BUKAN admin di grup ini!\n\n"
                f"Jadikan bot sebagai admin terlebih dahulu."
            )
            return
    except:
        update.message.reply_text("❌ Bot tidak bisa mengakses grup ini!")
        return

    add_approval_group(chat_id, chat_title)

    update.message.reply_text(
        f"✅ **Grup approval berhasil diset!**\n\n"
        f"📢 **Grup:** {chat_title}\n"
        f"🆔 **ID:** `{chat_id}`\n\n"
        f"📌 Semua notifikasi approval akan dikirim ke grup ini.\n"
        f"Gunakan /removeapprovalgroup untuk menghapus.",
        parse_mode="Markdown"
    )


def remove_approval_group_command(update, context):
    """Hapus grup approval - /removeapprovalgroup"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa menghapus grup approval!")
        return

    chat_id = update.effective_chat.id

    if not is_approval_group(chat_id):
        update.message.reply_text("❌ Grup ini bukan grup approval!")
        return

    remove_approval_group(chat_id)

    update.message.reply_text(
        f"✅ **Grup approval berhasil dihapus!**\n\n"
        f"Notifikasi approval tidak akan dikirim ke grup ini lagi."
    )


def list_approval_groups_command(update, context):
    """Lihat daftar grup approval - /listapprovalgroups"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa melihat grup approval!")
        return

    groups = get_approval_groups()

    if not groups:
        update.message.reply_text(
            "📭 **Belum ada grup approval yang diset.**\n\n"
            "Gunakan /setapprovalgroup di grup yang diinginkan.",
            parse_mode="Markdown"
        )
        return

    text = "📋 **DAFTAR GRUP APPROVAL**\n\n"
    for i, (chat_id, chat_title) in enumerate(groups, 1):
        text += f"{i}. {chat_title}\n"
        text += f"   🆔 ID: `{chat_id}`\n\n"

    text += f"Total: {len(groups)} grup"

    update.message.reply_text(text, parse_mode="Markdown")


def pending_approvals_command(update, context):
    """Lihat daftar pending approvals - /pending"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa melihat pending approvals!")
        return

    pending_list = get_all_pending_approvals()

    if not pending_list:
        update.message.reply_text("✅ **Tidak ada konten yang menunggu approval.**")
        return

    text = "⏳ **DAFTAR PENDING APPROVAL**\n\n"

    for approval_id, media_type, sender_name, caption, created_at in pending_list:
        media_icon = "📸" if media_type == 'photo' else "🎬"
        caption_preview = caption[:50] + "..." if len(caption) > 50 else caption

        text += f"{media_icon} **ID:** `{approval_id}`\n"
        text += f"   👤 {sender_name}\n"
        text += f"   📝 {caption_preview}\n"
        text += f"   📅 {created_at[:16]}\n\n"

    pending, approved, rejected = get_approval_stats()
    text += f"📊 **Statistik:**\n"
    text += f"   ⏳ Pending: {pending}\n"
    text += f"   ✅ Approved: {approved}\n"
    text += f"   ❌ Rejected: {rejected}"

    update.message.reply_text(text, parse_mode="Markdown")


def hapus_postingan_command(update, context):
    """Hapus postingan dari channel berdasarkan ID approval - /hapus approval_id"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa menghapus postingan!")
        return

    if len(context.args) < 1:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/hapus approval_id\n\n"
            "Contoh: `/hapus 123`\n\n"
            "📌 Cari ID approval dari pesan notifikasi di grup approval.\n"
            "Gunakan /listpost untuk melihat daftar postingan.",
            parse_mode="Markdown"
        )
        return

    try:
        approval_id = int(context.args[0])

        posted = get_posted_content_by_approval(approval_id)

        if not posted:
            update.message.reply_text(
                f"❌ **Postingan dengan ID approval `{approval_id}` tidak ditemukan!**\n\n"
                f"Kemungkinan:\n"
                f"• ID approval salah\n"
                f"• Postingan sudah dihapus sebelumnya\n"
                f"• Postingan belum di-ACC",
                parse_mode="Markdown"
            )
            return

        (
            id, posted_approval_id, media_type, media_id,
            channel_message_id, channel_chat_id, link_code,
            sender_id, sender_name, posted_at, posted_by
        ) = posted

        if not channel_message_id:
            update.message.reply_text(
                f"⚠️ **Postingan tidak memiliki message_id!**\n\n"
                f"📌 ID Approval: `{approval_id}`\n"
                f"Tidak bisa dihapus secara otomatis.",
                parse_mode="Markdown"
            )
            return

        try:
            context.bot.delete_message(
                chat_id=channel_chat_id,
                message_id=channel_message_id
            )
        except Exception as e:
            update.message.reply_text(
                f"❌ **Gagal menghapus postingan dari channel!**\n\n"
                f"Error: {e}\n\n"
                f"Kemungkinan:\n"
                f"• Pesan sudah dihapus sebelumnya\n"
                f"• Bot tidak punya izin hapus\n"
                f"• Message ID tidak valid",
                parse_mode="Markdown"
            )
            return

        delete_posted_content(approval_id)

        try:
            c.execute('SELECT username FROM users WHERE user_id = ?', (sender_id,))
            user_result = c.fetchone()
            if user_result and user_result[0]:
                mention = f"@{user_result[0]}"
            else:
                mention = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

            context.bot.send_message(
                chat_id=sender_id,
                text=(
                    f"🗑️ **Konten Anda telah dihapus oleh admin!**\n\n"
                    f"📌 ID Approval: `{approval_id}`\n"
                    f"📂 Tipe: {'📸 Gambar' if media_type == 'photo' else '🎬 Video'}\n"
                    f"👤 Admin: {update.effective_user.first_name}\n\n"
                    f"📢 Notifikasi dikirim ke {mention}"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Gagal kirim notifikasi hapus: {e}", exc_info=True)

        update.message.reply_text(
            f"✅ **Postingan berhasil dihapus!**\n\n"
            f"📌 ID Approval: `{approval_id}`\n"
            f"📂 Tipe: {'📸 Gambar' if media_type == 'photo' else '🎬 Video'}\n"
            f"👤 Pengirim: {sender_name}\n"
            f"🔗 Link: {link_code}\n\n"
            f"📢 Notifikasi telah dikirim ke pengirim.",
            parse_mode="Markdown"
        )
    except ValueError:
        update.message.reply_text("❌ Approval ID harus berupa angka!")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


def list_post_command(update, context):
    """Lihat daftar postingan yang sudah di-ACC - /listpost"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Hanya admin yang bisa melihat daftar postingan!")
        return

    limit = 20
    if len(context.args) > 0:
        try:
            limit = int(context.args[0])
            if limit > 100:
                limit = 100
        except:
            pass

    posts = get_all_posted_content(limit)

    if not posts:
        update.message.reply_text(
            "📭 **Belum ada postingan yang di-ACC.**\n\n"
            "Postingan akan muncul setelah admin menyetujui konten.",
            parse_mode="Markdown"
        )
        return

    text = f"📋 **DAFTAR POSTINGAN**  ({len(posts)} terakhir)\n\n"

    for approval_id, media_type, sender_name, link_code, posted_at, channel_message_id in posts:
        media_icon = "📸" if media_type == 'photo' else "🎬"
        status = "✅ Aktif" if channel_message_id else "⚠️ Tanpa ID"

        text += f"{media_icon} **ID:** `{approval_id}`\n"
        text += f"   👤 {sender_name}\n"
        text += f"   🔗 `{link_code}`\n"
        text += f"   📅 {posted_at[:16]}\n"
        text += f"   📌 {status}\n\n"

    text += f"\n💡 Gunakan `/hapus approval_id` untuk menghapus postingan."

    update.message.reply_text(text, parse_mode="Markdown")
