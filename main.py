import core.compat  # noqa: F401  (harus paling awal, sebelum telegram dimuat)

import sys

from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from config import ADMIN_IDS, CHANNEL_USERNAME, TOKEN, request_kwargs
from core.database import init_db
from core.errors import error_handler
from core.logger import get_logger, setup_logging
from features.approval.handlers import (
    handle_approval_callback,
    handle_caption_input,
    handle_caption_reply,
    hapus_postingan_command,
    list_approval_groups_command,
    list_post_command,
    pending_approvals_command,
    remove_approval_group_command,
    set_admin_caption_command,
    set_approval_group_command,
)
from features.broadcast.handlers import bc, bcphoto, bcvideo
from features.buttons.handlers import add_button_command, list_buttons_command, remove_buttons_command
from features.delivery.share import handle_image_link
from features.fsub.handlers import (
    add_channel_command,
    clean_duplicate_channels,
    get_text_sub_command,
    handle_channel_forward,
    handle_fsub_callback,
    list_channels_command,
    remove_channel_command,
    set_invite_link_command,
    set_text_sub_command,
    set_text_thumb_command,
)
from features.hashtag.handlers import (
    add_hashtag_command,
    check_hashtag_image_command,
    list_hashtag_images_command,
    list_hashtags_command,
    remove_hashtag_command,
    remove_hashtag_image_command,
    set_hashtag_image_command,
)
from features.menu.handlers import (
    admin_stats,
    getphoto_command,
    handle_menu_callback,
    handle_user_menu_callback,
    send_bot_intro_with_photo,
)
from features.thumbnail.handlers import get_thumbnail, set_thumbnail
from features.upload.handlers import handle_gif, handle_hashtag_callback, handle_photo, handle_video
from features.whitelist.handlers import unwhitelist_command, whitelist_command, whitelist_list_command

log = get_logger(__name__)

COMMANDS = {
    "start": handle_image_link,
    "stats": admin_stats,
    "sendch": send_bot_intro_with_photo,
    "gp": getphoto_command,
    "setthumb": set_thumbnail,
    "getthumb": get_thumbnail,
    "addchannel": add_channel_command,
    "rmchannel": remove_channel_command,
    "channels": list_channels_command,
    "settextthumb": set_text_thumb_command,
    "setinvite": set_invite_link_command,
    "settextsub": set_text_sub_command,
    "gettextsub": get_text_sub_command,
    "clearch": clean_duplicate_channels,
    "cleanch": clean_duplicate_channels,
    "settags": add_hashtag_command,
    "listtags": list_hashtags_command,
    "deltags": remove_hashtag_command,
    "setimg": set_hashtag_image_command,
    "delimg": remove_hashtag_image_command,
    "listimg": list_hashtag_images_command,
    "checkimg": check_hashtag_image_command,
    "addbutton": add_button_command,
    "rmbuttons": remove_buttons_command,
    "listbuttons": list_buttons_command,
    "free": whitelist_command,
    "delfree": unwhitelist_command,
    "freelist": whitelist_list_command,
    "setgrup": set_approval_group_command,
    "delgrup": remove_approval_group_command,
    "listgrup": list_approval_groups_command,
    "pending": pending_approvals_command,
    "cp": set_admin_caption_command,
    "hapus": hapus_postingan_command,
    "listpost": list_post_command,
    "bc": bc,
    "bcfoto": bcphoto,
    "bcvideo": bcvideo,
}


def register_handlers(dp):
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.reply, handle_caption_reply))
    dp.add_handler(
        MessageHandler(Filters.text & Filters.chat_type.group & ~Filters.command, handle_caption_input),
        group=0,
    )

    for name, handler in COMMANDS.items():
        dp.add_handler(CommandHandler(name, handler))

    dp.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^(menu_|back_to_admin|back_to_user)"))
    dp.add_handler(
        CallbackQueryHandler(handle_approval_callback, pattern="^(approve_|reject_|setcaption_|cancel_caption_)")
    )
    dp.add_handler(CallbackQueryHandler(handle_user_menu_callback, pattern="^(help_menu|back_to_menu)$"))
    dp.add_handler(
        CallbackQueryHandler(
            handle_fsub_callback,
            pattern="^(check_|add_channel_|done_join|no_invite_|private_channel_|cancel_add_channel)",
        )
    )
    dp.add_handler(
        CallbackQueryHandler(handle_hashtag_callback, pattern=r"^(h_\d+_|done_(photo|video|gif)$|cancel_(photo|video|gif)$)")
    )

    dp.add_handler(MessageHandler(Filters.forwarded, handle_channel_forward))
    dp.add_handler(MessageHandler(Filters.video & Filters.chat_type.private, handle_video))
    dp.add_handler(MessageHandler(Filters.animation & Filters.chat_type.private, handle_gif))
    dp.add_handler(MessageHandler(Filters.photo & Filters.chat_type.private, handle_photo))

    dp.add_error_handler(error_handler)


def main():
    setup_logging()
    if not TOKEN:
        log.critical("BOT_TOKEN belum diisi. Isi di file .env atau environment variable.")
        sys.exit(1)

    init_db()
    updater = Updater(token=TOKEN, use_context=True, request_kwargs=request_kwargs)
    register_handlers(updater.dispatcher)

    log.info("Bot berjalan | @%s | channel %s | admin %s", updater.bot.username, CHANNEL_USERNAME, ADMIN_IDS)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.critical("Bot berhenti karena error", exc_info=True)
        sys.exit(1)
