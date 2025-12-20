# server0/server_logger.py
import datetime
import os

class ServerLogger:
    LOG_DIR = "log"
    
    @staticmethod
    def _ensure_log_dir():
        """Đảm bảo thư mục log tồn tại"""
        if not os.path.exists(ServerLogger.LOG_DIR):
            os.makedirs(ServerLogger.LOG_DIR)
            print(f"[ServerLogger] Đã tạo thư mục log: {ServerLogger.LOG_DIR}")

    @staticmethod
    def log_alert(client_id, violation_type, detail):
        """Ghi cảnh báo vi phạm vào file log"""
        ServerLogger._ensure_log_dir()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # File log theo ngày: security_alerts_YYYY-MM-DD.log
        log_file = os.path.join(ServerLogger.LOG_DIR, f"security_alerts_{date_str}.log")
        
        log_entry = f"[{timestamp}] CLIENT: {client_id} | TYPE: {violation_type} | DETAIL: {detail}\n"
        
        # Ghi vào file (hoặc DB sau này)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"[LOGGER] ✅ Đã ghi cảnh báo vào {log_file}: {log_entry.strip()}")
        except Exception as e:
            print(f"[LOGGER] ❌ Lỗi ghi log: {e}")