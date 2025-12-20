# server/network/server_broadcaster.py

import threading
from queue import Queue, Empty
from src.common.network.tpkt_layer import TPKTLayer

""" Nhận (target_id, mcs_frame) từ queue, đóng gói TPKT và gửi đi.
    mcs_frame: đã bao gồm (channel header + pdu payload). """
class ServerBroadcaster(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="Broadcaster")
        self.running = True
        self.queue = Queue(maxsize=1024) # Giới hạn queue để tránh OOM
        self.clients = {}  # client_id -> ssl_socket
        self.lock = threading.Lock()

    # Lưu socket vào danh sách client
    def register(self, client_id: str, ssl_sock):
        with self.lock:
            self.clients[client_id] = ssl_sock
        print(f"[Broadcaster] Đã đăng ký {client_id}")

    # Xóa socket khỏi danh sách client
    def unregister(self, client_id: str):
        with self.lock:
            self.clients.pop(client_id, None)
        print(f"[Broadcaster] Đã hủy đăng ký {client_id}")
    
    # Lấy socket của client (để lấy IP address)
    def get_socket(self, client_id: str):
        """Lấy socket của client (để lấy IP address)"""
        with self.lock:
            return self.clients.get(client_id)

    # Đưa (target_id, mcs_frame) vào hàng đợi self.queue
    def enqueue(self, target_id: str, mcs_frame: bytes):
        if not self.running:
            return
        try:
            self.queue.put((target_id, mcs_frame), block=False)
        except Queue.Full:
            print(f"[Broadcaster] Hàng đợi gửi bị đầy! Bỏ qua gói tin cho {target_id}")

    def run(self):
        while self.running:
            try:
                target_id, mcs_frame = self.queue.get(timeout=0.5)
            except Empty:
                continue

            ssl_sock = None
            with self.lock:
                ssl_sock = self.clients.get(target_id) 

            if ssl_sock:
                try:
                    # --- Đóng gói TPKT và gửi ---
                    tpkt_packet = TPKTLayer.pack(mcs_frame) # Đóng gói thêm header TPKT (4 bytes) vào trước dữ liệu
                    ssl_sock.sendall(tpkt_packet) # Gửi toàn bộ dữ liệu qua mạng 
                    
                except Exception as e:
                    # Nếu gửi lỗi (ví dụ: client ngắt kết nối, ...). ServerReceiver sẽ tự phát hiện và dọn dẹp
                    print(f"[Broadcaster] Lỗi khi gửi cho {target_id}: {e}")

    def stop(self):
        self.running = False
        print("[Broadcaster] Đang dừng...")
        with self.queue.mutex:
            self.queue.queue.clear()
        with self.lock:
            self.clients.clear()
        print("[Broadcaster] Đã dừng.")