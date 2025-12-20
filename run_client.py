"""
Client Launcher - Chạy client với GUI đăng nhập
Chạy: python run_client.py
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.client.auth import ClientConnection

if __name__ == "__main__":
    # Khởi tạo QApplication
    app = QApplication(sys.argv)
    
    # Kết nối tới Auth Server
    try:
        app.conn = ClientConnection()
        print("[Client] Da ket noi toi Auth Server")
    except ConnectionRefusedError:
        QMessageBox.critical(
            None,
            "Loi ket noi",
            "Khong the ket noi toi Server!\n\n"
            "Vui long chay server truoc:\n"
            "python run_server.py"
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "Loi", f"Loi: {e}")
        sys.exit(1)
    
    # Hiển thị màn hình đăng nhập
    from src.gui.signin import SignInWindow
    signin_window = SignInWindow()
    signin_window.showMaximized()
    
    sys.exit(app.exec())
