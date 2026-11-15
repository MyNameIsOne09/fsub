import sqlite3

from config import DB_PATH
from core.logger import get_logger

log = get_logger(__name__)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_data BLOB,
    sender_id INTEGER,
    sender_name TEXT,
    username TEXT,
    caption TEXT,
    file_size INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS caption_state (
    user_id INTEGER PRIMARY KEY,
    approval_id INTEGER,
    data TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_data BLOB,
    sender_id INTEGER,
    sender_name TEXT,
    username TEXT,
    caption TEXT,
    file_size INTEGER,
    duration INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS image_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER,
    link_code TEXT UNIQUE,
    created_at TIMESTAMP,
    views INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    joined_channel BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS forced_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER,
    channel_username TEXT,
    channel_title TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_settings (
    channel_id INTEGER PRIMARY KEY,
    text_thumbnail TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_channel_joins (
    user_id INTEGER,
    channel_id INTEGER,
    joined_at TIMESTAMP,
    PRIMARY KEY (user_id, channel_id)
);

CREATE TABLE IF NOT EXISTS channel_buttons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER,
    button_text TEXT,
    button_url TEXT,
    button_position INTEGER DEFAULT 0,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS available_hashtags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_subtext (
    channel_id INTEGER PRIMARY KEY,
    subtext TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upload_whitelist (
    user_id INTEGER PRIMARY KEY,
    added_by INTEGER,
    added_at TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS posted_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_id INTEGER,
    media_type TEXT,
    media_id INTEGER,
    channel_message_id INTEGER,
    channel_chat_id INTEGER,
    link_code TEXT,
    sender_id INTEGER,
    sender_name TEXT,
    posted_at TIMESTAMP,
    posted_by INTEGER
);

CREATE TABLE IF NOT EXISTS channel_caption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caption_text TEXT,
    is_active BOOLEAN DEFAULT 1,
    updated_by INTEGER,
    updated_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hashtag_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE,
    file_id TEXT,
    file_data BLOB,
    caption TEXT,
    set_by INTEGER,
    set_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS gifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_data BLOB,
    sender_id INTEGER,
    sender_name TEXT,
    username TEXT,
    caption TEXT,
    file_size INTEGER,
    duration INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pending_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_type TEXT,
    file_id TEXT,
    file_data BLOB,
    sender_id INTEGER,
    sender_name TEXT,
    username TEXT,
    caption TEXT,
    file_size INTEGER,
    duration INTEGER DEFAULT 0,
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    hashtags TEXT,
    status TEXT DEFAULT 'pending',
    admin_caption TEXT,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    created_at TIMESTAMP,
    message_id INTEGER,
    chat_id INTEGER
);

CREATE TABLE IF NOT EXISTS approval_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE,
    chat_title TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
);
"""

MIGRATIONS = (
    ("users", "pending_gif_id", "INTEGER DEFAULT NULL"),
    ("users", "pending_image_id", "INTEGER DEFAULT NULL"),
    ("users", "pending_video_id", "INTEGER DEFAULT NULL"),
    ("forced_channels", "invite_link", "TEXT"),
    ("forced_channels", "updated_at", "TEXT"),
)


def _columns(table):
    c.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in c.fetchall()}


def init_db():
    """Buat tabel yang belum ada dan tambahkan kolom baru pada database lama."""
    c.executescript(SCHEMA)
    for table, column, ddl in MIGRATIONS:
        if column not in _columns(table):
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            log.info("Kolom %s.%s ditambahkan", table, column)
    conn.commit()
    log.info("Database siap: %s", DB_PATH)
