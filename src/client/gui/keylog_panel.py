"""
Keylogger Panel - Manages keylogger display and controls
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from .components import (
    StyledButton, StyledLabel, StyledLineEdit, 
    StyledTextEdit, PanelFrame, StatusLabel
)


class KeylogPanel(QWidget):
    """Panel for keylogger functionality"""
    
    # Signals
    start_keylog = pyqtSignal()  # Request to start keylogging
    stop_keylog = pyqtSignal()   # Request to stop keylogging
    clear_keylog = pyqtSignal()  # Request to clear keylog data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_logging = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize keylogger panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = StyledLabel("Keylogger", style_type="title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_button = StyledButton("Bắt Đầu Ghi", style_type="primary")
        self.start_button.clicked.connect(self.on_start_clicked)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = StyledButton("Dừng Ghi", style_type="danger")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        self.clear_button = StyledButton("Xóa Dữ Liệu", style_type="secondary")
        self.clear_button.clicked.connect(self.on_clear_clicked)
        control_layout.addWidget(self.clear_button)
        
        layout.addLayout(control_layout)
        
        # Keylog display
        keylog_label = StyledLabel("Phím Đã Ghi:", style_type="subtitle")
        layout.addWidget(keylog_label)
        
        self.keylog_display = StyledTextEdit(read_only=True)
        self.keylog_display.setMinimumHeight(350)
        layout.addWidget(self.keylog_display)
        
        # Statistics section
        stats_frame = PanelFrame()
        stats_layout = QHBoxLayout(stats_frame)
        
        self.stats_label = StyledLabel("Tổng phím: 0 | Đang ghi: Không")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_frame)
        
        # Status label
        self.status_label = StatusLabel()
        layout.addWidget(self.status_label)
        
        # Key count
        self.key_count = 0
    
    def on_start_clicked(self):
        """Handle start button click"""
        self.is_logging = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.show_success("Đang ghi phím...")
        self.update_stats()
        self.start_keylog.emit()
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        self.is_logging = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.show_warning("Đã dừng ghi phím")
        self.update_stats()
        self.stop_keylog.emit()
    
    def on_clear_clicked(self):
        """Handle clear button click"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn xóa toàn bộ dữ liệu keylog?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.keylog_display.clear()
            self.key_count = 0
            self.update_stats()
            self.status_label.show_normal("Đã xóa dữ liệu keylog")
            self.clear_keylog.emit()
    
    def add_key(self, key_text):
        """Add key to display"""
        self.keylog_display.append(key_text)
        self.key_count += 1
        self.update_stats()
    
    def add_keys(self, keys_text):
        """Add multiple keys to display"""
        lines = keys_text.split('\n')
        for line in lines:
            if line.strip():
                self.keylog_display.append(line)
                self.key_count += 1
        self.update_stats()
    
    def update_stats(self):
        """Update statistics display"""
        status = "Có" if self.is_logging else "Không"
        self.stats_label.setText(f"Tổng phím: {self.key_count} | Đang ghi: {status}")
    
    def set_enabled(self, enabled):
        """Enable or disable keylog controls"""
        if not enabled:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.status_label.show_warning("Chưa kết nối đến server")
        else:
            self.start_button.setEnabled(not self.is_logging)
            self.stop_button.setEnabled(self.is_logging)
            self.clear_button.setEnabled(True)
            if not self.is_logging:
                self.status_label.show_normal("Sẵn sàng")
