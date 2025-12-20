# 🐛 Debug Guide - Session Disconnect Issue

## 🔍 Vấn Đề

Session bị tự động disconnect sau một thời gian điều khiển, gây ra các triệu chứng:
- Không điều khiển được chuột/bàn phím nữa
- Nhấn nút Disconnect báo "Không ở trong phiên nào"
- Console spam nhiều lần "Disconnect button clicked"

## ✅ Đã Sửa

### 1. **Tắt thông báo lỗi spam**
- `gui_disconnect_session()` không còn báo "Lỗi" nữa
- Thay bằng log warning: "Không có phiên đang hoạt động"

### 2. **Kiểm tra trạng thái trước khi disconnect**
- `_on_disconnect_click()` kiểm tra `current_client_id` trước khi emit signal
- Tránh gửi disconnect request khi session đã ended

### 3. **Giảm spam log**
- Key Press chỉ log các phím đặc biệt (enter, backspace, esc)
- Key Release không log nữa
- Input events không gửi nếu session đã ended

### 4. **Hiển thị thông báo session ended**
- GUI hiển thị message box với icon ⚠️
- Hướng dẫn user click Disconnect để đóng window

## 🔧 Debug Steps

### Bước 1: Xác định nguyên nhân session ended

**Kiểm tra console output:**

```
[Manager] ⚠️ Phiên làm việc với 'testuser' đã kết thúc.
[Manager] Session kết thúc: current_session_client_id = testuser
[ManageScreenWindow] ⚠️ Session ended - trở về Connecting...
[ManageScreenWindow] Trước khi ended: current_client_id = testuser
[ManageScreenWindow] Sau khi ended: current_client_id = None
```

**Nguyên nhân có thể:**
1. Client bị crash/disconnect
2. Server detect network timeout
3. Manager bị mất kết nối
4. Session bị cleanup do lỗi

### Bước 2: Kiểm tra Server logs

**Trên Server console, tìm:**
```
[ServerSession] Đã dừng. Lý do: ...
[SessionManager] Dừng phiên ... do một bên ngắt kết nối.
```

### Bước 3: Kiểm tra Client logs

**Trên Client console, tìm:**
```
[Client] _on_disconnected được gọi.
[ClientNetwork] Mất kết nối tới server.
[ClientReceiver] Mất kết nối tới Server: ...
```

## 🧪 Test Cases

### Test 1: Keyboard Input Stability
```python
# Gõ liên tục trong 1 phút
# Expected: Session không bị disconnect
for i in range(60):
    type("hello world")
    time.sleep(1)
```

### Test 2: Idle Connection
```python
# Không làm gì trong 2 phút
# Expected: Session vẫn giữ (timeout là 10 phút)
time.sleep(120)
# Thử điều khiển lại
```

### Test 3: Reconnection
```python
# Sau khi session ended
# 1. Đóng window Remote Desktop
# 2. Mở lại và connect
# Expected: Có thể connect lại bình thường
```

## 🔍 Các Điểm Kiểm Tra

### Manager Side

**File: `manager.py`**
```python
def _on_session_ended(self, client_id: str):
    # Kiểm tra xem có được gọi không? Tại sao?
    print(f"[DEBUG] Session ended callback triggered")
    print(f"[DEBUG] Client ID: {client_id}")
    import traceback
    traceback.print_stack()  # In call stack để biết ai gọi
```

**File: `manager_app.py`**
```python
def _on_receiver_done(self):
    # Kiểm tra receiver có bị stop không?
    print(f"[DEBUG] Receiver done callback")
    print(f"[DEBUG] Running: {self.running}")
```

### Client Side

**File: `client.py`**
```python
def _on_disconnected(self):
    # Kiểm tra client có bị disconnect không?
    print(f"[DEBUG] Client disconnected callback")
    print(f"[DEBUG] Network running: {self.network.running}")
```

### Server Side

**File: `session.py`**
```python
def run(self):
    # Thêm log trong finally block
    print(f"[DEBUG] Session stopped")
    print(f"[DEBUG] Reason: {reason}")
    print(f"[DEBUG] Running: {self.running}")
```

## 💡 Giải Pháp Tạm Thời

Nếu session bị disconnect thường xuyên:

### 1. Tăng timeout
```python
# File: src/server/network/server_receiver.py
tpkt_body = TPKTLayer.recv_one(self.sock, recv_fn=self.sock.recv, timeout=1200.0)  # 20 phút
```

### 2. Thêm keepalive
```python
# File: manager_app.py hoặc client_network.py
self.client.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
```

### 3. Auto-reconnect
```python
# File: manage_clients.py
def _on_session_ended(self):
    # Tự động reconnect sau 2 giây
    if self.auto_reconnect:
        QTimer.singleShot(2000, lambda: self.manager.gui_connect_to_client(self.client_id))
```

## 📊 Monitoring

### Thêm heartbeat log

**Manager:**
```python
# Gửi ping mỗi 30 giây
def heartbeat(self):
    while self.running:
        if self.current_session_client_id:
            print(f"[Heartbeat] Session active: {self.current_session_client_id}")
        time.sleep(30)
```

**Server:**
```python
# Log active sessions
def monitor_sessions(self):
    while True:
        print(f"[Monitor] Active sessions: {len(self.active_sessions)}")
        time.sleep(60)
```

## 🔥 Common Issues

### Issue 1: "Socket closed" sau 1-2 phút
**Nguyên nhân:** Network timeout hoặc firewall
**Giải pháp:** 
- Kiểm tra firewall
- Tăng socket timeout
- Thêm keepalive packets

### Issue 2: Client bị crash khi nhận input
**Nguyên nhân:** pyautogui lỗi với một số phím đặc biệt
**Giải pháp:**
- Thêm try-catch trong `handle_input_pdu`
- Log chi tiết key không support
- Fallback sang `press()` thay vì `keyDown/keyUp`

### Issue 3: Manager mất kết nối Server
**Nguyên nhân:** SSL handshake timeout
**Giải pháp:**
- Kiểm tra certificate
- Tăng SSL timeout
- Log chi tiết SSL errors

## 📝 Checklist

Khi gặp disconnect issue, kiểm tra:
- [ ] Client console có error không?
- [ ] Server console có error không?
- [ ] Manager console có error không?
- [ ] Network có stable không? (ping test)
- [ ] Firewall có block không?
- [ ] Certificate còn valid không?
- [ ] Timeout settings có hợp lý không?
- [ ] Memory/CPU usage có cao không?

---

**Last Updated:** December 20, 2025  
**Status:** 🔧 Debugging in progress
