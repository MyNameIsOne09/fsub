from config import ADMIN_IDS
from core.logger import get_logger

log = get_logger(__name__)


def is_admin(user_id):
    return user_id in ADMIN_IDS


def download_file(bot, file_id):
    """Download file dari Telegram ke memory"""
    try:
        file = bot.get_file(file_id)
        file_data = file.download_as_bytearray()
        return bytes(file_data)
    except Exception as e:
        log.error(f"Download error: {e}", exc_info=True)
        return None
