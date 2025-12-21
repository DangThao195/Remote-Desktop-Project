# server/core/session_manager.py

import threading
import json
import time
import sys
import os
from queue import Queue, Empty

# Đảm bảo Python tìm thấy thư mục gốc
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

from src.server.server_constants import (
    ROLE_MANAGER, ROLE_CLIENT, ROLE_UNKNOWN,
    CMD_LOGIN, CMD_LOGIN_OK, CMD_LOGIN_FAIL,
    CMD_REGISTER, CMD_REGISTER_OK, 
    CMD_LIST_CLIENTS, CMD_CLIENT_LIST_UPDATE,
    CMD_CONNECT_CLIENT, CMD_SESSION_STARTED, CMD_SESSION_ENDED,
    CMD_ERROR, CHANNEL_CONTROL, CHANNEL_INPUT
)
from src.server.core.auth_handler import (
    sign_in as auth_sign_in, 
    sign_up as auth_sign_up,
    log_out as auth_log_out
)
from src.server.core.session import ServerSession

from src.common.network.pdu_builder import PDUBuilder
from src.common.network.mcs_layer import MCSLite

# Import database cho keylog
try:
    from src.client.key_log.database import create_keystroke
    KEYLOG_DB_AVAILABLE = True
except ImportError:
    print("[SessionManager] WARN: Keylog database module không khả dụng")
    KEYLOG_DB_AVAILABLE = False
    def create_keystroke(*args, **kwargs):
        return False

# Quản lý việc đăng ký (client/manager), xác thực User và điều phối các phiên (session).
class SessionManager(threading.Thread):
    def __init__(self, broadcaster):
        super().__init__(daemon=True, name="SessionManager")
        self.broadcaster = broadcaster
        self.pdu_queue = Queue()  # Hàng đợi xử lý tin nhắn Control
        self.running = True
        self.builder = PDUBuilder()
        self.seq = 0  # Sequence number
        
        # Quản lý kết nối và User
        self.clients = {}           # { client_id -> role }
        self.authenticated_users = {} # { client_id -> username } (Chỉ user đã login thành công)
        
        # Quản lý Phiên (Remote Desktop)
        self.client_session_map = {} # { client_id -> ServerSession object }
        self.active_sessions = {}    # { session_id -> ServerSession object }
        
        # Pending connection requests (Case 1: Manager connects before Client starts)
        self.pending_requests = {}  # { client_username: manager_id }
        
        self.lock = threading.Lock()

    def _next_seq(self):
        """Generate next sequence number"""
        with self.lock:
            self.seq += 1
            return self.seq

    def start(self):
        self.running = True
        super().start()
        print("[SessionManager] Service Started.")

    def stop(self):
        self.running = False
        with self.lock:            
            sessions = list(self.active_sessions.values()) # Copy danh sách để tránh lỗi khi loop
        
        for s in sessions: 
            s.stop()
        print("[SessionManager] Service Stopped.")

    # =========================================================================
    # CÁC CALLBACK TỪ LAYER MẠNG (ServerNetwork gọi cái này)
    # =========================================================================
    
    # Khi có socket mới kết nối tới
    def handle_new_connection(self, client_id, ssl_sock):
        with self.lock:
            self.clients[client_id] = ROLE_UNKNOWN
        print(f"[Network] New connection: {client_id}")

    # Khi socket bị ngắt kết nối
    def handle_disconnection(self, client_id):
        print(f"[Network] Disconnected: {client_id}")
        
        username = None
        session = None
        role = ROLE_UNKNOWN

        # 1. Xử lý Logout DB & Xóa khỏi RAM
        with self.lock:
            role = self.clients.pop(client_id, ROLE_UNKNOWN)
            username = self.authenticated_users.pop(client_id, None)
            session = self.client_session_map.pop(client_id, None)

        if username:
            print(f"[Auth] User {username} logged out implicitly.")
            # auth_log_out(session_id) # Nếu bạn muốn update DB LastLogin thì gọi ở đây

        # 2. Nếu đang trong phiên Remote, phải dừng phiên đó
        if session:
            print(f"[Session] Dừng phiên {session.session_id} do một bên ngắt kết nối.")
            session.stop()
            
            with self.lock:
                self.active_sessions.pop(session.session_id, None)
                # Tìm ID người còn lại để báo tin
                other_party_id = session.manager_id if client_id == session.client_id else session.client_id
                self.client_session_map.pop(other_party_id, None)
            
            # Gửi thông báo cho người còn lại (nếu họ vẫn còn online)
            if other_party_id in self.clients:
                self._send_control_pdu(other_party_id, f"{CMD_SESSION_ENDED}:Đối phương mất kết nối")

        # 3. Nếu là Client vừa thoát, cần cập nhật danh sách cho các Manager
        if role == ROLE_CLIENT:
            self._broadcast_client_list()

    # Khi có PDU mới từ Client/Manager
    """
        Trung tâm phân loại gói tin:
        - Nếu User đang trong phiên Remote -> Chuyển gói tin cho Session xử lý (Video/Input).
        - Nếu User đang rảnh -> Xử lý như lệnh Control (Login/Connect).
    """
    def handle_pdu(self, client_id, pdu):       
        pdu_type = pdu.get("type")
        
        # Phân biệt keylog (từ client) vs điều khiển input (từ manager)
        if pdu_type == "input":
            # Kiểm tra xem có phải keylog data không (có KeyData field)
            input_data = pdu.get('input', {})
            is_keylog = 'KeyData' in input_data or 'WindowTitle' in input_data
            
            # Nếu là keylog từ client → xử lý và forward tới manager
            if is_keylog:
                self._handle_input_pdu(client_id, pdu)
                return
            # Nếu là input điều khiển từ manager → forward tới client qua session
            # (để tiếp tục xử lý bên dưới)
        
        # Xử lý các loại PDU khác
        session = None
        with self.lock:
            session = self.client_session_map.get(client_id)
            
        if session:
            # User đang bận remote -> Chuyển dữ liệu vào Session
            session.enqueue_pdu(client_id, pdu)
        else:
            # User rảnh -> Đây là lệnh Control
            # Đẩy vào Queue để thread chính xử lý tuần tự, tránh race condition DB
            if pdu_type == "control":
                self.pdu_queue.put((client_id, pdu))

    # =========================================================================
    # VÒNG LẶP CHÍNH (XỬ LÝ CONTROL PDU)
    # =========================================================================
    def run(self):
        while self.running:
            try:
                # Lấy tin nhắn từ hàng đợi, timeout 0.5s để check cờ self.running
                client_id, pdu = self.pdu_queue.get(timeout=0.5)
                
                # Chỉ xử lý gói tin lại 'control' ở đây
                if pdu.get("type") == "control":
                    self._handle_control_logic(client_id, pdu)
                    
            except Empty:
                continue
            except Exception as e:
                print(f"[SessionManager] Critical Error in run loop: {e}")

    # Xử lý logic nghiệp vụ: Login, Signup, Connect...
    def _handle_control_logic(self, client_id, pdu):
        try:
            msg = pdu.get("message", "")
            if isinstance(msg, bytes):
                msg = msg.decode("utf-8") # Decode nếu cần

            # 1. Xử lý LOGIN
            if msg.startswith(CMD_LOGIN):
                # Format: "LOGIN:username:password:role"
                parts = msg.split(":")
                if len(parts) >= 3:
                    _, username, password = parts[0], parts[1], parts[2]
                    requested_role = parts[3] if len(parts) > 3 else ROLE_CLIENT
                    
                    print(f"[Auth] Check login: {username} ({requested_role})")
                    if auth_sign_in(username, password):
                        with self.lock:
                            self.clients[client_id] = requested_role
                            self.authenticated_users[client_id] = username
                        
                        self._send_control_pdu(client_id, f"{CMD_LOGIN_OK}:{requested_role}")
                        print(f"[Auth] Success: {username}")
                        
                        # Hậu xử lý: Nếu là Client login -> Báo cho Manager biết
                        if requested_role == ROLE_CLIENT:
                            self._broadcast_client_list()
                        elif requested_role == ROLE_MANAGER:
                            self._send_client_list(client_id)
                    else:
                        print(f"[Auth] Fail: {username}")
                        self._send_control_pdu(client_id, f"{CMD_LOGIN_FAIL}:Sai tài khoản hoặc mật khẩu")
                else:
                    self._send_control_pdu(client_id, f"{CMD_ERROR}:Sai định dạng login")

            # 2. Xử lý REGISTER
            elif msg.startswith(CMD_REGISTER):
                # Có 2 trường hợp:
                # A. Client đăng ký vào SessionManager (đã auth ở Auth Server): "register:client:user_id:username:role"
                # B. Đăng ký user mới: "REGISTER:username:pass:fullname:email"
                parts = msg.split(":")
                
                # Trường hợp A: Client đăng ký (đã authenticated)
                if len(parts) >= 4 and parts[1] == "client":
                    _, _, user_id, username = parts[:4]
                    role = parts[4] if len(parts) > 4 else ROLE_CLIENT
                    print(f"[Auth] Client auto-login: {username} (already authenticated)")
                    
                    with self.lock:
                        self.clients[client_id] = ROLE_CLIENT
                        self.authenticated_users[client_id] = username
                    
                    self._send_control_pdu(client_id, f"{CMD_LOGIN_OK}:client")
                    self._broadcast_client_list()
                    
                    # Check if there's a pending connection request for this client (Case 1)
                    pending_manager_id = None
                    with self.lock:
                        if username in self.pending_requests:
                            pending_manager_id = self.pending_requests.pop(username)
                            print(f"[Session] Found pending request from Manager {pending_manager_id} for Client {username}")
                    
                    # Start session outside lock to avoid deadlock
                    if pending_manager_id:
                        self._attempt_start_session(pending_manager_id, client_id)
                    
                # Trường hợp B: Đăng ký user mới
                elif len(parts) >= 5:
                    _, user, pwd, fname, mail = parts[:5]
                    print(f"[Auth] Registering: {user}")
                    if auth_sign_up(user, pwd, fname, mail):
                        self._send_control_pdu(client_id, f"{CMD_REGISTER_OK}")
                    else:
                        self._send_control_pdu(client_id, f"{CMD_ERROR}:User đã tồn tại hoặc lỗi DB")
                else:
                    self._send_control_pdu(client_id, f"{CMD_ERROR}:Thiếu thông tin đăng ký")

            # 3. Xử lý Lấy danh sách (nếu Manager yêu cầu thủ công)
            elif msg == CMD_LIST_CLIENTS:
                if self.clients.get(client_id) == ROLE_MANAGER:
                    self._send_client_list(client_id)

            # 4. Xử lý Yêu cầu Kết nối (Manager -> Client)
            elif msg.startswith(CMD_CONNECT_CLIENT):
                # Format: "CONNECT:target_client_id"
                # Check quyền Manager
                if self.clients.get(client_id) != ROLE_MANAGER:
                    self._send_control_pdu(client_id, f"{CMD_ERROR}:Bạn không có quyền Manager")
                    return

                try:
                    target_username = msg.split(":", 1)[1].strip()
                    
                    # Tìm socket_id của client từ username
                    target_client_id = None
                    with self.lock:
                        for cid, username in self.authenticated_users.items():
                            if username == target_username and self.clients.get(cid) == ROLE_CLIENT:
                                target_client_id = cid
                                break
                    
                    # Nếu tìm thấy client online, dùng socket_id. Nếu không, dùng username cho pending
                    if target_client_id:
                        self._attempt_start_session(manager_id=client_id, client_id=target_client_id)
                    else:
                        # Client chưa online - lưu pending request với username
                        with self.lock:
                            print(f"[Session] Client {target_username} not online yet. Saving pending request from Manager {client_id}")
                            self.pending_requests[target_username] = client_id
                            # Gửi thông báo cho Manager biết đang chờ
                            self._send_control_pdu(client_id, f"{CMD_SESSION_STARTED}:{target_username}")
                except IndexError:
                    pass

        except Exception as e:
            print(f"[SessionManager] Logic Error: {e}")

    # =========================================================================
    # SESSION & HELPER METHODS
    # =========================================================================
    # Cố gắng bắt đầu một phiên Remote Desktop
    def _attempt_start_session(self, manager_id, client_id):
        with self.lock:
            # Kiểm tra trạng thái các bên (client_id ở đây là socket_id)
            if client_id not in self.clients:
                self._send_control_pdu(manager_id, f"{CMD_ERROR}:Client không tồn tại")
                return
            if client_id in self.client_session_map:
                self._send_control_pdu(manager_id, f"{CMD_ERROR}:Client đang bận")
                return
            if manager_id in self.client_session_map:
                self._send_control_pdu(manager_id, f"{CMD_ERROR}:Bạn đang trong phiên khác")
                return
        print(f"[Session] Starting: Manager({manager_id}) <-> Client({client_id})")
        
        # Tạo Session Object
        session = ServerSession(manager_id, client_id, self.broadcaster, self._on_session_done_callback)
        session.start()

        with self.lock:
            self.active_sessions[session.session_id] = session
            self.client_session_map[manager_id] = session
            self.client_session_map[client_id] = session

        # Gửi thông báo SESSION_STARTED cho cả 2 để Client bắt đầu gửi ảnh
        self._send_control_pdu(manager_id, f"{CMD_SESSION_STARTED}:{client_id}")
        self._send_control_pdu(client_id, f"{CMD_SESSION_STARTED}:{manager_id}")
        
        # Cập nhật danh sách (Client này giờ đã bận)
        self._broadcast_client_list()

    # Được gọi từ bên trong ServerSession khi phiên kết thúc
    def _on_session_done_callback(self, session, reason):
        print(f"[Session] Closed {session.session_id}: {reason}")
        
        with self.lock:
            self.active_sessions.pop(session.session_id, None)
            self.client_session_map.pop(session.manager_id, None)
            self.client_session_map.pop(session.client_id, None)

        # Thông báo cho 2 bên
        self._send_control_pdu(session.manager_id, f"{CMD_SESSION_ENDED}:{session.client_id}")
        self._send_control_pdu(session.client_id, f"{CMD_SESSION_ENDED}:{session.manager_id}")
        
        # Client rảnh trở lại -> Cập nhật list
        self._broadcast_client_list()

    # Lấy danh sách các Client đang rảnh
    def _get_available_clients(self):
        available = []
        with self.lock:
            for cid, role in self.clients.items():
                # Điều kiện: Là client và chưa vào Session nào và đã login 
                if role == ROLE_CLIENT and cid not in self.client_session_map:
                    username = self.authenticated_users.get(cid, "Unknown")
                    # Lấy IP từ broadcaster
                    ip = "Unknown"
                    try:
                        sock = self.broadcaster.get_socket(cid)
                        if sock:
                            ip = sock.getpeername()[0]
                    except Exception as e:
                        # Không lấy được IP thì thôi
                        pass
                    # Dùng username làm 'id' để Manager có thể gửi CONNECT:username
                    available.append({"id": username, "name": username, "ip": ip})
        return available

    # Gửi danh sách Client cho 1 Manager cụ thể
    def _send_client_list(self, manager_id):
        data = self._get_available_clients()
        json_str = json.dumps(data)
        self._send_control_pdu(manager_id, f"{CMD_CLIENT_LIST_UPDATE}:{json_str}")

    # Gửi danh sách Client cho tất cả Manager
    def _broadcast_client_list(self):
        data = self._get_available_clients()
        print(f"[SessionManager] 📢 Broadcasting client list: {data}")  # DEBUG
        json_str = json.dumps(data)
        msg = f"{CMD_CLIENT_LIST_UPDATE}:{json_str}"
        
        with self.lock:
            managers = [cid for cid, role in self.clients.items() if role == ROLE_MANAGER]
        
        print(f"[SessionManager] Sending to {len(managers)} manager(s): {managers}")  # DEBUG
        for mid in managers:
            self._send_control_pdu(mid, msg)

    # Helper để đóng gói và gửi tin nhắn Control
    def _send_control_pdu(self, target_id, message: str):
        seq = self._next_seq()
        pdu_bytes = self.builder.build_control_pdu(seq, message.encode())
        mcs_frame = MCSLite.build(CHANNEL_CONTROL, pdu_bytes)
        self.broadcaster.enqueue(target_id, mcs_frame)  # Dùng enqueue, không phải send_to_client
    
    # [THÊM] Xử lý INPUT PDU (keylog) - Lưu DB và forward tới manager
    def _handle_input_pdu(self, client_id, pdu):
        """Xử lý keylog data từ client: lưu database và forward tới manager"""
        try:
            input_data = pdu.get('input')
            if not input_data or not isinstance(input_data, dict):
                print(f"[SessionManager] INPUT PDU không hợp lệ từ {client_id}")
                return
            
            # Lấy thông tin keylog
            key_data = input_data.get('KeyData', '')
            window_title = input_data.get('WindowTitle', 'Unknown')
            client_username = input_data.get('ClientID', client_id)
            logged_at = input_data.get('LoggedAt', '')
            
            print(f"[SessionManager] 📝 Keylog từ {client_username}: '{key_data[:20]}...' @ {window_title}")
            
            # 1. Lưu vào database
            if KEYLOG_DB_AVAILABLE:
                try:
                    success = create_keystroke(key_data, window_title, client_username)
                    if success:
                        print(f"[SessionManager] ✅ Đã lưu keylog vào DB")
                    else:
                        print(f"[SessionManager] ⚠️ Không thể lưu keylog vào DB")
                except Exception as db_err:
                    print(f"[SessionManager] ❌ Lỗi DB: {db_err}")
            
            # 2. Forward tới tất cả Manager đang online
            with self.lock:
                managers = [cid for cid, role in self.clients.items() if role == ROLE_MANAGER]
            
            if managers:
                # Rebuild INPUT PDU để gửi
                raw_payload = pdu.get('_raw_payload')
                if raw_payload:
                    # Gửi raw PDU (đã có đầy đủ header)
                    mcs_frame = MCSLite.build(CHANNEL_INPUT, raw_payload)
                    for manager_id in managers:
                        self.broadcaster.enqueue(manager_id, mcs_frame)  # Dùng enqueue
                    print(f"[SessionManager] 📤 Đã forward keylog tới {len(managers)} manager(s)")
                else:
                    print(f"[SessionManager] ⚠️ Không có raw_payload để forward")
            else:
                print(f"[SessionManager] ℹ️ Không có manager online để nhận keylog")
                
        except Exception as e:
            print(f"[SessionManager] ❌ Lỗi xử lý INPUT PDU: {e}")
            import traceback
            traceback.print_exc()