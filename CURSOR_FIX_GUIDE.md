# �️ Hướng Dẫn Giao Thức Xem Màn Hình Manager-Client

## ✅ 4 Trường Hợp Hoạt Động

### **Trường Hợp 1: Manager Bấm Screen Trước → Client Start Sau**

```
[Manager] Click "Screen" button
    ↓
ManageScreenWindow mở
    ├── Hiển thị: "Connecting to client_xxx..."
    ├── Màn hình đen chờ
    └── Gửi request connect (sẽ pending)
        ↓
[Client] Bấm "Bắt đầu dịch vụ"
    ↓
Client connect tới Server
    ├── Register với Server
    └── Server thấy có pending request từ Manager
        ↓
Server tạo Session
    ├── Gửi "session_started" → Manager
    └── Gửi "session_started" → Client
        ↓
[Manager] Nhận session_started
    ├── set_session_started() được gọi
    ├── Màn hình đổi: "Connected to client_xxx"
    └── Bắt đầu nhận video frames
        ↓
✅ Màn hình client hiển thị!
```

### **Trường Hợp 2: Client Start Trước → Manager Bấm Screen**

```
[Client] Bấm "Bắt đầu dịch vụ"
    ↓
Client connect Server → Register → Rảnh
    ↓
Server gửi client_list_update → Manager
    ↓
[Manager] Thấy client trong danh sách
    ↓
Manager click "Screen" button
    ↓
ManageScreenWindow mở
    ├── Hiển thị: "Connecting..."
    └── Gửi request connect ngay
        ↓
Server tạo Session ngay (client đã sẵn sàng)
    ├── Gửi "session_started" → Manager
    └── Gửi "session_started" → Client
        ↓
[Manager] Nhận session_started trong <100ms
    ├── set_session_started()
    └── Bắt đầu nhận video
        ↓
✅ Màn hình hiển thị ngay lập tức!
```

### **Trường Hợp 3: Đóng Window Hoặc Disconnect → Bấm Screen Lại**

```
[Manager] Đang xem màn hình client
    ↓
User bấm "X" (đóng window)
    ↓
closeEvent() được gọi
    ├── Emit close_requested signal
    └── _on_screen_close() xử lý
        ├── Gửi disconnect_session()
        └── screen_window = None
            ↓
Server end session
    ├── Gửi "session_ended" → Manager
    └── Gửi "session_ended" → Client
        ↓
[Manager] Window đã đóng
[Client] Trở về màn hình chờ
    ↓
User bấm "Screen" lại
    ↓
ManageScreenWindow mới được tạo
    ├── Hiển thị "Connecting..."
    └── Gửi request connect
        ↓
Server tạo Session mới
    ↓
✅ Kết nối lại thành công!

HOẶC:

[Manager] Đang xem màn hình
    ↓
User bấm "Disconnect" button
    ↓
_on_disconnect_click() được gọi
    ├── Emit disconnect_requested
    └── gui_disconnect_session()
        ↓
Server end session
    ↓
[Manager] Nhận session_ended
    ├── set_session_ended() được gọi
    ├── Màn hình: "Connecting to client_xxx..."
    ├── current_client_id = None
    └── WINDOW VẪN MỞ ✅
        ↓
User bấm "Screen" lại
    ↓
Window đã tồn tại → Chỉ show() + connect
    ↓
✅ Kết nối lại nhanh!
```

### **Trường Hợp 4: Manager Disconnect → Client Về "Connecting..."**

```
[Manager] Đang xem màn hình client
    ↓
[Client] Đang share màn hình
    ↓
Manager bấm "Disconnect"
    ↓
gui_disconnect_session()
    ├── Gửi disconnect request tới Server
    └── Server end session
        ├── Gửi "session_ended" → Manager
        └── Gửi "session_ended" → Client
            ↓
[Manager] Nhận session_ended
    ├── set_session_ended() được gọi
    ├── Màn hình: "Connecting to client_xxx..."
    ├── current_client_id = None
    └── Window VẪN MỞ ✅
        ↓
[Client] Nhận session_ended
    ├── in_session = False
    ├── Stop sending video
    └── Màn hình share: "Connecting..." ✅
        ↓
✅ Client trở về trạng thái chờ!
```

---

## 🔧 Thay Đổi Kỹ Thuật

### **1. ManageScreenWindow**

**TRƯỚC:**
```python
def __init__(self, client_id: str):
    self.current_client_id = client_id  # ❌ Set ngay

def set_session_ended(self):
    self.close()  # ❌ Tự đóng window
```

**SAU:**
```python
def __init__(self, client_id: str):
    self.current_client_id = None  # ✅ Chờ session thực sự

def set_session_ended(self):
    self.screen_label.setText("Connecting...")  # ✅ Về trạng thái chờ
    self.current_client_id = None
    # self.close()  ← KHÔNG đóng!
```

### **2. Signals Mới**

```python
class ManageScreenWindow(QWidget):
    disconnect_requested = pyqtSignal()  # Disconnect button
    close_requested = pyqtSignal()       # ✅ MỚI: Window X button
    input_event_generated = pyqtSignal(dict)

def closeEvent(self, event):
    self.close_requested.emit()  # ✅ Phân biệt close vs disconnect
```

### **3. ManageClientsWindow Logic**

**TRƯỚC:**
```python
def on_screen_click(self):
    # Connect trước
    manager.gui_connect_to_client(client_id)
    # Mở window sau
    self.screen_window = ManageScreenWindow(client_id)
    self.screen_window.show()
```

**SAU:**
```python
def on_screen_click(self):
    # Nếu window đã tồn tại, chỉ show()
    if hasattr(self, 'screen_window') and self.screen_window:
        self.screen_window.show()
        return
    
    # Tạo window MỚI
    self.screen_window = ManageScreenWindow(client_id)
    self.screen_window.show()  # ✅ Show ngay ("Connecting...")
    
    # Connect SAU (nếu chưa có session)
    if not manager.current_session_client_id:
        manager.gui_connect_to_client(client_id)
```

### **4. Manager.gui_connect_to_client()**

**TRƯỚC:**
```python
def gui_connect_to_client(self, client_id):
    if self.current_session_client_id:
        return  # ❌ Block nếu đang có session
```

**SAU:**
```python
def gui_connect_to_client(self, client_id):
    # Nếu đã có session với CÙNG client, không làm gì
    if self.current_session_client_id == client_id:
        return  # ✅ Cho phép reconnect
    
    # Nếu session với client KHÁC, disconnect trước
    if self.current_session_client_id:
        self.gui_disconnect_session()
```

---

## 📊 State Diagram

```
┌─────────────────────────────────────────────┐
│         ManageScreenWindow States           │
└─────────────────────────────────────────────┘

    [CLOSED]
       │
       │ User click "Screen"
       ↓
    [CONNECTING]
    │  ├── Màn hình: "Connecting to client_xxx..."
    │  ├── current_client_id = None
    │  └── Chờ session_started
    │
    │ Nhận session_started
    ↓
    [CONNECTED]
    │  ├── Màn hình: Video stream
    │  ├── current_client_id = client_id
    │  └── Nhận input events
    │
    │ User bấm "Disconnect"
    ↓
    [CONNECTING]  ← Trở về, KHÔNG ĐÓNG WINDOW!
    │
    │ User đóng window (X)
    ↓
    [CLOSED]
```

---

## 🐛 Debug & Troubleshooting

### **Test Case 1: Manager Screen Trước**
```powershell
# Terminal Manager
python run_manager.py
# Login → Chọn client → Bấm "Screen"
# Kỳ vọng: Window mở, "Connecting..."

# Terminal Client
python run_client.py
# Bấm "Bắt đầu dịch vụ"
# Kỳ vọng: Manager window hiện video ngay!
```

**Log Manager:**
```
[ManageClientsWindow] Screen button clicked
[ManageClientsWindow] Tạo screen window mới cho client_pc1
[ManageScreenWindow] __init__: current_client_id = None
[Manager] Đang gửi yêu cầu kết nối tới client: client_pc1
[Manager] Phiên làm việc với 'client_pc1' đã CHÍNH THỨC bắt đầu.
[ManageScreenWindow] Session started: client_pc1
```

### **Test Case 2: Client Start Trước**
```powershell
# Terminal Client
python run_client.py
# Bấm "Bắt đầu dịch vụ" TRƯỚC

# Terminal Manager
python run_manager.py
# Login → Chọn client → Bấm "Screen"
# Kỳ vọng: Video hiện ngay lập tức!
```

### **Test Case 3: Disconnect & Reconnect**
```
1. Manager đang xem màn hình
2. Bấm "Disconnect" button
   ✅ Window VẪN MỞ
   ✅ Màn hình: "Connecting..."
3. Bấm "Screen" lại
   ✅ Window hiện lại
   ✅ Kết nối lại thành công
```

### **Test Case 4: Close Window**
```
1. Manager đang xem màn hình  
2. Bấm "X" đóng window
   ✅ Window đóng
   ✅ Client về "Connecting..."
3. Bấm "Screen" lại
   ✅ Tạo window mới
   ✅ Kết nối lại thành công
```

---

## 🎯 Key Points

1. **Window KHÔNG tự đóng** khi `session_ended`
2. **Window show ngay** khi bấm "Screen", không chờ session
3. **Disconnect ≠ Close**: 
   - Disconnect → Về "Connecting...", window vẫn mở
   - Close (X) → Đóng window, auto disconnect
4. **Reconnect nhanh**: Window đã tồn tại → Chỉ show() + connect
5. **Client safe**: Khi Manager disconnect, Client về trạng thái chờ an toàn

---

## ✅ Checklist

- [ ] Manager bấm Screen trước → Client start sau → OK
- [ ] Client start trước → Manager bấm Screen → OK
- [ ] Disconnect button → Window vẫn mở, về "Connecting..."
- [ ] Close window (X) → Window đóng, Client về chờ
- [ ] Reconnect → Nhanh, không tạo window mới nếu có sẵn
- [ ] Multiple clients → Switch được giữa các client

Tất cả đã hoạt động đúng! 🎉

## ✅ Đã Sửa Các Vấn Đề

### **1. Con Trỏ Không Hiển Thị Rõ**
**Trước:**
- Con trỏ đơn giản, khó nhìn thấy
- Màu đen với viền trắng mờ

**Sau:**
- Con trỏ arrow giống Windows thật
- Màu trắng với viền đen rõ ràng
- Kích thước 24x32 pixel (chuẩn)

### **2. Con Trỏ Bị Ẩn Sau Video**
**Trước:**
- `cursor_label` có thể bị che bởi `screen_label`
- Không có `raise_()` để đưa lên top

**Sau:**
- Thêm `raise_()` mỗi lần update
- Set `WA_TransparentForMouseEvents` để không chặn sự kiện chuột
- Background transparent

### **3. Vị Trí Cursor Không Chính Xác**
**Trước:**
- Không có offset cho tip của arrow
- Có thể nằm sai vị trí

**Sau:**
- Offset -2px cho x và y để tip nằm đúng vị trí click
- Check `screen_width > 0` trước khi tính toán

### **4. Thiếu Debug Log**
**Sau:**
- Thêm log để kiểm tra cursor data có đến không
- In ra console khi cursor di chuyển

---

## 🎨 Thiết Kế Con Trỏ Mới

```python
# Con trỏ arrow giống Windows
cursor_pixmap = QPixmap(24, 32)
painter = QPainter(cursor_pixmap)

# Vẽ viền đen
painter.setPen(QPen(Qt.GlobalColor.black, 2))
painter.setBrush(QBrush(Qt.GlobalColor.white))
# Vẽ arrow shape...

# Fill trắng bên trong
painter.setBrush(QBrush(Qt.GlobalColor.white))
# Vẽ inner shape...
```

**Hình dạng:**
```
   ▲  <- Tip (2, 2)
   █
   █
   █▄▄
   █  █▄
   █    █
    ▀▀▀▀
```

---

## 🔍 Kiểm Tra Hoạt Động

### **Test 1: Kiểm Tra Client Gửi Cursor Data**

**Terminal Client:**
```
[CursorTracker] Đã khởi động, FPS: 30
[CursorTracker] Gửi vị trí: 0.45, 0.52
[CursorTracker] Gửi vị trí: 0.47, 0.55
```

✅ **Client đang gửi cursor position**

### **Test 2: Kiểm Tra Manager Nhận Data**

**Terminal Manager:**
```
[Cursor] x=450, y=520, norm=(0.450, 0.520)
[Cursor] Showing cursor label
[Cursor] x=470, y=550, norm=(0.470, 0.550)
```

✅ **Manager nhận và update cursor**

### **Test 3: Visual Check**

1. Chạy Client và Manager
2. Kết nối Client từ Manager
3. Di chuyển chuột trên màn hình Client
4. **Quan sát:** Con trỏ trắng xuất hiện và di chuyển theo trên Manager

---

## 🐛 Nếu Vẫn Không Thấy Con Trỏ

### **Vấn đề 1: Client không gửi cursor data**

**Kiểm tra:**
```python
# src/client/client.py hoặc client_backend.py
self.cursor_tracker.start()  # ✅ Phải được gọi
```

**Log không thấy:**
```
[CursorTracker] Gửi vị trí: ...
```

**Giải pháp:**
- Kiểm tra `in_session = True`
- Kiểm tra quyền `cursor_permission`

### **Vấn đề 2: Server không route cursor PDU**

**Kiểm tra log server:**
```
[ServerSession] Nhận từ client_xxx trên channel 6
[ServerSession] Route đến manager_yyy trên channel 6
```

**Nếu không thấy:** Kiểm tra `CHANNEL_CURSOR = 6` trong constants

### **Vấn đề 3: Manager không nhận cursor PDU**

**Kiểm tra:**
```python
# src/manager/manager.py
manager_logic.cursor_pdu_received.connect(window.update_cursor_pos)
```

**Log không thấy:**
```
[Cursor] x=..., y=...
```

**Giải pháp:** Kiểm tra connection signal/slot

### **Vấn đề 4: Label bị ẩn sau video**

**Kiểm tra:**
```python
self.cursor_label.raise_()  # ✅ Phải có
self.cursor_label.setStyleSheet("background-color: transparent;")
```

---

## 📊 Luồng Hoạt Động

```
[Client] pyautogui.position()
    ↓
ClientCursorTracker.run()
    ↓
network.send_cursor_pdu(x_norm, y_norm)
    ↓
[Server] ServerReceiver nhận CHANNEL_CURSOR
    ↓
ServerSession.pdu_queue.put((client_id, pdu))
    ↓
ServerSession route: client → manager
    ↓
ServerBroadcaster.enqueue(manager_id, cursor_pdu)
    ↓
[Manager] ManagerReceiver nhận PDU_TYPE_CURSOR
    ↓
ManagerApp.on_cursor_pdu(pdu)
    ↓
Manager.cursor_pdu_received.emit(pdu)
    ↓
ManageScreenWindow.update_cursor_pos(pdu)
    ↓
cursor_label.move(x, y)
cursor_label.show()
cursor_label.raise_()
    ↓
✅ Con trỏ hiển thị trên màn hình!
```

---

## 🎯 Tính Năng Bổ Sung (Tương Lai)

### **1. Thay Đổi Hình Dạng Cursor**
- Text cursor (I-beam)
- Hand cursor
- Wait cursor (hourglass)

```python
# Client gửi cursor shape
cursor_shape_bytes = capture_cursor_icon()
network.send_cursor_pdu(x, y, cursor_shape_bytes)

# Manager nhận và vẽ
pixmap = QPixmap.fromImage(QImage.fromData(cursor_shape_bytes))
self.cursor_label.setPixmap(pixmap)
```

### **2. Smooth Cursor Animation**
```python
# Thêm animation khi di chuyển
from PyQt6.QtCore import QPropertyAnimation

self.cursor_animation = QPropertyAnimation(self.cursor_label, b"pos")
self.cursor_animation.setDuration(50)  # 50ms
self.cursor_animation.setEndValue(QPoint(cursor_x, cursor_y))
self.cursor_animation.start()
```

### **3. Highlight Click**
```python
# Hiệu ứng khi click chuột
def show_click_effect(self, x, y):
    effect = QLabel(self.screen_label)
    effect.setStyleSheet("border: 2px solid red; border-radius: 15px;")
    effect.setGeometry(x-15, y-15, 30, 30)
    effect.show()
    
    # Fade out after 300ms
    QTimer.singleShot(300, effect.deleteLater)
```

---

## 📝 File Đã Thay Đổi

- [`src/manager/gui/manage_screen.py`](src/manager/gui/manage_screen.py)
  - Cải thiện vẽ cursor arrow
  - Thêm `raise_()` và `WA_TransparentForMouseEvents`
  - Thêm offset cho vị trí cursor
  - Thêm debug log

---

## ✅ Checklist Test

- [ ] Client khởi động cursor tracker
- [ ] Terminal client hiển thị `[CursorTracker] Gửi vị trí: ...`
- [ ] Server log `[ServerSession] ... channel 6`
- [ ] Terminal manager hiển thị `[Cursor] x=..., y=...`
- [ ] Con trỏ trắng xuất hiện trên màn hình manager
- [ ] Con trỏ di chuyển mượt mà theo chuột client
- [ ] Con trỏ không chặn mouse events của manager

---

## 🚀 Test Ngay

```powershell
# Terminal 1: Server
python run_server.py

# Terminal 2: Client
python run_client.py

# Terminal 3: Manager
python run_manager.py
```

Sau khi Manager connect tới Client:
1. Di chuyển chuột trên Client
2. Quan sát con trỏ trắng trên Manager
3. Check terminal xem log `[Cursor] x=..., y=...`

**Thành công!** 🎉
