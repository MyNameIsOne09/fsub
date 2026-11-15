from datetime import datetime
import json
from core.database import conn, c
from core.logger import get_logger

log = get_logger(__name__)


def save_caption_state(user_id, approval_id, data):
    """Simpan state caption ke database"""
    try:
        c.execute('''
            INSERT OR REPLACE INTO caption_state (user_id, approval_id, data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, approval_id, json.dumps(data), datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        log.error(f"Error saving state: {e}", exc_info=True)
        return False


def get_caption_state(user_id):
    """Ambil state caption dari database"""
    try:
        c.execute('SELECT approval_id, data FROM caption_state WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        if result:
            approval_id = result[0]
            data = json.loads(result[1])
            return approval_id, data
        return None, None
    except Exception as e:
        log.error(f"Error getting state: {e}", exc_info=True)
        return None, None


def clear_caption_state(user_id):
    """Hapus state caption"""
    try:
        c.execute('DELETE FROM caption_state WHERE user_id = ?', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        log.error(f"Error clearing state: {e}", exc_info=True)
        return False


def save_pending_approval(data):
    """Simpan konten yang menunggu approval"""
    c.execute('''
        INSERT INTO pending_approvals (
            media_type, file_id, file_data, sender_id, sender_name,
            username, caption, file_size, duration, width, height,
            hashtags, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('media_type'),
        data.get('file_id'),
        data.get('file_data'),
        data.get('sender_id'),
        data.get('sender_name'),
        data.get('username'),
        data.get('caption'),
        data.get('file_size', 0),
        data.get('duration', 0),
        data.get('width', 0),
        data.get('height', 0),
        data.get('hashtags', ''),
        'pending',
        datetime.now().isoformat()
    ))
    conn.commit()
    return c.lastrowid


def get_pending_approval(approval_id):
    """Ambil data pending approval by ID"""
    c.execute('SELECT * FROM pending_approvals WHERE id = ? AND status = "pending"', (approval_id,))
    return c.fetchone()


def get_all_pending_approvals():
    """Ambil semua pending approval"""
    c.execute('''
        SELECT id, media_type, sender_name, caption, created_at
        FROM pending_approvals
        WHERE status = "pending"
        ORDER BY created_at DESC
    ''')
    return c.fetchall()


def approve_content(approval_id, admin_id, admin_caption=None):
    """Setujui konten dan set caption admin"""
    c.execute('''
        UPDATE pending_approvals
        SET status = "approved",
            admin_caption = ?,
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
    ''', (admin_caption, admin_id, datetime.now().isoformat(), approval_id))
    conn.commit()

    c.execute('SELECT * FROM pending_approvals WHERE id = ?', (approval_id,))
    return c.fetchone()


def reject_content(approval_id, admin_id):
    """Tolak konten"""
    c.execute('''
        UPDATE pending_approvals
        SET status = "rejected",
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
    ''', (admin_id, datetime.now().isoformat(), approval_id))
    conn.commit()


def get_approval_stats():
    """Dapatkan statistik approval"""
    c.execute('SELECT COUNT(*) FROM pending_approvals WHERE status = "pending"')
    pending = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM pending_approvals WHERE status = "approved"')
    approved = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM pending_approvals WHERE status = "rejected"')
    rejected = c.fetchone()[0]

    return pending, approved, rejected


def add_approval_group(chat_id, chat_title):
    """Tambah grup untuk notifikasi approval"""
    c.execute('''
        INSERT OR REPLACE INTO approval_groups (chat_id, chat_title, is_active, created_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, chat_title, 1, datetime.now().isoformat()))
    conn.commit()


def remove_approval_group(chat_id):
    """Hapus grup approval"""
    c.execute('DELETE FROM approval_groups WHERE chat_id = ?', (chat_id,))
    conn.commit()


def get_approval_groups():
    """Dapatkan semua grup approval aktif"""
    c.execute('SELECT chat_id, chat_title FROM approval_groups WHERE is_active = 1')
    return c.fetchall()


def is_approval_group(chat_id):
    """Cek apakah chat_id adalah grup approval"""
    c.execute('SELECT id FROM approval_groups WHERE chat_id = ? AND is_active = 1', (chat_id,))
    return c.fetchone() is not None


def save_posted_content(approval_id, media_type, media_id, channel_message_id, channel_chat_id, link_code, sender_id, sender_name, admin_id):
    """Simpan data postingan yang sudah di-ACC"""
    c.execute('''
        INSERT INTO posted_content (
            approval_id, media_type, media_id, channel_message_id,
            channel_chat_id, link_code, sender_id, sender_name,
            posted_at, posted_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        approval_id, media_type, media_id, channel_message_id,
        channel_chat_id, link_code, sender_id, sender_name,
        datetime.now().isoformat(), admin_id
    ))
    conn.commit()
    return c.lastrowid


def get_posted_content_by_approval(approval_id):
    """Ambil data postingan berdasarkan approval_id"""
    c.execute('SELECT * FROM posted_content WHERE approval_id = ?', (approval_id,))
    return c.fetchone()


def delete_posted_content(approval_id):
    """Hapus data postingan dari database (setelah dihapus dari channel)"""
    c.execute('DELETE FROM posted_content WHERE approval_id = ?', (approval_id,))
    conn.commit()
    return c.rowcount > 0


def get_all_posted_content(limit=50):
    """Ambil daftar postingan terakhir"""
    c.execute('''
        SELECT approval_id, media_type, sender_name, link_code, posted_at, channel_message_id
        FROM posted_content
        ORDER BY posted_at DESC
        LIMIT ?
    ''', (limit,))
    return c.fetchall()
