# src/server/network/server_app.py

from src.server.network.server_network import ServerNetwork
from src.server.network.server_broadcaster import ServerBroadcaster
from src.server.core.session_manager import SessionManager
import sys

class ServerApp:
    def __init__(self, host="0.0.0.0", port=5000, certfile=None, keyfile=None):
        try:
            # 1. Broadcaster: Chịu trách nhiệm gửi dữ liệu xuống socket
            self.broadcaster = ServerBroadcaster()
            
            # 2. SessionManager: Chứa logic if/else, gọi auth, xử lý database
            self.session_manager = SessionManager(self.broadcaster)
            
            # 3. ServerNetwork: Chứa socket.accept(), thread loop nhận dữ liệu
            self.network = ServerNetwork(
                host=host, 
                port=port, 
                certfile=certfile, 
                keyfile=keyfile
            )
            
            # Mapping callbacks: Network nhận được gì -> ném sang SessionManager xử lý
            self.network.set_callbacks(
                on_connect=self.session_manager.handle_new_connection,
                on_pdu=self.session_manager.handle_pdu,
                on_disconnect=self.session_manager.handle_disconnection
            )
            
            # Network cần broadcaster để đăng ký socket mới vào danh sách quản lý gửi
            self.network.set_broadcaster(self.broadcaster)
            
        except Exception as e:
            print(f"[ServerApp] Init Error: {e}")
            sys.exit(1)

    def start(self):
        print("="*30)
        print("[ServerApp] System Starting...")
        try:
            self.broadcaster.start()
            self.session_manager.start()
            self.network.start() # Hàm này sẽ start Thread lắng nghe socket
            print(f"[ServerApp] Running on {self.network.host}:{self.network.port}")
            print("="*30)
        except Exception as e:
            print(f"[ServerApp] Start Error: {e}")
            self.stop()

    def stop(self):
        print("\n[ServerApp] System Stopping...")
        if hasattr(self, 'network'): self.network.stop()
        if hasattr(self, 'session_manager'): self.session_manager.stop()
        if hasattr(self, 'broadcaster'): self.broadcaster.stop()
        print("[ServerApp] Stopped.")