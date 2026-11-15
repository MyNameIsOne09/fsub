from datetime import datetime
from core.database import conn, c


def add_channel_button(channel_id, button_text, button_url, position=0):
    """Tambah custom button untuk channel"""
    c.execute('''
        INSERT INTO channel_buttons (channel_id, button_text, button_url, button_position, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (channel_id, button_text, button_url, position, datetime.now().isoformat()))
    conn.commit()


def get_channel_buttons(channel_id):
    """Dapatkan semua custom button untuk channel"""
    c.execute('SELECT button_text, button_url, button_position FROM channel_buttons WHERE channel_id = ? ORDER BY button_position', (channel_id,))
    return c.fetchall()


def clear_channel_buttons(channel_id):
    """Hapus semua button channel"""
    c.execute('DELETE FROM channel_buttons WHERE channel_id = ?', (channel_id,))
    conn.commit()
