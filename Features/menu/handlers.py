from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram import Update
from config import CHANNEL_ID
from core.database import c
from core.helpers import is_admin
from features.fsub.service import check_joined_channel, send_join_channel_button


def start_command(update, context):
    """Handler untuk /start - bedakan user dan admin dengan menu tombol"""
    user = update.effective_user
    user_id = user.id

    bot_username = context.bot.username

    c.execute('SELECT COUNT(*) FROM images')
    total_images = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM videos')
    total_videos = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]

    c.execute('SELECT SUM(views) FROM image_links')
    total_views = c.fetchone()[0] or 0

    c.execute('SELECT COUNT(*) FROM forced_channels')
    total_channels = c.fetchone()[0]

    if is_admin(user.id):
        keyboard = [
            [
            	InlineKeyboardButton("ᴛʜᴜᴍʙɴᴀɪʟ", callback_data="menu_thumbnail"),
            	InlineKeyboardButton("ғsᴜʙ", callback_data="menu_channel")
            ],
            [
            	InlineKeyboardButton("ʜᴀsʜᴛᴀɢs", callback_data="menu_hashtag"),
            	InlineKeyboardButton("ʙᴜᴛᴛᴏɴ", callback_data="menu_button")
            ],
            [
            	InlineKeyboardButton("ʟᴀɪɴɴʏᴀ", callback_data="menu_lainnya"),
            	InlineKeyboardButton("ᴛᴀɢs ɢᴀᴍʙᴀʀ", callback_data="menu_gambarhashtag")
            ],
            [
            	InlineKeyboardButton("ᴅᴀᴛᴀʙᴀsᴇ sᴇᴛ", callback_data="menu_approval"),
            	InlineKeyboardButton("ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="menu_broadcast")
            ],
            [
            	InlineKeyboardButton("sᴛᴏʀᴇ",	url="https://t.me/zenstoreni"),
            	InlineKeyboardButton("ᴏᴡɴᴇʀ",	url="https://t.me/zentokki")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"<blockquote><b>Welcome to the Admin Panel</b>\n"
            f"Statistik bot @{bot_username}\n"
            f"• Gambar : {total_images}\n"
            f"• Video : {total_videos}\n"
            f"• User : {total_users}\n"
            f"• Views : {total_views}\n"
            f"• Fsub : {total_channels} channel\n"
            f"═══════════════════════\n"
            f"Pilih menu di bawah :</blockquote>"
        )
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        if check_joined_channel(context.bot, user_id):
            keyboard = [
                [
                	InlineKeyboardButton("ʙᴀɴᴛᴜᴀɴ", callback_data="help_menu"),
                	InlineKeyboardButton("sᴛᴏʀᴇ", url="https://t.me/zenstoreni")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = (
                f"<blockquote>"
                f"🤖 <b>DANGER ZONE RATE PAP</b>\n\n"
                f"Silahkan kirim media berupa foto atau video yang ingin dipost ke channel.\n\n"
                f"❑ Watermark Sticker :\n"
                f"└ <a href='https://t.me/addstickers/dangerzonepap'>Save Watermark</a>\n\n"
                f"❑ Pilih hashtag berikut :\n"
                f"└ Girls / Boys"
                f"</blockquote>"
                f"<b>ᴄʀᴇᴀᴛᴇᴅ ʙʏ : @zentokki</b>"
            )
            update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            send_join_channel_button(update.message.chat_id, context.bot, None, user)


def handle_menu_callback(update, context):
    """Handler untuk tombol menu admin"""
    query = update.callback_query
    query.answer()
    data = query.data
    user_id = query.from_user.id

    bot_username = context.bot.username

    back_button = [[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_admin")]]
    back_markup = InlineKeyboardMarkup(back_button)

    if data == "menu_thumbnail":
        text = (
            "📸 <b>Thumbnail Channel</b>\n\n"
            "/setthumb - Set thumbnail (reply ke gambar)\n"
            "/getthumb - Lihat thumbnail saat ini"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_channel":
        text = (
            "📢 <b>Channel</b>\n\n"
            "/addchannel - Tambah channel\n"
            "/rmchannel - Hapus channel\n"
            "/channels - Lihat daftar channel\n"
            "/setinvite - Set invite link private\n"
            "/cleanch - Bersihkan duplikat"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_hashtag":
        text = (
            "🏷️ <b>Hashtag</b>\n\n"
            "/settags - Tambah hashtag\n"
            "/deltags - Hapus hashtag\n"
            "/listtags - Lihat daftar hashtag"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_button":
        text = (
            "🔘 <b>Custom Button</b>\n\n"
            "/addbutton - Tambah button\n"
            "/rmbuttons - Hapus semua button\n"
            "/listbuttons - Lihat daftar button"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_lainnya":
        text = (
            "📌 <b>Lainnya</b>\n\n"
            "/stats - Statistik lengkap\n"
            "/settextsub - Set teks subscription\n"
            "/gettextsub - Lihat teks subscription"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_gambarhashtag":
        text = (
            "🖼️ <b>Gambar Hashtag</b>\n\n"
            "/setimg - Set gambar untuk hashtag (reply ke gambar)\n"
            "/delimg - Hapus gambar hashtag\n"
            "/listimg - Lihat daftar gambar hashtag"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_approval":
        text = (
            "📋 <b>Approval</b>\n\n"
            "/pending - Lihat pending approval\n"
            "/setgrup - Set grup approval\n"
            "/listgrup - Lihat daftar grup approval\n"
            "/delgrup - Hapus grup approval"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_broadcast":
        text = (
            "📨 <b>Broadcast</b>\n\n"
            "/bc - Broadcast teks (reply ke pesan)\n"
            "/bcfoto - Broadcast foto (reply ke foto)\n"
            "/bcvideo - Broadcast video (reply ke video)"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "menu_whitelist":
        text = (
            "👤 <b>Whitelist</b>\n\n"
            "/free - Tambah user ke whitelist\n"
            "/delfree - Hapus user dari whitelist\n"
            "/freelist - Lihat daftar whitelist"
        )
        query.edit_message_text(text, reply_markup=back_markup, parse_mode="HTML")
    elif data == "back_to_admin":
        keyboard = [
            [
            	InlineKeyboardButton("ᴛʜᴜᴍʙɴᴀɪʟ", callback_data="menu_thumbnail"),
            	InlineKeyboardButton("ғsᴜʙ", callback_data="menu_channel")
            ],
            [
            	InlineKeyboardButton("Hashtag", callback_data="menu_hashtag"),
            	InlineKeyboardButton("ʙᴜᴛᴛᴏɴ", callback_data="menu_button")
            ],
            [
            	InlineKeyboardButton("ʟᴀɪɴɴʏᴀ", callback_data="menu_lainnya"),
            	InlineKeyboardButton("ᴛᴀɢs ɢᴀᴍʙᴀʀ", callback_data="menu_gambarhashtag")
            ],
            [
            	InlineKeyboardButton("ᴅᴀᴛᴀʙᴀsᴇ sᴇᴛ", callback_data="menu_approval"),
            	InlineKeyboardButton("ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="menu_broadcast")
            ],
            [
            	InlineKeyboardButton("sᴛᴏʀᴇ",	url="https://t.me/zenstoreni"),
            	InlineKeyboardButton("ᴏᴡɴᴇʀ",	url="https://t.me/zentokki")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        c.execute('SELECT COUNT(*) FROM images')
        total_images = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM videos')
        total_videos = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        c.execute('SELECT SUM(views) FROM image_links')
        total_views = c.fetchone()[0] or 0
        c.execute('SELECT COUNT(*) FROM forced_channels')
        total_channels = c.fetchone()[0]

        text = (
            f"<blockquote><b>Welcome to the Admin Panel</b>\n"
            f"Statistik bot @{bot_username}\n"
            f"• Gambar : {total_images}\n"
            f"• Video : {total_videos}\n"
            f"• User : {total_users}\n"
            f"• Views : {total_views}\n"
            f"• Fsub : {total_channels} channel\n"
            f"═══════════════════════\n"
            f"Pilih menu di bawah :</blockquote>"
        )
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")


def handle_user_menu_callback(update, context):
    """Menu bantuan untuk user"""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "help_menu":
        keyboard = [
            [InlineKeyboardButton("ᴋᴇᴍʙᴀʟɪ", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            "<blockquote>📖 <b>BANTUAN UNTUK SENDER</b>\n\n"
            "<b>Panduan Upload</b>\n"
            "1. Siapkan foto atau video dengan <a href='https://t.me/addstickers/dangerzonepap'>Watermark</a> \n"
            "2. Kasih caption pada photo atau video\n"
            "3. Pilih Hashtag sesuai gender kalian\n"
            "4. Tunggu verifikasi dari admin\n\n"
            "<b>Notes :</b>\n"
            "Bagi kalian para feker dilarang ngirim</blockquote>"
        )
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        return

    if data == "back_to_menu":
        keyboard = [
            [
            	InlineKeyboardButton("ʙᴀɴᴛᴜᴀɴ", callback_data="help_menu"),
            	InlineKeyboardButton("sᴛᴏʀᴇ", url="https://t.me/zenstoreni")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"<blockquote>"
            f"🤖 <b>DANGER ZONE RATE PAP</b>\n\n"
            f"Silakan kirim media berupa foto atau video yang ingin dipost ke channel.\n\n"
            f"❑ Watermark Sticker:\n"
            f"└ <a href='https://t.me/addstickers/dangerzonepap'>Save Watermark</a>\n\n"
            f"❑ Gunakan hashtag berikut:\n"
            f"└ Girls / Boys"
            f"</blockquote>"
            f"<b>ᴄʀᴇᴀᴛᴇᴅ ʙʏ : @zentokki</b>"
        )
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        return


def admin_stats(update, context):
    """Handler untuk /stats (hanya admin)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ **Anda bukan admin!**", parse_mode="Markdown")
        return

    c.execute('SELECT COUNT(*) FROM images')
    total_images = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM image_links')
    total_links = c.fetchone()[0]

    c.execute('SELECT SUM(views) FROM image_links')
    total_views = c.fetchone()[0] or 0

    c.execute('SELECT COUNT(*) FROM users WHERE joined_channel = 1')
    total_members = c.fetchone()[0]

    text = "📊 *STATISTIK BOT*\n\n"
    text += f"🖼️ *Total Gambar :* {total_images}\n"
    text += f"🔗 *Total Link :* {total_links}\n"
    text += f"👁️ *Total View :* {total_views}\n"
    text += f"👥 *Member Channel :* {total_members}\n"

    update.message.reply_text(text, parse_mode="Markdown")


def getphoto_command(update: Update, context):
    """Handler untuk mendapatkan photo ID - /getphoto (reply ke foto)"""
    user = update.effective_user

    if not is_admin(user.id):
        update.message.reply_text("❌ Hanya owner!", parse_mode=ParseMode.MARKDOWN)
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        update.message.reply_text(
            "📸 *Cara pakai:*\n1. Kirim foto\n2. Reply foto dengan `/getphoto`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    photo = update.message.reply_to_message.photo[-1]
    file_id = photo.file_id

    update.message.reply_text(
        f"*Photo ID:*\n`{file_id}`",
        parse_mode=ParseMode.MARKDOWN
    )


def send_bot_intro_with_photo(update: Update, context):
    """Kirim pengenalan bot ke channel dengan foto + inline keyboard"""

    CHANNEL_ID = "@zenstoreni"
    PHOTO_ID = "AgACAgEAAxkBAAN_aifBfc4E5CyClLEVKTA8p2huS8UAAoQMaxvF2QlFTBLWiWwXnGUBAAMCAAN5AAM7BA"

    caption = ("""<blockquote>
🤖 <i>FEATURED BOT FSUB</i>
━━━━━━━━━━━━━━━━━━━━━━
╔ Add button/tombol sendiri (maks 10)
╠ AutoPost ke Channel
╠ #Hastags untuk mempermudah pencarian
╠ Gambar/Video tidak bisa di simpan
╠ Custom text (Force Subscribe)
╠ Cocok untuk asupan/handle pap
╠ Set thumbnail channel
╚ Support group dan channel
━━━━━━━━━━━━━━━━━━━━━━
</blockquote>"""
    )

    keyboard = InlineKeyboardMarkup([
        [
        	InlineKeyboardButton("🤖 ʙᴏᴛ", url="https://t.me/zenfsubbbot"),
          InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url="https://t.me/zentokki")
        ]
     ])

    try:
        context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=PHOTO_ID,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        if update:
            update.message.reply_text("✅ *Pesan berhasil dikirim ke channel!*", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        if update:
            update.message.reply_text(f"❌ Gagal kirim: {e}", parse_mode=ParseMode.MarkDown)
