from telegram import Update
from telegram.error import NetworkError, TimedOut

from core.logger import get_logger

log = get_logger(__name__)


def _describe_update(update):
    if not isinstance(update, Update):
        return "-"
    user = update.effective_user.id if update.effective_user else "-"
    chat = update.effective_chat.id if update.effective_chat else "-"
    if update.callback_query:
        what = f"callback={update.callback_query.data}"
    elif update.effective_message:
        text = update.effective_message.text or update.effective_message.caption or ""
        what = f"pesan={text[:60]!r}"
    else:
        what = "update lain"
    return f"user={user} chat={chat} {what}"


def error_handler(update, context):
    """Catat semua error dari handler ke konsol dan logs/error.log."""
    error = context.error
    if isinstance(error, (NetworkError, TimedOut)):
        log.warning("Masalah jaringan Telegram: %s", error)
        return
    log.error(
        "Error pada handler | %s | %s: %s",
        _describe_update(update),
        type(error).__name__,
        error,
        exc_info=(type(error), error, error.__traceback__),
    )
