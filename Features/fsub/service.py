from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.error import BadRequest
from config import CHANNEL_USERNAME
from core.database import c
from features.fsub.queries import get_all_forced_channels, get_channel_subtext


def check_user_joined_all_channels(bot, user_id):
    """Cek apakah user sudah join SEMUA channel/grup wajib"""
    channels = get_all_forced_channels()
    if not channels:
        return True, None, None

    for chat_id, chat_username, chat_title, is_active in channels:
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False, chat_id, chat_username
        except BadRequest:
            return False, chat_id, chat_username
    return True, None, None


def check_joined_channel(bot, user_id):
    """Cek apakah user sudah join SEMUA channel (legacy compatibility)"""
    is_joined, failed_channel_id, failed_username = check_user_joined_all_channels(bot, user_id)
    return is_joined


def send_join_channel_button(chat_id, bot, link_code=None, user=None):
    """Kirim tombol untuk join channel/grup - HANYA yang BELUM dijoin"""

    all_chats = get_all_forced_channels()
    total_chats = len(all_chats)

    user_mention = ""
    user_id = None
    if user:
        user_id = user.id
        first_name = user.first_name or "Pengguna"
        safe_first_name = first_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        user_mention = f'<a href="tg://user?id={user_id}">{safe_first_name}</a>'
    else:
        user_mention = "Pengguna"

    not_joined_chats = []
    joined_chats = []

    if user_id:
        for ch_id, ch_username, ch_title, is_active in all_chats:
            try:
                member = bot.get_chat_member(ch_id, user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    joined_chats.append((ch_id, ch_username, ch_title, is_active))
                else:
                    not_joined_chats.append((ch_id, ch_username, ch_title, is_active))
            except BadRequest:
                not_joined_chats.append((ch_id, ch_username, ch_title, is_active))
    else:
        not_joined_chats = all_chats

    global_subtext = ""
    for ch_id, ch_username, ch_title, is_active in not_joined_chats:
        subtext = get_channel_subtext(ch_id)
        if subtext:
            global_subtext = subtext
            break

    if global_subtext:
        safe_subtext = global_subtext.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        main_text = safe_subtext
    else:
        main_text = "Anda harus bergabung di Channel/Grup saya Terlebih dahulu untuk Melihat File yang saya Bagikan"

    if not not_joined_chats and total_chats > 0:
        keyboard = [[InlineKeyboardButton("👍 SELESAI", callback_data="done_join")]]
        text = (
            f"<blockquote>"
            f"👋 Hallo {user_mention}\n\n"
            f"<b>✅ ANDA SUDAH JOIN SEMUA CHANNEL/GRUP!</b>\n\n"
            f"<i>Created by : @zentokk</i>"
            f"</blockquote>"
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return

    if total_chats == 0:
        keyboard = [
            [InlineKeyboardButton("📣 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 ᴄᴏʙᴀ ʟᴀɢɪ", callback_data="check_single")]
        ]
        text = (
            f"<blockquote>"
            f"👋 Hello {user_mention}\n\n"
            f"<b>{main_text}</b>\n\n"
            f"📢 Join Channel: {CHANNEL_USERNAME}\n\n"
            f"</blockquote>"
        )
    else:
        keyboard = []
        all_join_buttons = []

        for ch_id, ch_username, ch_title, is_active in not_joined_chats:
            c.execute('SELECT invite_link FROM forced_channels WHERE channel_id = ?', (ch_id,))
            result = c.fetchone()
            invite_link = result[0] if result else None

            try:
                chat_obj = bot.get_chat(ch_id)
                chat_type = chat_obj.type
            except:
                chat_type = "channel"

            if chat_type in ['group', 'supergroup']:
                chat_type_display = "ᴊᴏɪɴ ɢʀᴏᴜᴘ"
                button_icon = "📣"
            else:
                chat_type_display = "ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ"
                button_icon = "📣"

            safe_ch_title = str(ch_title).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            if ch_username.startswith('private_') or not ch_username:
                if invite_link:
                    all_join_buttons.append(InlineKeyboardButton(f"{button_icon} {chat_type_display}", url=invite_link))
                else:
                    all_join_buttons.append(InlineKeyboardButton(f"❌ {safe_ch_title}", callback_data=f"no_invite_{ch_id}"))
            else:
                clean_username = ch_username.replace('@', '')
                all_join_buttons.append(InlineKeyboardButton(f"{button_icon} {chat_type_display}", url=f"https://t.me/{clean_username}"))

        row = []
        for button in all_join_buttons:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        if link_code:
            callback_data = f"check_link_{link_code}"
        else:
            callback_data = "check_all"

        keyboard.append([InlineKeyboardButton("🔄 ᴄᴏʙᴀ ʟᴀɢɪ", callback_data=callback_data)])

        text = (
            f"<blockquote>"
            f"👋 Hallo {user_mention}\n\n"
            f"<b>{main_text}</b>\n\n"
            f"<i>Sisa : ({len(not_joined_chats)}/{total_chats})</i>\n"
            f"<i>Dibuat oleh :</i> <a href='https://t.me/zentokki'>Mas Zen</a>"
            f"</blockquote>"
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
