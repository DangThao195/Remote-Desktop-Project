"""
Reusable UI Components for Client GUI
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFrame, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap


class StyledButton(QPushButton):
    """Custom styled button with consistent appearance"""
    
    def __init__(self, text, parent=None, style_type="primary"):
        super().__init__(text, parent)
        self.style_type = style_type
        self.apply_style()
    
    def apply_style(self):
        """Apply button style based on type"""
        if self.style_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        elif self.style_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a6dc2;
                }
            """)
        elif self.style_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #c2160a;
                }
            """)


class StyledLabel(QLabel):
    """Custom styled label"""
    
    def __init__(self, text, parent=None, style_type="normal"):
        super().__init__(text, parent)
        self.style_type = style_type
        self.apply_style()
    
    def apply_style(self):
        """Apply label style based on type"""
        if self.style_type == "title":
            font = QFont("Arial", 16, QFont.Weight.Bold)
            self.setFont(font)
            self.setStyleSheet("color: #333; padding: 10px;")
        elif self.style_type == "subtitle":
            font = QFont("Arial", 12, QFont.Weight.Bold)
            self.setFont(font)
            self.setStyleSheet("color: #555; padding: 5px;")
        else:
            self.setStyleSheet("color: #666; padding: 5px;")


class StyledLineEdit(QLineEdit):
    """Custom styled line edit"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.apply_style()
    
    def apply_style(self):
        """Apply line edit style"""
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)


class StyledTextEdit(QTextEdit):
    """Custom styled text edit"""
    
    def __init__(self, parent=None, read_only=False):
        super().__init__(parent)
        self.setReadOnly(read_only)
        self.apply_style()
    
    def apply_style(self):
        """Apply text edit style"""
        self.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)


class PanelFrame(QFrame):
    """Custom frame for panels with consistent styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.apply_style()
    
    def apply_style(self):
        """Apply frame style"""
        self.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)


class StatusLabel(QLabel):
    """Label for displaying status with color coding"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.set_status("normal")
    
    def set_status(self, status_type):
        """Set status style based on type"""
        if status_type == "success":
            self.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
        elif status_type == "error":
            self.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
        elif status_type == "warning":
            self.setStyleSheet("""
                QLabel {
                    color: #ff9800;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
        else:  # normal
            self.setStyleSheet("""
                QLabel {
                    color: #666;
                    padding: 5px;
                }
            """)
    
    def show_success(self, text):
        """Show success message"""
        self.setText(text)
        self.set_status("success")
    
    def show_error(self, text):
        """Show error message"""
        self.setText(text)
        self.set_status("error")
    
    def show_warning(self, text):
        """Show warning message"""
        self.setText(text)
        self.set_status("warning")
    
    def show_normal(self, text):
        """Show normal message"""
        self.setText(text)
        self.set_status("normal")
