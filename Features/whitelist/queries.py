from datetime import datetime
from core.database import conn, c
from core.helpers import is_admin


def is_allowed_to_upload(user_id):
    """Cek apakah user diizinkan upload"""
    if is_admin(user_id):
        return True

    c.execute('SELECT user_id FROM upload_whitelist WHERE user_id = ?', (user_id,))
    return c.fetchone() is not None


def add_to_whitelist(user_id, admin_id, notes=""):
    """Tambah user ke whitelist"""
    c.execute('''
        INSERT OR REPLACE INTO upload_whitelist (user_id, added_by, added_at, notes)
        VALUES (?, ?, ?, ?)
    ''', (user_id, admin_id, datetime.now().isoformat(), notes))
    conn.commit()


def remove_from_whitelist(user_id):
    """Hapus user dari whitelist"""
    c.execute('DELETE FROM upload_whitelist WHERE user_id = ?', (user_id,))
    conn.commit()


def get_whitelist():
    """Dapatkan semua user di whitelist"""
    c.execute('''
        SELECT w.user_id, u.username, w.added_at, w.notes
        FROM upload_whitelist w
        LEFT JOIN users u ON w.user_id = u.user_id
        ORDER BY w.added_at DESC
    ''')
    return c.fetchall()
