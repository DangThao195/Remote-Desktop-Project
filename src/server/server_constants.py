# server/server_constants.py

import ssl
import json
import os
import logging

# Load config from JSON file
def load_config():
    """Load server configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'server_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}, using defaults")
        return {}

CONFIG = load_config()

# --- Cấu hình Mạng & Bảo mật ---
SERVER_HOST = CONFIG.get('server', {}).get('host', '0.0.0.0')
SERVER_PORT = CONFIG.get('server', {}).get('port', 5000)
USE_TLS = CONFIG.get('server', {}).get('use_tls', True)

# BẮT BUỘC nếu dùng TLS: Bạn phải tạo file cert và key
# Lệnh tự tạo (cho development):
# openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -sha256 -days 365 -nodes -addext "subjectAltName=DNS:localhost"
CERT_FILE = CONFIG.get('server', {}).get('cert_file', 'src/server.crt')
KEY_FILE = CONFIG.get('server', {}).get('key_file', 'src/server.key')

# Auth Server Configuration
AUTH_SERVER_ENABLED = CONFIG.get('auth_server', {}).get('enabled', True)
AUTH_SERVER_HOST = CONFIG.get('auth_server', {}).get('host', '0.0.0.0')
AUTH_SERVER_PORT = CONFIG.get('auth_server', {}).get('port', 5001)

# Logging Configuration
LOG_LEVEL = CONFIG.get('logging', {}).get('level', 'INFO')
LOG_FORMAT = CONFIG.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = CONFIG.get('logging', {}).get('file', 'log/server.log')

# Cấu hình TLS
# Sử dụng cài đặt an toàn, yêu cầu ít nhất TLS 1.2
TLS_VERSION = ssl.PROTOCOL_TLS_SERVER
try:
    # Tùy chọn mới hơn, an toàn hơn
    TLS_VERSION = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    TLS_VERSION.minimum_version = ssl.TLSVersion.TLSv1_2
    TLS_VERSION.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    TLS_VERSION.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:ECDHE+AES256:!aNULL:!MD5:!RC4")
except AttributeError:
    # Fallback cho Python cũ
    TLS_VERSION = ssl.PROTOCOL_TLSv1_2

# --- Định nghĩa Kênh (Channel) ---
# Phải khớp với client và manager
CHANNEL_VIDEO = 2
CHANNEL_CONTROL = 3
CHANNEL_INPUT = 4
CHANNEL_FILE = 5
CHANNEL_CURSOR = 6
# Danh sách tất cả các kênh mà ServerReceiver sẽ lắng nghe
ALL_CHANNELS = (
    CHANNEL_VIDEO,
    CHANNEL_CONTROL,
    CHANNEL_INPUT,
    CHANNEL_FILE,
    CHANNEL_CURSOR,
)

# --- Định nghĩa Vai trò (Role) ---
ROLE_MANAGER = "manager"
ROLE_CLIENT = "client"
ROLE_UNKNOWN = "unknown"

# --- Định nghĩa Lệnh (Command) ---
# Các lệnh này được gửi qua PDU_TYPE_CONTROL
# Client/Manager -> Server
CMD_REGISTER = "register:"         # Ví dụ: "register:manager"
CMD_LOGIN = "login:"         
CMD_LOGIN_OK = "login_ok"
CMD_LOGIN_FAIL = "login_fail"

CMD_LIST_CLIENTS = "list_clients"  # Manager yêu cầu danh sách client
CMD_CONNECT_CLIENT = "connect:"    # Manager yêu cầu kết nối: "connect:client_pc_1"
CMD_DISCONNECT = "disconnect"      # Manager/Client báo ngắt kết nối phiên
CMD_SECURITY_ALERT = "security_alert" # Cấu trúc: "security_alert:Loại vi phạm|Nội dung chi tiết"

# Server -> Client/Manager
CMD_REGISTER_OK = "register_ok"   # Ví dụ: "register_ok:manager"
CMD_CLIENT_LIST_UPDATE = "client_list_update" # Gửi JSON: "client_list_update:['pc1', 'pc2']"
CMD_SESSION_STARTED = "session_started"       # Báo phiên bắt đầu: "session_started:client_pc_1"
CMD_SESSION_ENDED = "session_ended"           # Báo phiên kết thúc: "session_ended:client_pc_1"
CMD_ERROR = "error"                           # Báo lỗi: "error:Client not found"
