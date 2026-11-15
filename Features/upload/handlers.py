from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from core.helpers import download_file
from features.approval.notify import send_approval_notification
from features.approval.queries import save_pending_approval
from features.fsub.service import check_joined_channel, send_join_channel_button
from features.hashtag.queries import get_available_hashtags


def handle_photo(update, context):
    """Menerima gambar dari user - cek FSUB dulu, pilih hashtag, lalu masuk pending approval"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or ""
    full_name = f"{first_name} {user.last_name or ''}".strip()

    if not check_joined_channel(context.bot, user_id):
        send_join_channel_button(update.message.chat_id, context.bot, None, user)
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    caption = update.message.caption or ""

    processing_msg = update.message.reply_text("⏳ Memproses gambar...")

    file_data = download_file(context.bot, file_id)

    if file_data:
        processing_msg.delete()

        if not hasattr(handle_photo, "temp_data"):
            handle_photo.temp_data = {}

        handle_photo.temp_data[user_id] = {
            'file_id': file_id,
            'file_data': file_data,
            'caption': caption,
            'full_name': full_name,
            'username': username,
            'type': 'photo'
        }

        send_hashtag_selection(update, context, file_id, "photo", file_data)
    else:
        processing_msg.edit_text("❌ Gagal memproses gambar! Silakan coba lagi.")


def handle_video(update, context):
    """Menerima video dari user - cek FSUB dulu, pilih hashtag, lalu masuk pending approval"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or ""
    full_name = f"{first_name} {user.last_name or ''}".strip()

    if not check_joined_channel(context.bot, user_id):
        send_join_channel_button(update.message.chat_id, context.bot, None, user)
        return

    video = update.message.video
    file_id = video.file_id
    caption = update.message.caption or ""
    duration = video.duration
    width = video.width
    height = video.height
    file_size = video.file_size

    processing_msg = update.message.reply_text("⏳ Memproses video...")

    processing_msg.delete()

    if not hasattr(handle_video, "temp_data"):
        handle_video.temp_data = {}

    handle_video.temp_data[user_id] = {
        'file_id': file_id,
        'caption': caption,
        'full_name': full_name,
        'username': username,
        'duration': duration,
        'width': width,
        'height': height,
        'file_size': file_size,
        'type': 'video'
    }

    send_hashtag_selection(update, context, file_id, "video", None)


def handle_gif(update, context):
    """Menerima GIF (animation) dari user - cek FSUB dulu, pilih hashtag, lalu masuk pending approval"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or ""
    full_name = f"{first_name} {user.last_name or ''}".strip()

    if not check_joined_channel(context.bot, user_id):
        send_join_channel_button(update.message.chat_id, context.bot, None, user)
        return

    gif = update.message.animation
    file_id = gif.file_id
    caption = update.message.caption or ""
    duration = gif.duration
    width = gif.width
    height = gif.height
    file_size = gif.file_size

    if not hasattr(handle_gif, "temp_data"):
        handle_gif.temp_data = {}

    handle_gif.temp_data[user_id] = {
        'file_id': file_id,
        'caption': caption,
        'full_name': full_name,
        'username': username,
        'duration': duration,
        'width': width,
        'height': height,
        'file_size': file_size,
        'type': 'gif'
    }

    send_hashtag_selection(update, context, file_id, "gif", None)


def process_to_approval(update, context, selected_tags, file_id, file_type, file_data=None):
    """Proses konten setelah hashtag dipilih - LANGSUNG KE PENDING APPROVAL"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or ""
    full_name = f"{first_name} {user.last_name or ''}".strip()

    temp_caption = ""
    temp_duration = 0
    temp_width = 0
    temp_height = 0
    temp_file_size = 0
    temp_file_id = file_id
    temp_file_data = file_data

    if file_type == "photo" and hasattr(handle_photo, "temp_data") and user_id in handle_photo.temp_data:
        temp_caption = handle_photo.temp_data[user_id].get('caption', '')
        temp_file_data = handle_photo.temp_data[user_id].get('file_data', file_data)
        temp_file_id = handle_photo.temp_data[user_id].get('file_id', file_id)
        full_name = handle_photo.temp_data[user_id].get('full_name', full_name)
        username = handle_photo.temp_data[user_id].get('username', username)
    elif file_type == "gif" and hasattr(handle_gif, "temp_data") and user_id in handle_gif.temp_data:
        temp_caption = handle_gif.temp_data[user_id].get('caption', '')
        temp_duration = handle_gif.temp_data[user_id].get('duration', 0)
        temp_width = handle_gif.temp_data[user_id].get('width', 0)
        temp_height = handle_gif.temp_data[user_id].get('height', 0)
        temp_file_size = handle_gif.temp_data[user_id].get('file_size', 0)
        temp_file_id = handle_gif.temp_data[user_id].get('file_id', file_id)
        full_name = handle_gif.temp_data[user_id].get('full_name', full_name)
        username = handle_gif.temp_data[user_id].get('username', username)
    elif file_type == "video" and hasattr(handle_video, "temp_data") and user_id in handle_video.temp_data:
        temp_caption = handle_video.temp_data[user_id].get('caption', '')
        temp_duration = handle_video.temp_data[user_id].get('duration', 0)
        temp_width = handle_video.temp_data[user_id].get('width', 0)
        temp_height = handle_video.temp_data[user_id].get('height', 0)
        temp_file_size = handle_video.temp_data[user_id].get('file_size', 0)
        temp_file_id = handle_video.temp_data[user_id].get('file_id', file_id)
        full_name = handle_video.temp_data[user_id].get('full_name', full_name)
        username = handle_video.temp_data[user_id].get('username', username)

    hashtag_text = " ".join(selected_tags) if selected_tags else ""

    final_caption = temp_caption
    if hashtag_text:
        if final_caption:
            final_caption += f"\n\n{hashtag_text}"
        else:
            final_caption = hashtag_text

    pending_data = {
        'media_type': file_type,
        'file_id': temp_file_id,
        'file_data': temp_file_data,
        'sender_id': user_id,
        'sender_name': full_name,
        'username': username,
        'caption': final_caption,
        'file_size': len(temp_file_data) if file_type == "photo" else temp_file_size,
        'duration': temp_duration,
        'width': temp_width,
        'height': temp_height,
        'hashtags': hashtag_text
    }

    approval_id = save_pending_approval(pending_data)

    text_notif = (
        f"<blockquote>Gambar berhasil dikirim\n"
        f"Tunggu konfirmasi dari admin</blockquote>"
    )

    if update.callback_query:
        update.callback_query.message.reply_text(text_notif, parse_mode="HTML")
    else:
        update.message.reply_text(text_notif, parse_mode="HTML")

    send_approval_notification(context.bot, approval_id, pending_data)

    if file_type == "photo" and hasattr(handle_photo, "temp_data") and user_id in handle_photo.temp_data:
        del handle_photo.temp_data[user_id]
    elif file_type == "video" and hasattr(handle_video, "temp_data") and user_id in handle_video.temp_data:
        del handle_video.temp_data[user_id]
    elif file_type == "gif" and hasattr(handle_gif, "temp_data") and user_id in handle_gif.temp_data:
        del handle_gif.temp_data[user_id]


def send_hashtag_selection(update, context, file_id, file_type, file_data=None):
    """Kirim tombol pilihan hashtag - dengan tombol CANCEL"""
    hashtags = get_available_hashtags()

    if not hashtags:
        process_to_approval(update, context, [], file_id, file_type, file_data)
        return

    keyboard = []
    row = []
    for i, tag in enumerate(hashtags):
        callback = f"h_{i}_{file_type}"
        row.append(InlineKeyboardButton(tag, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("SELESAI", callback_data=f"done_{file_type}"),
        InlineKeyboardButton("BATAL", callback_data=f"cancel_{file_type}")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "<blockquote><b>PILIH HASHTAG SESUAI GENDER</b>\n\n"
    text += "Harus sesuai dengan gender jika tidak akan di tolak</blockquote>\n"

    update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


def handle_hashtag_callback(update, context):
    """Callback pemilihan hashtag saat upload"""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("h_"):
        parts = data.split("_")
        if len(parts) >= 2:
            try:
                tag_index = int(parts[1])
                file_type = parts[2] if len(parts) > 2 else "photo"
            except ValueError:
                return

            hashtags = get_available_hashtags()
            if tag_index >= len(hashtags):
                return

            full_tag = hashtags[tag_index]

            if not hasattr(handle_hashtag_callback, "user_hashtags"):
                handle_hashtag_callback.user_hashtags = {}

            if user_id not in handle_hashtag_callback.user_hashtags:
                handle_hashtag_callback.user_hashtags[user_id] = []

            if full_tag in handle_hashtag_callback.user_hashtags[user_id]:
                handle_hashtag_callback.user_hashtags[user_id].remove(full_tag)
            else:
                handle_hashtag_callback.user_hashtags[user_id].append(full_tag)

            current = " ".join(handle_hashtag_callback.user_hashtags[user_id])

            keyboard = []
            row = []
            for i, ht in enumerate(hashtags):
                if ht in handle_hashtag_callback.user_hashtags[user_id]:
                    button_text = f"✅ {ht}"
                else:
                    button_text = ht
                row.append(InlineKeyboardButton(button_text, callback_data=f"h_{i}_{file_type}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

            keyboard.append([
                InlineKeyboardButton("✅ SELESAI", callback_data=f"done_{file_type}"),
                InlineKeyboardButton("❌ BATAL", callback_data=f"cancel_{file_type}")
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            text = f"🏷 *Hashtag Saat Ini*\n"
            text += f"{current if current else '(belum ada)'}\n\n"
            text += "Klik hashtag untuk menambah/menghapus, lalu klik SELESAI atau BATAL."

            query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            return

    if data.startswith("done_"):
        file_type = data.split("_")[1] if len(data.split("_")) > 1 else "photo"

        selected = handle_hashtag_callback.user_hashtags.get(user_id, []) if hasattr(handle_hashtag_callback, "user_hashtags") else []

        if not selected:
          query.edit_message_text(
						"<blockquote><b>Gagal Kirim Gambar , Minimal pilih 1 gender</b></blockquote>",
						reply_markup=query.message.reply_markup,
						parse_mode="HTML"
					)
          return

        file_id = None
        file_data = None

        if file_type == "photo" and hasattr(handle_photo, "temp_data") and user_id in handle_photo.temp_data:
            file_id = handle_photo.temp_data[user_id].get('file_id')
            file_data = handle_photo.temp_data[user_id].get('file_data')
        elif file_type == "video" and hasattr(handle_video, "temp_data") and user_id in handle_video.temp_data:
            file_id = handle_video.temp_data[user_id].get('file_id')
        elif file_type == "gif" and hasattr(handle_gif, "temp_data") and user_id in handle_gif.temp_data:
            file_id = handle_gif.temp_data[user_id].get('file_id')

        if file_id:
            process_to_approval(update, context, selected, file_id, file_type, file_data if file_type == "photo" else None)

        if hasattr(handle_hashtag_callback, "user_hashtags") and user_id in handle_hashtag_callback.user_hashtags:
            del handle_hashtag_callback.user_hashtags[user_id]
        if file_type == "photo" and hasattr(handle_photo, "temp_data") and user_id in handle_photo.temp_data:
            del handle_photo.temp_data[user_id]
        elif file_type == "video" and hasattr(handle_video, "temp_data") and user_id in handle_video.temp_data:
            del handle_video.temp_data[user_id]

        query.edit_message_text("<blockquote>Proses Selesai</blockquote>", parse_mode="HTML")
        return

    if data.startswith("cancel_"):
        file_type = data.split("_")[1] if len(data.split("_")) > 1 else "photo"

        if hasattr(handle_hashtag_callback, "user_hashtags") and user_id in handle_hashtag_callback.user_hashtags:
            del handle_hashtag_callback.user_hashtags[user_id]
        if file_type == "photo" and hasattr(handle_photo, "temp_data") and user_id in handle_photo.temp_data:
            del handle_photo.temp_data[user_id]
        elif file_type == "video" and hasattr(handle_video, "temp_data") and user_id in handle_video.temp_data:
            del handle_video.temp_data[user_id]
        elif file_type == "gif" and hasattr(handle_gif, "temp_data") and user_id in handle_gif.temp_data:
            del handle_gif.temp_data[user_id]

        query.edit_message_text(
            "❌ **Pengiriman dibatalkan!**\n\n"
            "Anda dapat mengirim ulang gambar/video kapan saja.",
            parse_mode="Markdown"
        )
        return
