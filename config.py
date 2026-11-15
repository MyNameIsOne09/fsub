import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env_file(path):
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(BASE_DIR / ".env")

TOKEN = os.getenv("BOT_TOKEN", "ISI TOKEN BOT DISINI")
CHANNEL_USERNAME = "@storyzenni"
CHANNEL_ID = ISI CHANNEL ID BERAWAL -100
ADMIN_IDS = [8189597803]

DB_PATH = BASE_DIR / "database.db"
LOG_DIR = BASE_DIR / "logs"

request_kwargs = {
    "connect_timeout": 60,
    "read_timeout": 120,
    "con_pool_size": 10,
}
