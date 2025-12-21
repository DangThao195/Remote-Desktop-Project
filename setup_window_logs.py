"""
Script để tạo bảng window_logs trong database
"""
import mysql.connector
from config.server_config import host_db, user_db, password_db, database_db

def create_window_logs_table():
    try:
        conn = mysql.connector.connect(
            host=host_db,
            user=user_db,
            password=password_db,
            database=database_db
        )
        cursor = conn.cursor()
        
        # Tạo bảng window_logs
        create_table_query = """
        CREATE TABLE IF NOT EXISTS window_logs (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            WindowTitle VARCHAR(500) NOT NULL,
            ProcessName VARCHAR(255) NOT NULL,
            ViewID VARCHAR(100) NOT NULL,
            LoggedAt DATETIME NOT NULL,
            INDEX idx_view_id (ViewID),
            INDEX idx_logged_at (LoggedAt),
            INDEX idx_view_logged (ViewID, LoggedAt)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("✅ Đã tạo bảng window_logs thành công!")
        
        # Kiểm tra bảng
        cursor.execute("SHOW TABLES LIKE 'window_logs'")
        result = cursor.fetchone()
        if result:
            print(f"✅ Bảng {result[0]} đã tồn tại")
            
            # Hiển thị cấu trúc bảng
            cursor.execute("DESCRIBE window_logs")
            columns = cursor.fetchall()
            print("\n📋 Cấu trúc bảng window_logs:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    create_window_logs_table()
