from core.database import conn, c
from core.helpers import is_admin


def bcphoto(update, context):
    """Broadcast foto - reply ke foto dengan caption (support multi-line)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        update.message.reply_text(
            "📸 Cara Broadcast Foto:\n\n"
            "1. Kirim foto dengan caption (bisa multi-line/enter)\n"
            "2. Reply foto tersebut dengan /bcfoto\n\n"
            "Contoh caption:\n"
            "uwihh\n"
            "mantep nihh"
        )
        return

    photo = update.message.reply_to_message.photo[-1]

    caption = update.message.reply_to_message.caption or ""

    if not caption:
        caption = " ".join(context.args) if context.args else "Broadcast Foto"

    broadcast_text = f"""<blockquote>
{caption}
━━━━━━━━━━━━━━━━━━━━━━
<i>Created by : @zenstoreni</i></blockquote>"""

    msg = update.message.reply_text("⏳ Wait lagi dikirim...")

    c.execute('SELECT user_id FROM users')
    users = c.fetchall()

    if not users:
        msg.edit_text("❌ Tidak ada user!")
        return

    sukses = 0
    gagal = 0
    block = 0

    for row in users:
        uid = row[0]
        try:
            context.bot.send_photo(
                chat_id=uid,
                photo=photo.file_id,
                caption=broadcast_text,
                parse_mode="HTML",
                timeout=60
            )
            sukses += 1
        except:
            try:
                context.bot.send_photo(
                    chat_id=uid,
                    photo=photo.file_id,
                    caption=f"{caption}\nCreated by : @zentokki"
                )
                sukses += 1
            except Exception as e:
                if "blocked" in str(e).lower():
                    block += 1
                    c.execute('DELETE FROM users WHERE user_id = ?', (uid,))
                    conn.commit()
                else:
                    gagal += 1

    msg.delete()
    update.message.reply_text(
        f"""<blockquote>
<b>◈ Broadcast Telah Selesai</b>
┌ Berhasil : {sukses}
├ Gagal Kirim : {gagal}
├ User Blok Bot : {block} (dihapus)
└ Jumlah User : {len(users)}
</blockquote>""",
        parse_mode="HTML"
    )


def bcvideo(update, context):
    """Broadcast video - reply ke video dengan caption (support multi-line)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        update.message.reply_text(
            "🎬 Cara Broadcast Video:\n\n"
            "1. Kirim video dengan caption (bisa multi-line/enter)\n"
            "2. Reply video tersebut dengan /bcvideo\n\n"
            "Contoh caption:\n"
            "uwihh\n"
            "mantep nihh"
        )
        return

    video = update.message.reply_to_message.video

    caption = update.message.reply_to_message.caption or ""

    if not caption:
        caption = " ".join(context.args) if context.args else "Broadcast Video"

    broadcast_text = f"""<blockquote>
{caption}
━━━━━━━━━━━━━━━━━━━━━━
<i>Created by : @zenstoreni</i></blockquote>"""

    msg = update.message.reply_text("⏳ Wait lagi dikirim...")

    c.execute('SELECT user_id FROM users')
    users = c.fetchall()

    if not users:
        msg.edit_text("❌ Tidak ada user!")
        return

    sukses = 0
    gagal = 0
    block = 0

    for row in users:
        uid = row[0]
        try:
            context.bot.send_video(
                chat_id=uid,
                video=video.file_id,
                caption=broadcast_text,
                parse_mode="HTML",
                timeout=120
            )
            sukses += 1
        except:
            try:
                context.bot.send_video(
                    chat_id=uid,
                    video=video.file_id,
                    caption=f"{caption}\nCreated by : @zentokki"
                )
                sukses += 1
            except Exception as e:
                if "blocked" in str(e).lower():
                    block += 1
                    c.execute('DELETE FROM users WHERE user_id = ?', (uid,))
                    conn.commit()
                else:
                    gagal += 1

    msg.delete()
    update.message.reply_text(
        f"""<blockquote>
<b>◈ Broadcast Telah Selesai</b>
┌ Berhasil : {sukses}
├ Gagal Kirim : {gagal}
├ User Blok Bot : {block} (dihapus)
└ Jumlah User : {len(users)}
</blockquote>""",
        parse_mode="HTML"
    )


def bc(update, context):
    """Broadcast teks - reply ke pesan (support multi-line)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text("❌ Bukan admin!")
        return

    if update.message.reply_to_message:
        pesan = update.message.reply_to_message.text or ""
    else:
        if len(context.args) < 1:
            update.message.reply_text(
                "📢 **Cara Broadcast:**\n\n"
                "1. Ketik pesan multi-line, lalu reply dengan /bc\n"
                "2. Atau langsung: /bc pesan_anda"
            )
            return
        pesan = " ".join(context.args)

    if not pesan:
        update.message.reply_text("❌ Pesan kosong!")
        return

    broadcast_text = f"""<blockquote>
{pesan}
━━━━━━━━━━━━━━━━━━━━━━
<i>Created by : @zenstoreni</i></blockquote>"""

    msg = update.message.reply_text("⏳ Wait lagi dikirim...")

    c.execute('SELECT user_id FROM users')
    users = c.fetchall()

    if not users:
        msg.edit_text("❌ Tidak ada user!")
        return

    sukses = 0
    gagal = 0
    block = 0

    for row in users:
        uid = row[0]
        try:
            context.bot.send_message(
                chat_id=uid,
                text=broadcast_text,
                parse_mode="HTML",
                timeout=30
            )
            sukses += 1
        except:
            try:
                context.bot.send_message(
                    chat_id=uid,
                    text=f"{pesan}\nCreated by : @zentokki"
                )
                sukses += 1
            except Exception as e:
                if "blocked" in str(e).lower():
                    block += 1
                    c.execute('DELETE FROM users WHERE user_id = ?', (uid,))
                    conn.commit()
                else:
                    gagal += 1

    msg.delete()
    update.message.reply_text(
        f"""<blockquote>
<b>◈ Broadcast Telah Selesai</b>
┌ Berhasil : {sukses}
├ Gagal Kirim : {gagal}
├ User Blok Bot : {block} (dihapus)
└ Jumlah User : {len(users)}
</blockquote>""",
        parse_mode="HTML"
    )
