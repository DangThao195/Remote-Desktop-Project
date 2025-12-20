# src/manager/gui/manage_screen.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QPen, QPolygon, QMouseEvent, QKeyEvent, QCursor
from PIL.ImageQt import ImageQt

from src.gui.ui_components import (
    SPOTIFY_GREEN, DARK_BG, CARD_BG, TEXT_LIGHT, SUBTEXT
)


class ManageScreenWindow(QWidget):
    disconnect_requested = pyqtSignal()
    close_requested = pyqtSignal()
    input_event_generated = pyqtSignal(dict)

    def __init__(self, client_id: str):
        super().__init__()
        self.client_id = client_id
        self.setWindowTitle(f"Remote Desktop - {client_id}")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_LIGHT};")

        # Biến trạng thái
        self.current_client_id = None  # Chỉ set khi session thực sự bắt đầu
        self.client_pixmap = QPixmap()
        self.last_mouse_sent_time = 0
        self.current_cursor_norm_x = 0.5
        self.current_cursor_norm_y = 0.5

        # Tạo con trỏ ảo (giống con trỏ Windows thật)
        cursor_pixmap = QPixmap(24, 32)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Vẽ arrow cursor
        # Shadow/outline
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        arrow_points = [
            QPoint(2, 2), 
            QPoint(2, 24), 
            QPoint(8, 18), 
            QPoint(12, 28),
            QPoint(15, 26),
            QPoint(11, 16),
            QPoint(18, 16)
        ]
        painter.drawPolygon(QPolygon(arrow_points))
        
        # Inner white fill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        inner_points = [
            QPoint(3, 3), 
            QPoint(3, 22), 
            QPoint(8, 17), 
            QPoint(11, 25),
            QPoint(13, 24),
            QPoint(10, 16),
            QPoint(16, 16)
        ]
        painter.drawPolygon(QPolygon(inner_points))
        painter.end()
        self.cursor_pixmap_base = cursor_pixmap

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Top bar
        top_bar = QHBoxLayout()
        title = QLabel(f"Remote Desktop - {self.client_id}")
        title.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {TEXT_LIGHT};")
        top_bar.addWidget(title)

        top_bar.addStretch()

        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        disconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff4444;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: #ff6666;
            }}
            QPushButton:pressed {{
                background-color: #cc0000;
            }}
        """)
        disconnect_btn.clicked.connect(self._on_disconnect_click)
        top_bar.addWidget(disconnect_btn)

        main_layout.addLayout(top_bar)

        # Screen display area
        screen_frame = QFrame()
        screen_frame.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 8px;")
        screen_layout = QVBoxLayout(screen_frame)

        self.screen_label = QLabel("Connecting...")
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet(f"background-color: black; color: {TEXT_LIGHT}; border-radius: 6px;")
        self.screen_label.setMinimumSize(800, 600)

        # Bật MouseTracking cho Label
        self.screen_label.setMouseTracking(True)
        self.screen_label.installEventFilter(self)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Tạo cursor label
        self.cursor_label = QLabel(self.screen_label)
        self.cursor_label.setPixmap(self.cursor_pixmap_base)
        self.cursor_label.setFixedSize(24, 32)  # Khớp với size của cursor pixmap
        self.cursor_label.setStyleSheet("background-color: transparent;")
        self.cursor_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Không chặn mouse events
        self.cursor_label.raise_()  # Đưa lên phía trên
        self.cursor_label.hide()  # Ẩn ban đầu

        screen_layout.addWidget(self.screen_label)
        main_layout.addWidget(screen_frame)

    def update_video_frame(self, image):
        """Update video frame from client"""
        if image:
            # Convert PIL Image to QPixmap
            qt_image = ImageQt(image)
            pixmap = QPixmap.fromImage(qt_image)
            self.screen_label.setPixmap(pixmap.scaled(
                self.screen_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.client_pixmap = pixmap

            # Show cursor if we have video
            if not self.cursor_label.isVisible():
                self.cursor_label.show()

    def update_cursor_pos(self, cursor_data):
        """Update cursor position"""
        if not cursor_data:
            return

        x_norm = cursor_data.get('x', 0.5)
        y_norm = cursor_data.get('y', 0.5)

        self.current_cursor_norm_x = x_norm
        self.current_cursor_norm_y = y_norm

        # Update cursor position on screen
        screen_width = self.screen_label.width()
        screen_height = self.screen_label.height()

        if screen_width > 0 and screen_height > 0:
            cursor_x = int(x_norm * screen_width)
            cursor_y = int(y_norm * screen_height)

            # Offset để con trỏ ở đúng vị trí (tip của arrow)
            self.cursor_label.move(cursor_x - 2, cursor_y - 2)
            
            # Debug: In ra console
            print(f"[Cursor] x={cursor_x}, y={cursor_y}, norm=({x_norm:.3f}, {y_norm:.3f})")
            
            # Hiển thị con trỏ và đưa lên top
            if not self.cursor_label.isVisible():
                self.cursor_label.show()
                print("[Cursor] Showing cursor label")
            self.cursor_label.raise_()

    def eventFilter(self, obj, event):
        """Handle mouse and keyboard events on screen"""
        if obj == self.screen_label:
            if isinstance(event, QMouseEvent):
                return self.handle_mouse_event(event)
            elif isinstance(event, QKeyEvent):
                return self.handle_key_event(event)

        return super().eventFilter(obj, event)

    def handle_mouse_event(self, event: QMouseEvent):
        """Handle mouse events"""
        if not self.current_client_id:
            return False

        # Tính tọa độ normalized
        screen_width = self.screen_label.width()
        screen_height = self.screen_label.height()

        if screen_width == 0 or screen_height == 0:
            return False

        x_norm = event.position().x() / screen_width
        y_norm = event.position().y() / screen_height

        # Giới hạn trong khoảng 0-1
        x_norm = max(0, min(1, x_norm))
        y_norm = max(0, min(1, y_norm))

        event_dict = None
        
        if event.type() == QEvent.Type.MouseButtonPress:
            button_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle"
            }
            button = button_map.get(event.button())
            if button:
                event_dict = {
                    "type": "mouse_click",
                    "x_norm": x_norm,
                    "y_norm": y_norm,
                    "button": button,
                    "pressed": True
                }
                
        elif event.type() == QEvent.Type.MouseButtonRelease:
            button_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle"
            }
            button = button_map.get(event.button())
            if button:
                event_dict = {
                    "type": "mouse_click",
                    "x_norm": x_norm,
                    "y_norm": y_norm,
                    "button": button,
                    "pressed": False
                }
                
        elif event.type() == QEvent.Type.MouseMove:
            event_dict = {
                "type": "mouse_move",
                "x_norm": x_norm,
                "y_norm": y_norm
            }

        if event_dict:
            self.input_event_generated.emit(event_dict)

        return True

    def handle_key_event(self, event: QKeyEvent):
        """Handle keyboard events"""
        if not self.current_client_id:
            return False

        key_map = {
            Qt.Key.Key_Backspace: 'backspace',
            Qt.Key.Key_Tab: 'tab',
            Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Enter: 'enter',
            Qt.Key.Key_Shift: 'shift',
            Qt.Key.Key_Control: 'ctrl',
            Qt.Key.Key_Alt: 'alt',
            Qt.Key.Key_Escape: 'esc',
            Qt.Key.Key_Space: 'space',
            Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Home: 'home',
            Qt.Key.Key_End: 'end',
            Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Right: 'right',
            Qt.Key.Key_Down: 'down',
        }

        # Add F1-F12
        for i in range(1, 13):
            key_map[getattr(Qt.Key, f'Key_F{i}')] = f'f{i}'

        key = event.key()
        key_name = key_map.get(key, chr(key).lower() if key < 256 else "")

        if key_name:
            # Định dạng phù hợp với ClientInputHandler: key_press/key_release
            event_type = "key_press" if event.type() == QEvent.Type.KeyPress else "key_release"
            event_dict = {
                "type": event_type,
                "key": key_name
            }
            self.input_event_generated.emit(event_dict)
            return True

        return False

    def set_session_started(self, client_id: str):
        """Called when session starts"""
        print(f"[ManageScreenWindow] Session started: {client_id}")
        self.screen_label.setText(f"Connected to {client_id}")
        self.current_client_id = client_id

    def set_session_ended(self):
        """Called when session ends - VỀ TRẠNG THÁI CONNECTING, KHÔNG ĐÓNG WINDOW"""
        print(f"[ManageScreenWindow] Session ended - trở về Connecting...")
        self.screen_label.clear()
        self.screen_label.setText(f"Connecting to {self.client_id}...")
        self.current_client_id = None
        self.cursor_label.hide()
        self.client_pixmap = QPixmap()
        # KHÔNG đóng window!
        # self.close()
    
    def _on_disconnect_click(self):
        """Handle disconnect button click"""
        print(f"[ManageScreenWindow] Disconnect button clicked")
        self.disconnect_requested.emit()
    
    def closeEvent(self, event):
        """Handle window close event (X button)"""
        print(f"[ManageScreenWindow] Window đang bị đóng")
        self.close_requested.emit()
        event.accept()

    def show_error(self, error_msg: str):
        """Show error message"""
        self.screen_label.setText(f"Error: {error_msg}")