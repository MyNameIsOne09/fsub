from datetime import datetime
from core.database import conn, c
from core.logger import get_logger

log = get_logger(__name__)


def get_available_hashtags():
    """Dapatkan semua hashtag yang tersedia"""
    c.execute('SELECT tag FROM available_hashtags WHERE is_active = 1')
    return [row[0] for row in c.fetchall()]


def add_hashtag(tag):
    """Tambah hashtag baru"""
    c.execute('INSERT OR IGNORE INTO available_hashtags (tag, is_active, created_at) VALUES (?, ?, ?)',
              (tag, 1, datetime.now().isoformat()))
    conn.commit()


def remove_hashtag(tag):
    """Hapus hashtag"""
    c.execute('DELETE FROM available_hashtags WHERE tag = ?', (tag,))
    conn.commit()


def set_hashtag_image(tag, file_id, file_data=None, caption="", admin_id=None):
    """Set gambar untuk hashtag tertentu"""
    try:
        tag = tag.strip()

        c.execute('SELECT id FROM hashtag_images WHERE tag = ?', (tag,))
        existing = c.fetchone()

        if existing:
            c.execute('''
                UPDATE hashtag_images
                SET file_id = ?, file_data = ?, caption = ?, set_by = ?, set_at = ?, is_active = 1
                WHERE tag = ?
            ''', (file_id, file_data, caption, admin_id, datetime.now().isoformat(), tag))
        else:
            c.execute('''
                INSERT INTO hashtag_images (tag, file_id, file_data, caption, set_by, set_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tag, file_id, file_data, caption, admin_id, datetime.now().isoformat()))

        conn.commit()

        c.execute('SELECT tag, file_id, is_active FROM hashtag_images WHERE tag = ?', (tag,))
        result = c.fetchone()

        if result:
            return True
        else:
            return False
    except Exception as e:
        log.error(f"Error set_hashtag_image: {e}", exc_info=True)
        return False


def get_hashtag_image(tag):
    """Ambil gambar untuk hashtag tertentu"""
    try:
        c.execute('SELECT file_id, file_data, caption FROM hashtag_images WHERE tag = ? AND is_active = 1', (tag,))
        result = c.fetchone()
        if result:
            return result

        if tag.startswith('📬'):
            clean_tag = tag.replace('📬', '').strip()
            c.execute('SELECT file_id, file_data, caption FROM hashtag_images WHERE tag = ? AND is_active = 1', (clean_tag,))
            result = c.fetchone()
            if result:
                return result

        c.execute('SELECT file_id, file_data, caption FROM hashtag_images WHERE tag LIKE ? AND is_active = 1', (f'%{tag}%',))
        result = c.fetchone()
        if result:
            return result

        if tag.startswith('📬'):
            clean_tag = tag.replace('📬', '').strip()
            c.execute('SELECT file_id, file_data, caption FROM hashtag_images WHERE tag LIKE ? AND is_active = 1', (f'%{clean_tag}%',))
            result = c.fetchone()
            if result:
                return result

        return None
    except Exception as e:
        log.error(f"Error get_hashtag_image: {e}", exc_info=True)
        return None


def get_all_hashtag_images():
    """Ambil semua gambar hashtag"""
    c.execute('SELECT tag, file_id, caption, set_at FROM hashtag_images WHERE is_active = 1 ORDER BY tag')
    return c.fetchall()


def remove_hashtag_image(tag):
    """Hapus gambar hashtag (soft delete)"""
    c.execute('UPDATE hashtag_images SET is_active = 0 WHERE tag = ?', (tag,))
    conn.commit()
    return c.rowcount > 0
