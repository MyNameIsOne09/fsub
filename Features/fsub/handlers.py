from datetime import datetime
import html
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest
from core.database import conn, c
from core.logger import get_logger
from core.helpers import is_admin
from features.delivery.share import process_content_by_link
from features.fsub.queries import add_forced_channel, delete_channel_subtext, get_all_forced_channels, get_channel_subtext, remove_forced_channel, set_channel_subtext, set_channel_text_thumbnail
from features.fsub.service import check_joined_channel, send_join_channel_button

log = get_logger(__name__)


def handle_channel_forward(update, context):
    """Handler untuk mendeteksi channel/grup dari forward pesan"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("")
        return

    if update.message.forward_from_chat:
        chat = update.message.forward_from_chat
        chat_id = chat.id
        chat_username = chat.username if chat.username else f"private_{abs(chat_id)}"
        chat_title = chat.title
        chat_type = chat.type

        if chat_type in ['group', 'supergroup']:
            chat_type_display = "GRUP"
        else:
            chat_type_display = "CHANNEL"

        try:
            member = context.bot.get_chat_member(chat_id, context.bot.id)
            if member.status not in ['administrator', 'creator']:
                update.message.reply_text(
                    f"❌ Bot BUKAN admin di {chat_type_display} {chat_title}!\n\n"
                    f"Langkah-langkah:\n"
                    f"1. Invite bot ke {chat_type_display.lower()}\n"
                    f"2. Jadikan bot sebagai admin\n"
                    f"3. Forward ulang pesan"
                )
                return
        except BadRequest:
            update.message.reply_text(
                f"❌ Bot tidak bisa mengakses {chat_type_display} {chat_title}\n"
                f"Pastikan bot sudah:\n"
                f"• Diinvite ke {chat_type_display.lower()}\n"
                f"• Menjadi admin\n\n"
                f"Kemudian forward ulang pesan."
            )
            return

        c.execute('SELECT invite_link FROM forced_channels WHERE channel_id = ?', (chat_id,))
        result = c.fetchone()
        existing_invite = result[0] if result else None

        if existing_invite:
            add_forced_channel(chat_id, chat_username, chat_title, existing_invite)
            update.message.reply_text(
                f"✅ {chat_type_display} {chat_title} berhasil ditambahkan dengan invite link yang sudah ada!"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("TAMBAHKAN", callback_data=f"add_channel_{chat_id}_{chat_username}")],
                [InlineKeyboardButton("TAMBAH dan SET LINK", callback_data=f"add_channel_link_{chat_id}_{chat_username}")],
                [InlineKeyboardButton("BATAL", callback_data="cancel_add_channel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            chat_title_escaped = html.escape(chat_title)
            chat_type_display_escaped = html.escape(chat_type_display)

            text = (
                f"🔍 <b>{chat_type_display_escaped} Terdeteksi :</b>\n\n"
                f"📢 <b>Nama :</b> {chat_title_escaped}\n"
                f"🆔 <b>ID :</b> <code>{chat_id}</code>\n"
                f"🔒 <b>Tipe :</b> {chat_type_display_escaped}\n\n"
                f"⚠️ Yakin Anda ingin menambahkan {chat_type_display.lower()} ini?\n\n"
                f"• <b>TAMBAHKAN</b> : Untuk Channel Publik\n"
                f"• <b>TAMBAH + SET LINK</b> : Set invite link untuk Channel Private"
            )

            try:
                update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
            except Exception as e:
                log.error(f"HTML Error: {e}", exc_info=True)
                text_plain = (
                    f"🔍 {chat_type_display} Terdeteksi :\n\n"
                    f"📢 Nama : {chat_title}\n"
                    f"🆔 ID : {chat_id}\n"
                    f"🔒 Tipe : {chat_type_display}\n\n"
                    f"⚠️ Yakin Anda ingin menambahkan {chat_type_display.lower()} ini?\n\n"
                    f"• TAMBAHKAN : Untuk Channel Publik\n"
                    f"• TAMBAH + SET LINK : Set invite link untuk Channel Private"
                )
                update.message.reply_text(text_plain, reply_markup=reply_markup)
    else:
        update.message.reply_text(
            "Forward pesan dari channel/grup untuk menambahkan.\n\n"
            "📌 Catatan : Bot akan mendeteksi otomatis apakah itu channel atau grup."
        )


def add_channel_command(update, context):
    """Tambah channel/grup wajib join - /addchannel channel_id"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        text = (
            "<blockquote>"
            "<b>Cara penggunaan:</b>\n\n"
            "1. <b>Untuk CHANNEL/GROUP PUBLIC (punya username):</b>\n"
            "   /addchannel @username\n"
            "   Contoh: <code>/addchannel @channelku</code>\n\n"
            "2. <b>Untuk CHANNEL/GROUP PRIVATE (tanpa username):</b>\n"
            "   /addchannel channel_id\n"
            "   Contoh: <code>/addchannel -1001234567890</code>\n\n"
            "3. <b>Alternatif (paling mudah):</b>\n"
            "   • Jadikan bot sebagai admin di channel/grup\n"
            "   • <b>FORWARD</b> pesan dari channel/grup ke bot ini\n\n"
            "Pastikan bot sudah menjadi admin di channel/grup"
            "</blockquote>"
        )
        update.message.reply_text(text, parse_mode="HTML")
        return

    try:
        chat_input = context.args[0]

        if chat_input.startswith('@'):
            try:
                chat = context.bot.get_chat(chat_input)
                chat_id = chat.id
                channel_username = chat.username if chat.username else f"private_{abs(chat_id)}"
                channel_title = chat.title
                chat_type = chat.type
            except Exception as e:
                update.message.reply_text(f"❌ Gagal mendapatkan info chat: {e}")
                return
        else:
            chat_id = int(chat_input)

            try:
                chat = context.bot.get_chat(chat_id)
                channel_username = chat.username if chat.username else f"private_{abs(chat_id)}"
                channel_title = chat.title
                chat_type = chat.type
            except Exception as e:
                update.message.reply_text(
                    f"❌ Gagal mendapatkan info chat!\n\n"
                    f"Error: {e}\n\n"
                    f"Pastikan:\n"
                    f"• Bot sudah diinvite ke chat\n"
                    f"• Bot adalah admin di chat\n"
                    f"• ID chat benar"
                )
                return

        if chat_type in ['group', 'supergroup']:
            chat_type_display = "GRUP"
        elif chat_type == 'channel':
            chat_type_display = "CHANNEL"
        else:
            chat_type_display = "CHAT"

        try:
            member = context.bot.get_chat_member(chat_id, context.bot.id)
            if member.status not in ['administrator', 'creator']:
                update.message.reply_text(
                    f"❌ Bot BUKAN admin di {chat_type_display} {channel_title}!\n\n"
                    f"Untuk menambahkan, bot harus menjadi admin terlebih dahulu.\n\n"
                    f"Langkah-langkah:\n"
                    f"1. Invite bot ke {chat_type_display.lower()}\n"
                    f"2. Jadikan bot sebagai admin\n"
                    f"3. Ulangi perintah ini"
                )
                return
        except BadRequest:
            update.message.reply_text(
                f"❌ Bot tidak bisa mengakses {chat_type_display} {channel_title}\n"
                f"Pastikan bot sudah:\n"
                f"• Diinvite ke {chat_type_display.lower()}\n"
                f"• Menjadi admin"
            )
            return

        add_forced_channel(chat_id, channel_username, channel_title)

        channel_title_escaped = html.escape(str(channel_title))
        channel_username_escaped = html.escape(str(channel_username))
        chat_type_display_escaped = html.escape(str(chat_type_display))

        text = (
            f"✅ <b>{chat_type_display_escaped} BERHASIL DITAMBAHKAN</b>\n"
            f"◈ Nama: {channel_title_escaped}\n"
            f"◈ ID: <code>{chat_id}</code>\n"
            f"◈ Username: {channel_username_escaped if channel_username != f'private_{chat_id}' else '(private)'}\n"
            f"◈ Tipe: {chat_type_display_escaped}\n\n"
        )

        if not chat.username:
            text += (
                f"<b>Untuk {chat_type_display.lower()} PRIVATE:</b>\n"
                f"Gunakan perintah:\n"
                f"<code>/setinvite {chat_id} https://t.me/+invite_link</code>\n\n"
            )

        text += f"💠 <i>Created by</i> : @zenstoreni"

        try:
            update.message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            log.error(f"HTML Error: {e}", exc_info=True)
            text_plain = (
                f"✅ {chat_type_display} BERHASIL DITAMBAHKAN\n"
                f"◈ Nama: {channel_title}\n"
                f"◈ ID: {chat_id}\n"
                f"◈ Username: {channel_username if channel_username != f'private_{chat_id}' else '(private)'}\n"
                f"◈ Tipe: {chat_type_display}\n\n"
            )
            if not chat.username:
                text_plain += (
                    f"Untuk {chat_type_display.lower()} PRIVATE:\n"
                    f"Gunakan perintah:\n"
                    f"/setinvite {chat_id} https://t.me/+invite_link\n\n"
                )
            text_plain += f"💠 Created by : @zenstoreni"
            update.message.reply_text(text_plain)
    except ValueError:
        update.message.reply_text(
            "❌ Format ID salah!\n\n"
            "Gunakan:\n"
            "• <code>/addchannel @username</code> (untuk public)\n"
            "• <code>/addchannel -1001234567890</code> (untuk private)",
            parse_mode="HTML"
        )
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


def remove_channel_command(update, context):
    """Hapus channel wajib join - /rmchannel channel_id"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /rmchannel channel_id")
        return

    try:
        channel_id = int(context.args[0])
        remove_forced_channel(channel_id)
        update.message.reply_text(f"✅ Channel berhasil dihapus!")
    except ValueError:
        update.message.reply_text("❌ Channel ID harus berupa angka!")


def list_channels_command(update, context):
    """Lihat daftar channel wajib join"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    channels = get_all_forced_channels()

    if not channels:
        update.message.reply_text("📭 Belum ada channel wajib join.")
        return

    text = f"<blockquote>📢 <b>DAFTAR CHANNEL WAJIB JOIN</b>\n"
    text += "═" * 20 + "\n\n"

    for i, (ch_id, ch_username, ch_title, active) in enumerate(channels, 1):
        ch_title_escaped = html.escape(str(ch_title))

        status_icon = "√" if active == 1 else "×"

        if ch_username.startswith('private_'):
            display_username = "Private"
        else:
            display_username = f"@{ch_username.replace('@', '')}"

        text += f"{i}. <b>{ch_title_escaped}</b> {display_username}\n"
        text += f"    ID : <code>{ch_id}</code>  {status_icon}\n"

        try:
            c.execute('SELECT invite_link FROM forced_channels WHERE channel_id = ?', (ch_id,))
            result = c.fetchone()
            invite_link = result[0] if result else None
            if invite_link:
                text += f"    <a href='{invite_link}'>Join Channel</a>\n"
        except Exception as e:
            log.error(f"Error getting invite link: {e}", exc_info=True)

        text += "\n"

    text += "═" * 20 + "\n"
    text += f"💠 created by : @zenstoreni</blockquote>"

    try:
        update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        log.error(f"HTML Error: {e}", exc_info=True)
        text_plain = f"📢 DAFTAR CHANNEL WAJIB JOIN ({len(channels)} channel)\n"
        text_plain += "=" * 20 + "\n\n"

        for i, (ch_id, ch_username, ch_title, active) in enumerate(channels, 1):
            status_icon = "✅" if active == 1 else "❌"

            if ch_username.startswith('private_'):
                display_username = "Private"
            else:
                display_username = f"@{ch_username.replace('@', '')}"

            text_plain += f"{i}. {ch_title} {display_username}\n"
            text_plain += f"   🆔 ID : {ch_id}  {status_icon}\n"

            try:
                c.execute('SELECT invite_link FROM forced_channels WHERE channel_id = ?', (ch_id,))
                result = c.fetchone()
                invite_link = result[0] if result else None
                if invite_link:
                    text_plain += f"   🔗 Invite: {invite_link}\n"
            except:
                pass

            text_plain += "\n"

        text_plain += "=" * 20 + "\n"
        text_plain += f"💠 Total: {len(channels)} channel wajib join"

        update.message.reply_text(text_plain, disable_web_page_preview=True)


def set_text_thumb_command(update, context):
    """Set text thumbnail untuk channel - /settextthumb channel_id text"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 2:
        update.message.reply_text(
            "❌ /settextthumb channel_id text_anda\n\n"
            "Contoh: /settextthumb -1001234567890 Wajib join channel ini dulu ya!"
        )
        return

    try:
        channel_id = int(context.args[0])
        text = " ".join(context.args[1:])
        set_channel_text_thumbnail(channel_id, text)
        update.message.reply_text(f"✅ Text thumbnail untuk channel {channel_id} berhasil diset!")
    except ValueError:
        update.message.reply_text("❌ Channel ID harus berupa angka!")


def clean_duplicate_channels(update, context):
    """Bersihkan channel duplikat - /cleanchannels"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    c.execute('''
        DELETE FROM forced_channels
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM forced_channels
            GROUP BY channel_id
        )
    ''')
    conn.commit()

    deleted = c.rowcount
    update.message.reply_text(f"✅ Bersihkan selesai! {deleted} channel duplikat dihapus.")


def set_invite_link_command(update, context):
    """Set invite link untuk channel private - /setinvite channel_id invite_link"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 2:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/setinvite channel_id https://t.me/joinchat/xxxxx\n\n"
            "Contoh: /setinvite -1003951357620 https://t.me/joinchat/abc123def\n\n"
            "📌 **Cara dapatkan invite link:**\n"
            "1. Buka channel private\n"
            "2. Klik 'Invite Link' / 'Bagikan Link'\n"
            "3. Copy link dan paste di sini"
        )
        return

    try:
        channel_id = int(context.args[0])
        invite_link = context.args[1]

        if not invite_link.startswith(("https://t.me/joinchat/", "https://t.me/+", "http://")):
            update.message.reply_text("❌ Invite link tidak valid! Pastikan link dari Telegram.")
            return

        c.execute('UPDATE forced_channels SET invite_link = ? WHERE channel_id = ?', (invite_link, channel_id))
        conn.commit()

        c.execute('SELECT channel_title FROM forced_channels WHERE channel_id = ?', (channel_id,))
        result = c.fetchone()
        channel_title = result[0] if result else f"Channel {channel_id}"

        update.message.reply_text(
            f"✅ *Invite link untuk channel {channel_title} berhasil diset!*\n\n"
            f"🔗 Link: {invite_link}\n\n"
            f"📌 Tombol JOIN akan muncul untuk user yang belum join channel ini."
        )
    except ValueError:
        update.message.reply_text("❌ Channel ID harus berupa angka!")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


def set_text_sub_command(update, context):
    """Set text subscription untuk channel - /settextsub channel_id text"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 2:
        update.message.reply_text(
            "❌ **Cara penggunaan:**\n"
            "/settextsub channel_id text_anda\n\n"
            "Contoh: /settextsub -1001234567890 Jangan lupa share ke teman-teman!\n\n"
            "📌 Teks ini akan tampil di halaman paksa join.\n"
            "Gunakan /settextsub channel_id \"\" untuk menghapus."
        )
        return

    try:
        channel_id = int(context.args[0])
        text = " ".join(context.args[1:])

        c.execute('SELECT channel_title FROM forced_channels WHERE channel_id = ?', (channel_id,))
        result = c.fetchone()

        if not result:
            update.message.reply_text(f"❌ Channel dengan ID {channel_id} tidak ditemukan!\n\nGunakan /channels untuk melihat daftar channel.")
            return

        channel_title = result[0]

        if text.strip() == "":
            delete_channel_subtext(channel_id)
            update.message.reply_text(f"✅ Teks subscription untuk channel **{channel_title}** berhasil dihapus!", parse_mode="Markdown")
        else:
            set_channel_subtext(channel_id, text)
            update.message.reply_text(
                f"✅ **Teks subscription untuk channel {channel_title} berhasil diset!**\n\n"
                f"📝 Teks: {text}\n\n"
                f"📌 Teks akan tampil di halaman paksa join.\n"
                f"Gunakan /settextsub {channel_id} \"\" untuk menghapus.",
                parse_mode="Markdown"
            )
    except ValueError:
        update.message.reply_text("❌ Channel ID harus berupa angka!")


def get_text_sub_command(update, context):
    """Lihat text subscription untuk channel - /gettextsub channel_id"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if len(context.args) < 1:
        update.message.reply_text("❌ /gettextsub channel_id\n\nContoh: /gettextsub -1001234567890")
        return

    try:
        channel_id = int(context.args[0])

        c.execute('SELECT channel_title FROM forced_channels WHERE channel_id = ?', (channel_id,))
        result = c.fetchone()

        if not result:
            update.message.reply_text(f"❌ Channel dengan ID {channel_id} tidak ditemukan!")
            return

        channel_title = result[0]
        subtext = get_channel_subtext(channel_id)

        if subtext:
            update.message.reply_text(
                f"📢 **Channel:** {channel_title}\n"
                f"🆔 **ID:** `{channel_id}`\n\n"
                f"💬 **Subtext:**\n{subtext}",
                parse_mode="Markdown"
            )
        else:
            update.message.reply_text(
                f"📢 **Channel:** {channel_title}\n"
                f"🆔 **ID:** `{channel_id}`\n\n"
                f"💬 **Subtext:** (belum diset)\n\n"
                f"Gunakan /settextsub {channel_id} teks_anda untuk menambahkan.",
                parse_mode="Markdown"
            )
    except ValueError:
        update.message.reply_text("❌ Channel ID harus berupa angka!")


def handle_fsub_callback(update, context):
    """Callback cek keanggotaan dan penambahan channel wajib join"""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_all" or data.startswith("check_link_"):
        link_code = None
        if data.startswith("check_link_"):
            parts = data.split("_")
            link_code = parts[2] if len(parts) > 2 else None

        send_join_channel_button(query.message.chat_id, context.bot, link_code, query.from_user)

        try:
            query.delete_message()
        except:
            pass
        return

    if data == "check_single":
        if check_joined_channel(context.bot, user_id):
            query.edit_message_text("✅ BERHASIL! Anda sudah join channel!")
        else:
            send_join_channel_button(query.message.chat_id, context.bot, None, query.from_user)
            try:
                query.delete_message()
            except:
                pass
        return

    if data.startswith("add_channel_link_"):
        try:
            parts = data.split("_")
            channel_id = int(parts[3])
            channel_username = "_".join(parts[4:]) if len(parts) > 4 else f"private_{abs(channel_id)}"

            chat = context.bot.get_chat(channel_id)
            channel_title = chat.title

            c.execute('''
                INSERT OR REPLACE INTO forced_channels (channel_id, channel_username, channel_title, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel_id, channel_username, channel_title, 1, datetime.now().isoformat()))
            conn.commit()

            text = (
                f"✅ *Channel {channel_title} berhasil ditambahkan!*\n\n"
                f"📌 Sekarang set invite link untuk channel private :\n\n"
                f"*Gunakan perintah :*\n"
                f"`/setinvite {channel_id} https://t.me/+fvmpybAh1lRlYzBl`\n\n"
                f"Code by : @zentokk"
            )
            query.edit_message_text(text, parse_mode="Markdown")
        except Exception as e:
            query.edit_message_text(f"❌ Error: {e}")
        return

    if data.startswith("add_channel_") and not data.startswith("add_channel_link_"):
        try:
            parts = data.split("_")
            if len(parts) < 3:
                query.edit_message_text("❌ Data tidak valid!")
                return

            channel_id = int(parts[2])
            channel_username = "_".join(parts[3:]) if len(parts) > 3 else f"private_{abs(channel_id)}"

            chat = context.bot.get_chat(channel_id)
            channel_title = chat.title

            c.execute('SELECT channel_id FROM forced_channels WHERE channel_id = ?', (channel_id,))
            existing = c.fetchone()

            if existing:
                c.execute('''
                    UPDATE forced_channels
                    SET channel_username = ?, channel_title = ?, is_active = 1, updated_at = ?
                    WHERE channel_id = ?
                ''', (channel_username, channel_title, datetime.now().isoformat(), channel_id))
                conn.commit()
                status = "diperbarui"
            else:
                c.execute('''
                    INSERT OR REPLACE INTO forced_channels
                    (channel_id, channel_username, channel_title, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (channel_id, channel_username, channel_title, 1, datetime.now().isoformat()))
                conn.commit()
                status = "ditambahkan"

            channel_title_escaped = html.escape(str(channel_title))
            channel_username_display = chat.username if chat.username else '(private)'

            text = (
                f"✅ <b>Channel berhasil {status}!</b>\n\n"
                f"<b>Nama :</b> {channel_title_escaped}\n"
                f"<b>ID :</b> <code>{channel_id}</code>\n"
                f"<b>Username :</b> {channel_username_display}\n\n"
                f"💠 <i>Created by :</i> @zentokk"
            )

            try:
                query.edit_message_text(text, parse_mode="HTML")
            except Exception as e:
                log.error(f"HTML Error: {e}", exc_info=True)
                text_plain = (
                    f"✅ Channel berhasil {status}!\n\n"
                    f"Nama : {channel_title}\n"
                    f"ID : {channel_id}\n"
                    f"Username : {channel_username_display}\n\n"
                    f"Created by : @zentokk"
                )
                query.edit_message_text(text_plain)
        except ValueError as e:
            query.edit_message_text(f"❌ Error: ID channel tidak valid! {e}")
        except BadRequest as e:
            if "chat not found" in str(e).lower():
                query.edit_message_text(
                    f"❌ Channel tidak ditemukan!\n\n"
                    f"Pastikan:\n"
                    f"• Bot sudah diinvite ke channel\n"
                    f"• Bot adalah admin di channel\n"
                    f"• ID channel benar"
                )
            else:
                query.edit_message_text(f"❌ Error: {e}")
        except Exception as e:
            query.edit_message_text(f"❌ Error: {e}")
        return

    if data == "done_join":
        query.edit_message_text(
            "✅ **SELESAI!**\n\n"
            "Anda sudah join semua channel/grup.\n\n"
            "Silakan kirim ulang gambar/video Anda.",
            parse_mode="Markdown"
        )
        return

    if data.startswith("no_invite_"):
        channel_id = int(data.split("_")[2])

        c.execute('SELECT channel_title FROM forced_channels WHERE channel_id = ?', (channel_id,))
        result = c.fetchone()
        if result:
            channel_title = result[0]
            text = (
                f"🔒 *Channel PRIVATE: {channel_title}*\n\n"
                f"⚠️ *Invite link belum diset oleh admin!*\n\n"
                f"📌 *Channel ID:* `{channel_id}`\n\n"
                f"Hubungi admin untuk menambahkan invite link menggunakan :\n"
                f"`/setinvite {channel_id} https://t.me/joinchat/xxxxx`"
            )
            query.edit_message_text(text, parse_mode="Markdown")
        return

    if data == "cancel_add_channel":
        query.edit_message_text("❌ Penambahan channel dibatalkan.")
        return

    if data.startswith("private_channel_"):
        channel_id = int(data.split("_")[2])

        c.execute('SELECT channel_title, channel_username FROM forced_channels WHERE channel_id = ?', (channel_id,))
        result = c.fetchone()
        if result:
            channel_title, channel_username = result
            text = (
                f"🔒 *Channel PRIVATE: {channel_title}*\n\n"
                f"Channel ini adalah channel private.\n\n"
                f"*Cara join :*\n"
                f"1. Minta invite link ke admin channel\n"
                f"2. Klik link invite tersebut\n"
                f"3. Setelah join, klik tombol CEK KEHANGGOTAAN\n\n"
                f"📌 *Channel ID :* `{channel_id}`"
            )
            query.edit_message_text(text, parse_mode="Markdown")
        return

    if data.startswith("check_all_channels"):
        parts = data.split("_")
        link_code = parts[3] if len(parts) > 3 and parts[3] != "None" else None

        channels = get_all_forced_channels()

        if not channels:
            if check_joined_channel(context.bot, user_id):
                if link_code:
                    process_content_by_link(update, context, link_code, query)
                else:
                    query.edit_message_text("✅ BERHASIL!")
            else:
                send_join_channel_button(query.message.chat_id, context.bot, link_code, query.from_user)
            return

        joined_channels = []
        not_joined_channels = []

        for channel_id, channel_username, channel_title, is_active in channels:
            try:
                member = context.bot.get_chat_member(channel_id, user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    joined_channels.append(channel_username)
                else:
                    not_joined_channels.append(channel_username)
            except BadRequest:
                not_joined_channels.append(channel_username)

        if not_joined_channels:
            send_join_channel_button(query.message.chat_id, context.bot, link_code, query.from_user)
        else:
            query.edit_message_text("✅ BERHASIL! Anda sudah join semua channel!\n\nMengirim konten...")

            if link_code:
                process_content_by_link(update, context, link_code, query)
        return

    if data.startswith("check_join"):
        parts = data.split("_")
        link_code = parts[2] if len(parts) > 2 and parts[2] != "None" else None

        if check_joined_channel(context.bot, user_id):
            if link_code:
                process_content_by_link(update, context, link_code, query)
            else:
                query.edit_message_text("✅ BERHASIL!")
        else:
            send_join_channel_button(query.message.chat_id, context.bot, link_code, query.from_user)
        return
