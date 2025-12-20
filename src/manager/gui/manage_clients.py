# src/gui/manage_client.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QSplitter, QListWidget, QLabel,
    QTextEdit, QPushButton, QFormLayout
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
        actions = ["Keylogger", "Screen", "Control", "File Transfer", "All History"]
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
            }}
        """)
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
        token = QApplication.instance().client_connected[index][1]
        
        # Kiểm tra xem có auth connection không
        conn = QApplication.instance().conn
        if conn:
            try:
                data = conn.client_profile(token)
                status = conn.check_connected_status(token, QApplication.instance().current_user)
            except Exception as e:
                print(f"Lỗi khi lấy thông tin client: {e}")
                data = None
                status = "unknown"
        else:
            # Không có auth service, hiển thị thông tin cơ bản
            data = None
            status = "connected"
        
        if data:
            self.lbl_username.setText(name)
            self.lbl_email.setText(data[4])
            self.lbl_fullname.setText(data[3])
            if status.lower() == "connected":
                self.lbl_status.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {SPOTIFY_GREEN};")
            else:
                 self.lbl_status.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: gray;")
            self.lbl_status.setText(f"Status: {status}")
        else:
            # Hiển thị thông tin cơ bản từ client_connected
            self.lbl_username.setText(name)
            self.lbl_email.setText("N/A")
            self.lbl_fullname.setText("N/A")
            self.lbl_status.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {SPOTIFY_GREEN};")
            self.lbl_status.setText(f"Status: {status}")

    def open_add_client(self):
        from src.gui.add_client import AddClientWindow  
        self.add_client_window = AddClientWindow()
        self.add_client_window.show()
        self.close()
            
    def view_screen(self):
        """Mở màn hình xem client - LOGIC MỚI theo 4 trường hợp"""
        if not self.selected_client_id:
            print(f"[ManageClientsWindow] Chưa chọn client nào!")
            return
        
        print(f"[ManageClientsWindow] Mở màn hình cho client: {self.selected_client_id}")
        
        # Lấy manager logic
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
        manager = QApplication.instance().manager_logic
        if manager:
            manager.gui_disconnect_session()
    
    def _on_screen_close(self):
        """Handle close button (X) - Đóng window VÀ disconnect"""
        print(f"[ManageClientsWindow] Screen window bị đóng")
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
            
# def main():
#     app = QApplication(sys.argv)
#     app.setFont(QFont("Segoe UI", 10))
#     win = ManageClientsWindow()
#     win.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
