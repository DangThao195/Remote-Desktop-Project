# server/network/server_network.py

import socket
import ssl
import threading
from queue import Queue, Empty
from src.common.network.x224_handshake import X224Handshake
from src.common.network.security_layer_tls import create_server_context, server_wrap_socket
from src.server.server_constants import TLS_VERSION
from src.server.network.server_receiver import ServerReceiver

class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=5000, max_clients=200, certfile=None, keyfile=None):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.certfile = certfile
        self.keyfile = keyfile
        
        self.sock = None # Socket chủ, dùng để lắng nghe tại port 5000
        self.tls_context = None 
        
        self.clients = {}  # cid -> (ssl_sock, receiver_thread)
        self.running = False
        self.lock = threading.Lock()
        
        # Callbacks
        self.broadcaster = None
        self.on_connect_cb = None
        self.on_pdu_cb = None
        self.on_disconnect_cb = None

    def set_broadcaster(self, bc):
        self.broadcaster = bc

    def set_callbacks(self, on_connect, on_pdu, on_disconnect):
        self.on_connect_cb = on_connect
        self.on_pdu_cb = on_pdu
        self.on_disconnect_cb = on_disconnect

    def start(self):
        try:
            # --- Tạo Socket Server ---
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port)) # Đăng ký địa chỉ IP: Port
            self.sock.listen(self.max_clients) # Bắt đầu lắng nghe kết nối
            
            self.running = True
            
            # --- Bắt đầu luồng chấp nhận kết nối ---
            threading.Thread(target=self._accept_loop, daemon=True).start()
            print(f"[ServerNetwork] Đang lắng nghe (có TLS) trên {self.host}:{self.port}")
            
        except ssl.SSLError as e:
            print(f"[ServerNetwork] Lỗi SSL. Kiểm tra file cert/key: {e}")
            raise
        except Exception as e:
            print(f"[ServerNetwork] Lỗi khi khởi động: {e}")
            raise

    def _accept_loop(self):
        while self.running:
            try:
                # raw_sock: socket thô chưa qua TLS (nối tới client)
                # addr: địa chỉ IP:Port của client
                raw_sock, addr = self.sock.accept()
            except OSError:
                if self.running: print("[ServerNetwork] Lỗi accept().")
                break # Socket đã đóng

            print(f"[ServerNetwork] Có kết nối thô từ {addr}")
            
            ssl_sock = None
            try:
                # --- Handshake X224 (trên socket thô) ---
                ok, cid = X224Handshake.server_do_handshake(raw_sock, timeout=10)
                if not ok or not cid:
                    print(f"[ServerNetwork] Handshake X224 thất bại từ {addr}.")
                    raw_sock.close()
                    continue
                
                # --- Wrap TLS (nếu có certfile/keyfile) ---
                if self.certfile and self.keyfile:
                    if not self.tls_context:
                        self.tls_context = create_server_context(
                            certfile=self.certfile,
                            keyfile=self.keyfile
                        )
                    ssl_sock = server_wrap_socket(raw_sock, self.tls_context, do_handshake=True)
                    print(f"[ServerNetwork] Handshake thành công cho {cid}@{addr} (TLS enabled)")
                else:
                    ssl_sock = raw_sock
                    print(f"[ServerNetwork] Handshake thành công cho {cid}@{addr} (No TLS)")

                # --- Khởi tạo Receiver Thread ---
                # pdu_queue là queue chung của ServerNetwork
                receiver = ServerReceiver(
                    ssl_sock, 
                    cid, 
                    pdu_push_callback=self.on_pdu_cb,
                    done_callback=self._on_receiver_done
                )
                receiver.start()

                with self.lock:
                    # Đóng kết nối cũ nếu cid này đã tồn tại
                    if cid in self.clients:
                        print(f"[ServerNetwork] {cid} kết nối lại, đóng phiên cũ.")
                        self._cleanup_client(cid)
                    
                    self.clients[cid] = (ssl_sock, receiver)
                
                # Đăng ký với Broadcaster để có thể gửi tin
                if self.broadcaster:
                    self.broadcaster.register(cid, ssl_sock)
                
                # Báo cho SessionManager biết có client mới
                if self.on_connect_cb:
                    self.on_connect_cb(cid, ssl_sock)

            except ssl.SSLError as e:
                print(f"[ServerNetwork] Lỗi TLS Handshake: {e}")
                if ssl_sock: ssl_sock.close()
                else: raw_sock.close()
            except Exception as e:
                print(f"[ServerNetwork] Lỗi khi xử lý kết nối mới: {e}")
                if ssl_sock: ssl_sock.close()
                else: raw_sock.close()

    # Callback được gọi bởi ServerReceiver khi nó kết thúc (lỗi/mất kết nối)
    def _on_receiver_done(self, client_id):
        if not self.running:
            return
            
        print(f"[ServerNetwork] Receiver cho {client_id} đã dừng.")
        with self.lock:
            self._cleanup_client(client_id)
            
        # Báo cho Broadcaster/SessionManager
        if self.broadcaster:
            self.broadcaster.unregister(client_id)
        if self.on_disconnect_cb:
            self.on_disconnect_cb(client_id)

    # Dọn dẹp tài nguyên của client (phải được gọi trong lock)
    def _cleanup_client(self, cid):
        if cid in self.clients:
            sock, receiver = self.clients.pop(cid)
            if receiver and receiver.is_alive():
                receiver.stop()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except: pass
            try:
                sock.close()
            except: pass

    def stop(self):
        self.running = False
        with self.lock:
            client_ids = list(self.clients.keys())
            print(f"[ServerNetwork] Đang đóng {len(client_ids)} kết nối...")
            for cid in client_ids:
                self._cleanup_client(cid)
        
        if self.sock:
            try:
                self.sock.close()
            except: pass
        print("[ServerNetwork] Đã dừng.")