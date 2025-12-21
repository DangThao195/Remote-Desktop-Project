# src/gui/manage_client.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QSplitter, QListWidget, QLabel,
    QTextEdit, QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.gui.ui_components import (
    SPOTIFY_GREEN, DARK_BG, CARD_BG, TEXT_LIGHT, SUBTEXT,
    create_back_button, create_search_bar, create_client_list
)


class ManageClientsWindow(QWidget):
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    input_event_generated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.selected_client_id = None
        self.setWindowTitle("Server Control Panel")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_LIGHT};")
        self.init_ui()
        
        # Kết nối signals từ manager sẽ được gọi sau khi window hiển thị
        # Dùng QTimer để delay cho đến khi manager_logic đã được khởi tạo
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._connect_manager_signals)  # Delay 100ms
    
    def _connect_manager_signals(self):
        """Kết nối signals từ manager logic để nhận keylog và security alerts"""
        try:
            manager = QApplication.instance().manager_logic
            if manager:
                # Nhận keylog data liên tục
                manager.input_pdu_received.connect(self.display_keylog)
                # Nhận security alerts liên tục
                manager.security_alert_received.connect(self.display_security_alert)
                print("[ManageClientsWindow] Đã kết nối signals để nhận keylog và security alerts liên tục")
            else:
                print("[ManageClientsWindow] WARN: manager_logic chưa sẵn sàng, thử lại sau...")
                # Thử lại sau 500ms
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(500, self._connect_manager_signals)
        except AttributeError:
            print("[ManageClientsWindow] WARN: manager_logic chưa tồn tại, thử lại sau...")
            # Thử lại sau 500ms
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, self._connect_manager_signals)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # ==== Thanh top: Back + Add Client ====
        top_bar = QHBoxLayout()
        self.back_btn = create_back_button()
        search_user_box, self.search_user = create_search_bar("Search client by username or IP")
        top_bar.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        top_bar.addStretch()

        top_bar.addWidget(search_user_box)

        main_layout.addLayout(top_bar)

        # ==== Splitter trái/phải ====
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # ---------- BÊN TRÁI ----------
        sidebar = QFrame()
        sidebar.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 6px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        lbl_clients = QLabel("Clients")
        lbl_clients.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sidebar_layout.addWidget(lbl_clients)

        self.client_list = QListWidget()
        self.client_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {DARK_BG};
                border-radius: 6px;
                padding: 4px;
                font-size: 11pt;
                color: {TEXT_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {SPOTIFY_GREEN};
                color: black;
                border-radius: 4px;
            }}
        """)
        for name in QApplication.instance().client_connected:
            self.client_list.addItem(name[0])

        add_btn = QPushButton("Add Client")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SPOTIFY_GREEN};
                color: black;
                border-radius: 10px;
                padding: 6px 14px;
                font-weight: bold;
                margin-top: 16px;
            }}
            QPushButton:hover {{
                opacity: 0.85;
            }}
        """)
        add_btn.clicked.connect(self.open_add_client)
        
        self.client_list.currentRowChanged.connect(self.show_client_info)
        self.client_list.itemClicked.connect(
            lambda item: self.show_client_info(self.client_list.row(item))
        )

        sidebar_layout.addWidget(self.client_list, stretch=1)
        sidebar_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        # Biến tracking cho keylogger mode
        self.keylogger_active = False  # Có đang hiển thị keylogger hay không
        self.session_keylog_buffer = []  # Buffer keylog trong session hiện tại

        # Khu vực thông tin chi tiết client
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet(f"background-color: {DARK_BG}; border-radius: 8px;")
        info_layout = QFormLayout(self.info_frame)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(6)
        self.lbl_username = QLabel("-")
        self.lbl_email = QLabel("-")
        self.lbl_fullname = QLabel("-")

        for lbl in [self.lbl_username, self.lbl_email, self.lbl_fullname]:
            lbl.setStyleSheet(f"color: {TEXT_LIGHT}; font-size: 10pt;")

        info_layout.addRow("Username:", self.lbl_username)
        info_layout.addRow("Email:", self.lbl_email)
        info_layout.addRow("IP:", self.lbl_fullname)
        sidebar_layout.addWidget(self.info_frame)

        # Label trạng thái ngay dưới khung info
        self.lbl_status = QLabel("Status: -")
        self.lbl_status.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {SUBTEXT};")
        sidebar_layout.addWidget(self.lbl_status)

        splitter.addWidget(sidebar)

        # ---------- BÊN PHẢI ----------
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(12)

        self.server_ip_label = QLabel("Server IP: 192.168.1.1")
        self.server_ip_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        right_layout.addWidget(self.server_ip_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn_layout = QHBoxLayout()
        actions = ["Keylogger", "Security Alerts", "Screen", "Control", "File Transfer"]
        self.buttons = {}
        for act in actions:
            btn = QPushButton(act)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SPOTIFY_GREEN};
                    color: black;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.85;
                }}
            """)
            self.buttons[act] = btn
            btn_layout.addWidget(btn)
        right_layout.addLayout(btn_layout)

        # Connect signals
        self.buttons["Screen"].clicked.connect(self.view_screen)
        self.buttons["Keylogger"].clicked.connect(self.view_keylogger)
        self.buttons["Security Alerts"].clicked.connect(self.view_security_alerts)

        self.action_area = QTextEdit()
        self.action_area.setPlaceholderText("Action output will appear here...")
        self.action_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {CARD_BG};
                border: 1px solid {SUBTEXT};
                border-radius: 8px;
                color: {TEXT_LIGHT};
                padding: 8px;
                font-size: 11pt;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
        """)
        self.action_area.setReadOnly(True)
        right_layout.addWidget(self.action_area, stretch=1)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        # Dữ liệu giả lập thông tin client
        # self.client_data = {
        #     "Alice": {"email": "alice@example.com", "ip": "192.168.1.5", "status": "Connected"},
        #     "Bob": {"email": "bob@example.com", "ip": "192.168.1.8", "status": "Not connect"},
        #     "Charlie": {"email": "charlie@example.com", "ip": "192.168.1.12", "status": "Connected"},
        #     "David": {"email": "david@example.com", "ip": "192.168.1.20", "status": "Not connect"},
        # }

        self.back_btn.clicked.connect(self.open_server_gui)

    def open_server_gui(self):
        from src.gui.server_gui import ServerWindow
        self.server_gui = ServerWindow()
        self.server_gui.show()
        self.close()

    def show_client_info(self, index):
        if index < 0:
            self.lbl_username.setText("-")
            self.lbl_email.setText("-")
            self.lbl_fullname.setText("-")
            self.lbl_status.setText("Status: -")
            self.selected_client_id = None
            return

        # Text dạng: "username (IP)" -> Tách ra lấy username
        display_text = self.client_list.item(index).text()
        if '(' in display_text:
            name = display_text.split('(')[0].strip()
        else:
            name = display_text
        self.selected_client_id = name
        
        # CHECK MAIN SERVER STATUS - Kiểm tra client có trong manager.client_list không
        manager = QApplication.instance().manager_logic
        is_connected_to_main_server = False
        
        if manager and manager.client_list:
            # Kiểm tra xem client có trong danh sách từ Main Server không
            for client in manager.client_list:
                if client['id'] == name or client.get('name') == name:
                    is_connected_to_main_server = True
                    print(f"[ManageClientsWindow] ✅ Client {name} đã kết nối Main Server!")
                    break
        
        print(f"[ManageClientsWindow] Client {name} connected to Main Server: {is_connected_to_main_server}")
        print(f"[ManageClientsWindow] Current client_list from server: {manager.client_list if manager else 'No manager'}")
        
        # Kiểm tra index có hợp lệ không (tránh IndexError khi client disconnect)
        client_connected_list = QApplication.instance().client_connected
        if index >= len(client_connected_list):
            print(f"[WARN] Client index {index} out of range. Client đã disconnect.")
            self.lbl_username.setText(name)
            self.lbl_email.setText("N/A")
            self.lbl_fullname.setText("N/A")
            self.lbl_status.setStyleSheet("font-size: 11pt; font-weight: bold; color: gray;")
            self.lbl_status.setText("Status: Disconnected")
            return
            
        token = client_connected_list[index][1]
        
        # Lấy thông tin profile từ Auth Server
        conn = QApplication.instance().conn
        data = None
        if conn:
            try:
                data = conn.client_profile(token)
            except Exception as e:
                print(f"Lỗi khi lấy thông tin client: {e}")
                data = None
        
        # Hiển thị thông tin
        if data:
            self.lbl_username.setText(name)
            self.lbl_email.setText(data[4])
            self.lbl_fullname.setText(data[3])
        else:
            # Không có profile từ Auth Server
            self.lbl_username.setText(name)
            self.lbl_email.setText("N/A")
            self.lbl_fullname.setText("N/A")
        
        # Status dựa trên Main Server connection, KHÔNG phải Auth Server
        if is_connected_to_main_server:
            self.lbl_status.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {SPOTIFY_GREEN};")
            self.lbl_status.setText("Status: connected")
        else:
            self.lbl_status.setStyleSheet("font-size: 11pt; font-weight: bold; color: gray;")
            self.lbl_status.setText("Status: no connected")

    def open_add_client(self):
        from src.gui.add_client import AddClientWindow  
        self.add_client_window = AddClientWindow()
        self.add_client_window.show()
        self.close()
            
    def view_screen(self):
        """Mở màn hình xem client - LOGIC MỚI theo 4 trường hợp"""
        if not self.selected_client_id:
            print(f"[ManageClientsWindow] Chưa chọn client nào!")
            QMessageBox.warning(self, "No Client Selected", "Please select a client first!")
            return
        
        print(f"[ManageClientsWindow] Mở màn hình cho client: {self.selected_client_id}")
        
        # Lấy manager logic
        manager = QApplication.instance().manager_logic
        if not manager:
            print(f"[ManageClientsWindow] LỖI: Không tìm thấy manager_logic!")
            return
        
        # Kiểm tra client có trong danh sách từ server không (manager.client_list)
        print(f"[ManageClientsWindow] Danh sách client từ server: {manager.client_list}")
        client_ids = [c['id'] for c in manager.client_list]
        if self.selected_client_id not in client_ids:
            print(f"[ManageClientsWindow] Client {self.selected_client_id} không có trong danh sách rảnh từ server!")
            print(f"[ManageClientsWindow] Available clients: {client_ids}")
            QMessageBox.warning(self, "Client Not Available", 
                              f"Client '{self.selected_client_id}' is not available. It may be disconnected or in another session.")
            return
        manager = QApplication.instance().manager_logic
        if not manager:
            print(f"[ManageClientsWindow] LỖI: Không tìm thấy manager_logic!")
            return
        
        # Nếu đã có screen window, chỉ hiện lại
        if hasattr(self, 'screen_window') and self.screen_window:
            print(f"[ManageClientsWindow] Screen window đã tồn tại, hiện lại")
            self.screen_window.show()
            self.screen_window.raise_()
            self.screen_window.activateWindow()
            return
        
        # Tạo window mới
        print(f"[ManageClientsWindow] Tạo screen window mới cho {self.selected_client_id}")
        from src.manager.gui.manage_screen import ManageScreenWindow
        self.screen_window = ManageScreenWindow(self.selected_client_id)
        
        # Connect signals
        print(f"[ManageClientsWindow] Kết nối signals với manager logic")
        self.screen_window.disconnect_requested.connect(self._on_screen_disconnect)
        self.screen_window.close_requested.connect(self._on_screen_close)
        self.screen_window.input_event_generated.connect(manager._on_gui_input)
        
        manager.session_started.connect(self.screen_window.set_session_started)
        manager.session_ended.connect(self.screen_window.set_session_ended)
        manager.video_pdu_received.connect(self.screen_window.update_video_frame)
        manager.cursor_pdu_received.connect(self.screen_window.update_cursor_pos)
        manager.error_received.connect(self.screen_window.show_error)
        
        self.screen_window.show()
        
        # Gửi yêu cầu connect nếu chưa có session
        if not manager.current_session_client_id:
            print(f"[ManageClientsWindow] Gửi yêu cầu connect tới {self.selected_client_id}")
            manager.gui_connect_to_client(self.selected_client_id)
        else:
            print(f"[ManageClientsWindow] Đã có session với {manager.current_session_client_id}")
        
        # QUAN TRỌNG: Không đóng ManageClientsWindow để giữ kết nối
        # self.close()  # KHÔNG được đóng window này!
    
    def _on_screen_disconnect(self):
        """Handle disconnect button click - CHỈ disconnect session, GIỮ window"""
        print(f"[ManageClientsWindow] Screen window yêu cầu disconnect (GIỮ window)")
        
        # KHÔNG reset keylog buffer - vì keylog theo session của client, không theo screen session
        # Buffer chỉ reset khi client disconnect khỏi Main Server
        
        manager = QApplication.instance().manager_logic
        if manager:
            manager.gui_disconnect_session()
    
    def _on_screen_close(self):
        """Handle close button (X) - Đóng window VÀ disconnect"""
        print(f"[ManageClientsWindow] Screen window bị đóng")
        
        # KHÔNG reset keylog buffer - vì keylog theo session của client
        
        manager = QApplication.instance().manager_logic
        if manager and manager.current_session_client_id:
            print(f"[ManageClientsWindow] Auto disconnect do window đóng")
            manager.gui_disconnect_session()
        
        # Cleanup
        if hasattr(self, 'screen_window'):
            self.screen_window = None
            
    def update_client_list(self, client_list: list):
        """Update the client list from manager logic"""
        print(f"[ManageClientsWindow] Cập nhật danh sách client: {client_list}")
        try:
            self.client_list.clear()
            # Lưu client_list để search
            self.full_client_list = client_list
            
            for client in client_list:
                # Hiển thị: username (IP)
                client_id = client['id']
                client_ip = client.get('ip', 'Unknown')
                display_text = f"{client_id} ({client_ip})"
                self.client_list.addItem(display_text)
                
            # Update app.client_connected with dummy tokens
            app = QApplication.instance()
            app.client_connected = [(client['id'], "dummy_token") for client in client_list]
            
            # Connect search
            if not hasattr(self, '_search_connected'):
                self.search_user.textChanged.connect(self.filter_clients)
                self._search_connected = True
        except Exception as e:
            print(f"[ManageClientsWindow] LỖI khi cập nhật danh sách client: {e}")
            import traceback
            traceback.print_exc()
    
    def filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_user.text().lower()
        self.client_list.clear()
        
        if not hasattr(self, 'full_client_list'):
            return
            
        for client in self.full_client_list:
            client_id = client['id']
            client_ip = client.get('ip', 'Unknown')
            display_text = f"{client_id} ({client_ip})"
            
            # Search by username OR IP
            if search_text in client_id.lower() or search_text in client_ip.lower():
                self.client_list.addItem(display_text)
        
    def set_session_started(self, client_id: str):
        """Called when session starts"""
        self.action_area.append(f"Session started with {client_id}")
        
    def set_session_ended(self):
        """Called when session ends"""
        self.action_area.append("Session ended")
        
    def update_video_frame(self, image):
        """Update video frame - placeholder for now"""
        pass
        
    def update_cursor_pos(self, cursor_data):
        """Update cursor position - placeholder for now"""
        pass
        
    def show_error(self, error_msg: str):
        """Show error message"""
        self.action_area.append(f"Error: {error_msg}")
    
    def view_keylogger(self):
        """Bật hiển thị keylogger logs - hiển thị khi client đã bắt đầu dịch vụ"""
        if not self.selected_client_id:
            self.action_area.clear()
            self.action_area.append("⚠️ Vui lòng chọn client trước!")
            return
        
        # Bật keylogger mode
        self.keylogger_active = True
        self.action_area.clear()
        
        # Kiểm tra xem client có đang online (đã bắt đầu dịch vụ) không
        manager = QApplication.instance().manager_logic
        client_online = False
        
        if manager and manager.client_list:
            # Check xem client có trong danh sách từ Main Server không
            for client in manager.client_list:
                if client['id'] == self.selected_client_id or client.get('name') == self.selected_client_id:
                    client_online = True
                    break
        
        keyboard_icon = "\u2328\ufe0f"  # Emoji ⌨️
        
        if client_online:
            # Client đã bắt đầu dịch vụ - hiển thị keylog buffer
            html_content = f"""
                <div style='border-bottom: 2px solid {SPOTIFY_GREEN}; padding-bottom: 10px; margin-bottom: 10px;'>
                    <h3 style='color: {SPOTIFY_GREEN}; margin: 5px 0;'>{keyboard_icon} KEYLOGGER - {self.selected_client_id}</h3>
                    <p style='color: {SUBTEXT}; margin: 5px 0; font-size: 10pt;'>Trạng thái: <b style='color: {SPOTIFY_GREEN};'>Đang theo dõi...</b></p>
                </div>
                <div style='color: {TEXT_LIGHT}; font-size: 10pt; margin: 10px 0;'>
                    Lịch sử gõ phím từ khi client bắt đầu dịch vụ:
                </div>
            """
            self.action_area.setHtml(html_content)
            
            # Hiển thị buffer hiện tại (nếu có)
            for log_entry in self.session_keylog_buffer:
                self.action_area.append(log_entry)
        else:
            # Client chưa bắt đầu dịch vụ
            html_content = f"""
                <div style='border-bottom: 2px solid {SUBTEXT}; padding-bottom: 10px; margin-bottom: 10px;'>
                    <h3 style='color: {SUBTEXT}; margin: 5px 0;'>{keyboard_icon} KEYLOGGER - {self.selected_client_id}</h3>
                    <p style='color: {SUBTEXT}; margin: 5px 0; font-size: 10pt;'>Trạng thái: <b style='color: orange;'>Chờ client bắt đầu dịch vụ...</b></p>
                </div>
                <div style='color: {SUBTEXT}; font-size: 10pt; margin: 10px 0; text-align: center; padding: 20px;'>
                    ⚠️ Client chưa bắt đầu dịch vụ.<br>
                    Keylogger sẽ tự động hiển thị khi client bấm <b>"Bắt đầu dịch vụ"</b>.
                </div>
            """
            self.action_area.setHtml(html_content)
    
    def view_security_alerts(self):
        """Hiển thị thông báo vi phạm bảo mật từ client"""
        if not self.selected_client_id:
            self.action_area.append("⚠️ Vui lòng chọn client trước!")
            return
        
        self.action_area.clear()
        alert_icon = "\U0001F6A8"  # Emoji 🚨
        html_content = f"""
            <div style='border-bottom: 2px solid #FF4444; padding-bottom: 10px; margin-bottom: 10px;'>
                <h2 style='color: #FF4444; margin: 5px 0;'>{alert_icon} THÔNG BÁO VI PHẠM BẢO MẬT</h2>
                <p style='color: {SUBTEXT}; margin: 5px 0;'>Client: <b style='color: {TEXT_LIGHT};'>{self.selected_client_id}</b></p>
                <p style='color: {SUBTEXT}; margin: 5px 0;'>Trạng thái: <b style='color: #FF4444;'>Đang giám sát...</b></p>
            </div>
            <p style='color: {SUBTEXT}; font-style: italic;'>Cảnh báo vi phạm sẽ hiển thị bên dưới:</p>
        """
        self.action_area.setHtml(html_content)
        
    def display_keylog(self, pdu: dict):
        """Hiển thị keylog data - hiển thị khi client online, không cần screen session"""
        try:
            # Chỉ hiển thị nếu keylogger mode đang bật
            if not self.keylogger_active:
                return
            
            # INPUT PDU format: {"type": "input", "input": {KeyData, WindowTitle, ...}, "message": ...}
            input_data = pdu.get('input')  # Dict đã được parse từ JSON
            message = pdu.get('message', '')
            
            # Debug log
            print(f"[display_keylog] Nhận PDU: type={pdu.get('type')}, input={input_data}, message={message[:50] if message else 'None'}...")
            
            # Nếu là security alert thì bỏ qua
            if isinstance(message, str) and message.startswith('security_alert:'):
                return
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Xử lý keylog data từ dict input
            if input_data and isinstance(input_data, dict):
                key_data = input_data.get('KeyData', '')
                window_title = input_data.get('WindowTitle', 'Unknown')
                client_id = input_data.get('ClientID', 'Unknown')
                logged_at = input_data.get('LoggedAt', timestamp)
                
                # Chỉ hiển thị nếu là từ client đang được chọn
                if self.selected_client_id and client_id != self.selected_client_id:
                    print(f"[display_keylog] Bỏ qua keylog từ {client_id}, đang chọn {self.selected_client_id}")
                    return
                
                # Format đơn giản như chat log - chỉ hiển thị timestamp và text
                log_html = f"""
                <div style='margin: 3px 0; padding: 5px 8px;'>
                    <span style='color: {SUBTEXT}; font-size: 9pt;'>[{logged_at}]</span>
                    <span style='color: {TEXT_LIGHT}; font-family: monospace; margin-left: 8px;'>{key_data}</span>
                </div>
                """
                
                # Thêm vào buffer
                self.session_keylog_buffer.append(log_html)
                
                # Hiển thị
                self.action_area.append(log_html)
                print(f"[display_keylog] ✅ Hiển thị keylog: {key_data[:20]}...")
            
            else:
                # Không có input data
                print(f"[display_keylog] ⚠️ Không tìm thấy input data trong PDU")
            
            # Auto scroll to bottom
            scrollbar = self.action_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"[ManageClientsWindow] Lỗi hiển thị keylog: {e}")
            import traceback
            traceback.print_exc()
    
    def display_security_alert(self, pdu: dict):
        """Hiển thị cảnh báo vi phạm từ client"""
        try:
            message = pdu.get('message', '')
            
            # Parse security_alert message
            # Format: "security_alert:Loại vi phạm|Chi tiết"
            if message.startswith('security_alert:'):
                content = message.split(':', 1)[1]
                if '|' in content:
                    violation_type, detail = content.split('|', 1)
                else:
                    violation_type = 'General'
                    detail = content
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Ghi vào file log
                self._write_violation_log(timestamp, self.selected_client_id or 'Unknown', violation_type, detail)
                
                # HTML formatted alert
                alert_html = f"""
                <div style='background-color: rgba(255,0,0,0.15); 
                            padding: 10px; 
                            margin: 8px 0; 
                            border-left: 4px solid #FF4444;
                            border-radius: 6px;'>
                    <div style='color: #FF4444; font-weight: bold; font-size: 12pt;'>
                        🚨 CẢNH BÁO VI PHẠM [{timestamp}]
                    </div>
                    <div style='color: {TEXT_LIGHT}; margin: 8px 0;'>
                        👤 <b>Client:</b> {self.selected_client_id or 'Unknown'}
                    </div>
                    <div style='color: #FFA500; margin: 8px 0;'>
                        ⚠️ <b>Loại vi phạm:</b> {violation_type}
                    </div>
                    <div style='color: {TEXT_LIGHT}; font-family: monospace; margin: 8px 0; padding: 8px; background-color: rgba(0,0,0,0.4); border-radius: 4px;'>
                        📋 <b>Chi tiết:</b><br/>
                        {detail}
                    </div>
                </div>
                """
                self.action_area.append(alert_html)
                
                # Auto scroll to bottom
                scrollbar = self.action_area.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
                print(f"[ManageClientsWindow] 🚨 Hiển thị cảnh báo vi phạm: {violation_type} - {detail}")
        except Exception as e:
            print(f"[ManageClientsWindow] Lỗi hiển thị security alert: {e}")
            import traceback
            traceback.print_exc()
    
    def _write_violation_log(self, timestamp, client_id, violation_type, detail):
        """Ghi log vi phạm vào file"""
        try:
            import os
            from datetime import datetime
            
            # Tạo thư mục logs nếu chưa có
            log_dir = "log"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Tên file: violations_YYYY-MM-DD.log
            log_filename = f"{log_dir}/violations_{datetime.now().strftime('%Y-%m-%d')}.log"
            
            # Ghi log
            log_entry = f"[{timestamp}] CLIENT: {client_id} | TYPE: {violation_type} | DETAIL: {detail}\n"
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            print(f"[ManageClientsWindow] ✅ Đã ghi log vi phạm vào file: {log_filename}")
        except Exception as e:
            print(f"[ManageClientsWindow] ❌ Lỗi ghi file log: {e}")
            
# def main():
#     app = QApplication(sys.argv)
#     app.setFont(QFont("Segoe UI", 10))
#     win = ManageClientsWindow()
#     win.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
