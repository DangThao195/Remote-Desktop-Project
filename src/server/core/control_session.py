# server/core/control_session.py

import threading
from queue import Queue, Empty
from src.server.server_constants import (
    CHANNEL_VIDEO, CHANNEL_CONTROL, CHANNEL_INPUT, CHANNEL_FILE, CHANNEL_CURSOR
)
from src.common.network.mcs_layer import MCSLite

class ControlSession(threading.Thread):
    """
    Control Session: Cho phép 1 Manager điều khiển 1 Client (1-1 exclusive)
    - Manager gửi input (mouse/keyboard) → Client
    - Client gửi video/cursor → Manager
    - Chỉ 1 manager có thể control 1 client tại 1 thời điểm
    """
    def __init__(self, manager_id, client_id, broadcaster, done_callback):
        self.session_id = f"CTRL:{manager_id}::{client_id}"
        super().__init__(daemon=True, name=f"ControlSession-{self.session_id}")
        
        self.manager_id = manager_id
        self.client_id = client_id
        self.broadcaster = broadcaster
        self.done_callback = done_callback
        
        self.pdu_queue = Queue(maxsize=4096)
        self.running = True
        
        print(f"[ControlSession] Created: {self.session_id}")
    
    def enqueue_pdu(self, from_id, pdu):
        """Nhận PDU từ SessionManager và xử lý"""
        if not self.running:
            return
        
        # Ưu tiên PDU quan trọng (Input, Control, File) hơn Video
        if pdu.get("type") in ("full", "rect") and self.pdu_queue.full():
            return  # Bỏ video frame nếu queue đầy
        
        try:
            self.pdu_queue.put((from_id, pdu), block=False)
        except Queue.Full:
            # Nếu queue vẫn đầy và PDU quan trọng, loại bỏ PDU cũ
            if pdu.get("type") not in ("full", "rect"):
                try:
                    self.pdu_queue.get_nowait()
                    self.pdu_queue.put((from_id, pdu), block=False)
                except:
                    pass
    
    def run(self):
        """Thread chính xử lý relay PDU giữa manager và client"""
        print(f"[ControlSession] Started: {self.session_id}")
        reason = "Normal shutdown"
        
        try:
            while self.running:
                try:
                    from_id, pdu = self.pdu_queue.get(timeout=0.5)
                except Empty:
                    continue
                
                ptype = pdu.get("type")
                raw_payload = pdu.get("_raw_payload")
                
                if not raw_payload:
                    continue
                
                # === Từ Client → Manager ===
                if from_id == self.client_id:
                    target_id = self.manager_id
                    
                    if ptype in ("full", "rect"):
                        # Video frame
                        mcs_frame = MCSLite.build(CHANNEL_VIDEO, raw_payload)
                    elif ptype == "cursor":
                        # Cursor position
                        mcs_frame = MCSLite.build(CHANNEL_CURSOR, raw_payload)
                    elif ptype == "control":
                        # Control message
                        mcs_frame = MCSLite.build(CHANNEL_CONTROL, raw_payload)
                    elif ptype == "input":
                        # Input (keylog) - forward to manager
                        mcs_frame = MCSLite.build(CHANNEL_INPUT, raw_payload)
                    else:
                        # File transfer
                        mcs_frame = MCSLite.build(CHANNEL_FILE, raw_payload)
                    
                    self.broadcaster.enqueue(target_id, mcs_frame)
                
                # === Từ Manager → Client ===
                elif from_id == self.manager_id:
                    target_id = self.client_id
                    
                    if ptype == "input":
                        # Input control (mouse/keyboard)
                        # print(f"[ControlSession] 🎮 Forwarding input from manager to {target_id}")
                        mcs_frame = MCSLite.build(CHANNEL_INPUT, raw_payload)
                    elif ptype == "control":
                        # Control command
                        mcs_frame = MCSLite.build(CHANNEL_CONTROL, raw_payload)
                    elif ptype not in ("full", "rect", "cursor"):
                        # File transfer
                        mcs_frame = MCSLite.build(CHANNEL_FILE, raw_payload)
                    else:
                        continue
                    
                    self.broadcaster.enqueue(target_id, mcs_frame)
        
        except Exception as e:
            reason = f"Error: {e}"
            print(f"[ControlSession] Error: {e}")
        finally:
            self.running = False
            print(f"[ControlSession] Stopped: {self.session_id}. Reason: {reason}")
            if self.done_callback:
                self.done_callback(self, reason)
    
    def stop(self):
        """Dừng control session"""
        self.running = False
        with self.pdu_queue.mutex:
            self.pdu_queue.queue.clear()
