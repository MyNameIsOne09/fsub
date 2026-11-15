import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from config import LOG_DIR

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 5

_COLORS = {
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;31m",
}
_RESET = "\033[0m"


class ConsoleFormatter(logging.Formatter):
    """Format konsol (server/Termux): warning kuning, error merah."""

    def __init__(self, use_color):
        super().__init__(LOG_FORMAT, DATE_FORMAT)
        self.use_color = use_color

    def format(self, record):
        text = super().format(record)
        color = _COLORS.get(record.levelno)
        if record.levelno >= logging.ERROR:
            text = ">>> ERROR <<<\n" + text
        if self.use_color and color:
            text = f"{color}{text}{_RESET}"
        return text


def setup_logging():
    """Pasang logger: konsol, logs/bot.log (semua) dan logs/error.log (hanya error)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if getattr(root, "_dzbot_ready", False):
        return
    root.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ConsoleFormatter(sys.stdout.isatty()))

    app_file = RotatingFileHandler(
        LOG_DIR / "bot.log", maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    app_file.setLevel(logging.INFO)
    app_file.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    error_file = RotatingFileHandler(
        LOG_DIR / "error.log", maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    root.addHandler(console)
    root.addHandler(app_file)
    root.addHandler(error_file)
    root._dzbot_ready = True

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    _install_exception_hooks()


def _install_exception_hooks():
    log = logging.getLogger("uncaught")

    def handle_main(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("Exception tidak tertangani", exc_info=(exc_type, exc, tb))

    def handle_thread(args):
        if issubclass(args.exc_type, SystemExit):
            return
        log.critical(
            "Exception tidak tertangani di thread %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = handle_main
    threading.excepthook = handle_thread


def get_logger(name):
    return logging.getLogger(name)
