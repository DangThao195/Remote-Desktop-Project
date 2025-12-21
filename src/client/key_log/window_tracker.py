"""
Window Title Tracker - Theo dõi và lưu window titles
"""
import mysql.connector
from datetime import datetime
import win32gui
import win32process
import psutil
from config.server_config import host_db, user_db, password_db, database_db


def get_connection():
    return mysql.connector.connect(
        host=host_db,
        user=user_db,
        password=password_db,
        database=database_db
    )


def get_active_window_info():
    """Lấy thông tin cửa sổ đang active"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        
        return {
            'title': win32gui.GetWindowText(hwnd),
            'process_name': process.name(),
            'pid': pid
        }
    except:
        return None


def create_window_log(window_title, process_name, view_id):
    """Lưu window title vào database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO window_logs (WindowTitle, ProcessName, ViewID, LoggedAt)
            VALUES (%s, %s, %s, NOW())
        """

        cursor.execute(query, (window_title, process_name, view_id))
        conn.commit()
        return True

    except Exception as e:
        print(f"❌ DB Error (window_logs): {e}")
        return False

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


def get_windows_by_session(view_id, session_start_time):
    """Lấy danh sách windows từ một session cụ thể"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT WindowTitle, ProcessName, LoggedAt
            FROM window_logs
            WHERE ViewID = %s AND LoggedAt >= %s
            ORDER BY LoggedAt DESC
        """

        cursor.execute(query, (view_id, session_start_time))
        results = cursor.fetchall()
        return results

    except Exception as e:
        print(f"❌ DB Error: {e}")
        return []

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


def get_all_windows(view_id):
    """Lấy tất cả windows của một client"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT WindowTitle, ProcessName, LoggedAt
            FROM window_logs
            WHERE ViewID = %s
            ORDER BY LoggedAt DESC
            LIMIT 100
        """

        cursor.execute(query, (view_id,))
        results = cursor.fetchall()
        return results

    except Exception as e:
        print(f"❌ DB Error: {e}")
        return []

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
