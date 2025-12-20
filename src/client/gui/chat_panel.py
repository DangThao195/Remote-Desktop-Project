"""
Chat Panel - Manages chat interface and functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from .components import (
    StyledButton, StyledLabel, StyledLineEdit, 
    StyledTextEdit, PanelFrame, StatusLabel
)


class ChatPanel(QWidget):
    """Panel for chat functionality"""
    
    # Signals
    message_sent = pyqtSignal(str)  # Emits message to be sent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize chat panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = StyledLabel("Chat", style_type="title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Chat history display
        self.chat_history = StyledTextEdit(read_only=True)
        self.chat_history.setMinimumHeight(300)
        layout.addWidget(self.chat_history)
        
        # Input section
        input_layout = QHBoxLayout()
        
        self.message_input = StyledLineEdit("Nhập tin nhắn...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, stretch=1)
        
        self.send_button = StyledButton("Gửi", style_type="primary")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setFixedWidth(100)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Status label
        self.status_label = StatusLabel()
        layout.addWidget(self.status_label)
    
    def send_message(self):
        """Handle sending message"""
        message = self.message_input.text().strip()
        if not message:
            self.status_label.show_warning("Vui lòng nhập tin nhắn!")
            return
        
        # Add to chat history
        self.add_message("Bạn", message)
        
        # Clear input
        self.message_input.clear()
        
        # Emit signal
        self.message_sent.emit(message)
    
    def add_message(self, sender, message):
        """Add message to chat history"""
        self.chat_history.append(f"<b>{sender}:</b> {message}")
    
    def add_system_message(self, message):
        """Add system message to chat history"""
        self.chat_history.append(f"<i style='color: #888;'>[Hệ thống] {message}</i>")
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history.clear()
        self.status_label.show_normal("Đã xóa lịch sử chat")
    
    def set_enabled(self, enabled):
        """Enable or disable chat controls"""
        self.message_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        
        if not enabled:
            self.status_label.show_warning("Chưa kết nối đến server")
        else:
            self.status_label.show_success("Đã kết nối")
