# manager/manager_constants.py
# --- Cấu hình Mạng & Bảo mật ---

# BẮT BUỘC: File CA (Certificate Authority) của server
# Nếu bạn tự tạo cert server (self-signed), file .crt chính là file CA.
# Sao chép file 'server.crt' từ server và đổi tên thành 'ca.crt' ở đây.
import os

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CA_FILE = os.path.join(_CURRENT_DIR, "ca.crt")

# --- Định nghĩa Kênh (Channel) ---
# Phải khớp với server
CHANNEL_VIDEO = 2
CHANNEL_CONTROL = 3
CHANNEL_INPUT = 4
CHANNEL_FILE = 5
CHANNEL_CURSOR = 6

ALL_CHANNELS = (
    CHANNEL_VIDEO,
    CHANNEL_CONTROL,
    CHANNEL_INPUT,
    CHANNEL_FILE,
    CHANNEL_CURSOR,
)

# --- Lệnh Gửi đi (Manager -> Server) ---
CMD_REGISTER = "register:"
CMD_LOGIN = "login:"
CMD_LIST_CLIENTS = "list_clients"
CMD_VIEW_CLIENT = "view:"  # Xem màn hình (1-to-many), ví dụ: "view:admin3"
CMD_CONTROL_CLIENT = "control:"  # Điều khiển (1-to-1 exclusive), ví dụ: "control:admin3"
CMD_STOP_VIEW = "stop_view"  # Dừng xem
CMD_STOP_CONTROL = "stop_control"  # Dừng điều khiển
CMD_DISCONNECT = "disconnect"  # Legacy, dùng stop_control thay thế

# --- Lệnh Nhận về (Server -> Manager) ---
CMD_REGISTER_OK = "register_ok"
CMD_CLIENT_LIST_UPDATE = "client_list_update" # "client_list_update:['pc1', 'pc2']"
CMD_VIEW_STARTED = "view_started"  # Server xác nhận view session đã bắt đầu
CMD_CONTROL_STARTED = "control_started"  # Server xác nhận control session đã bắt đầu
CMD_VIEW_ENDED = "view_ended"  # View session kết thúc
CMD_CONTROL_ENDED = "control_ended"  # Control session kết thúc
CMD_SESSION_STARTED = "session_started"  # Legacy
CMD_SESSION_ENDED = "session_ended"  # Legacy
CMD_ERROR = "error"