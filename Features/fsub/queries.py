from datetime import datetime
from core.database import conn, c


def add_forced_channel(chat_id, chat_username, chat_title, invite_link=None):
    """Tambah channel/grup wajib join dengan invite link opsional"""
    c.execute('''
        INSERT OR REPLACE INTO forced_channels (channel_id, channel_username, channel_title, is_active, invite_link, created_at)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM forced_channels WHERE channel_id = ?), ?))
    ''', (chat_id, chat_username, chat_title, 1, invite_link, chat_id, datetime.now().isoformat()))
    conn.commit()


def remove_forced_channel(channel_id):
    """Hapus channel wajib join"""
    c.execute('DELETE FROM forced_channels WHERE channel_id = ?', (channel_id,))
    conn.commit()


def get_all_forced_channels():
    """Dapatkan semua channel wajib join"""
    c.execute('SELECT channel_id, channel_username, channel_title, is_active FROM forced_channels WHERE is_active = 1')
    return c.fetchall()


def get_channel_subtext(channel_id):
    """Dapatkan text subscription untuk channel tertentu"""
    c.execute('SELECT subtext FROM channel_subtext WHERE channel_id = ?', (channel_id,))
    result = c.fetchone()
    return result[0] if result else None


def set_channel_subtext(channel_id, text):
    """Set text subscription untuk channel"""
    c.execute('''
        INSERT OR REPLACE INTO channel_subtext (channel_id, subtext, updated_at)
        VALUES (?, ?, ?)
    ''', (channel_id, text, datetime.now().isoformat()))
    conn.commit()


def delete_channel_subtext(channel_id):
    """Hapus text subscription untuk channel"""
    c.execute('DELETE FROM channel_subtext WHERE channel_id = ?', (channel_id,))
    conn.commit()


def set_channel_text_thumbnail(channel_id, text):
    """Set text thumbnail untuk channel"""
    c.execute('''
        INSERT OR REPLACE INTO channel_settings (channel_id, text_thumbnail, updated_at)
        VALUES (?, ?, ?)
    ''', (channel_id, text, datetime.now().isoformat()))
    conn.commit()
