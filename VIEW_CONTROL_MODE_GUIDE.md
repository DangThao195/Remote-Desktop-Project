# Hướng dẫn View & Control Mode

## Tổng quan

Hệ thống đã được nâng cấp để tách riêng 2 chế độ:
- **VIEW Mode** (Chỉ xem): Nhiều manager có thể xem màn hình của 1 client cùng lúc (1-nhiều)
- **CONTROL Mode** (Điều khiển): Chỉ 1 manager có thể điều khiển 1 client tại 1 thời điểm (1-1 exclusive)

## Sự khác biệt

| Tiêu chí | VIEW Mode | CONTROL Mode |
|----------|-----------|--------------|
| Số lượng | 1 client → Nhiều viewers | 1 client → 1 controller |
| Video | ✅ Nhận (có thể chậm) | ✅ Nhận (real-time) |
| Điều khiển | ❌ Không | ✅ Mouse + Keyboard |
| Độc quyền | Không | Có (1-1 exclusive) |
| Sử dụng | Giám sát, Demo | Remote support |

## Server Commands

### 1. VIEW Mode

**Manager request view:**
```
Command: view:client_username
Response: view_started:client_username  (thành công)
          error:...                      (lỗi)
```

**Manager stop view:**
```
Command: stop_view
Response: view_stopped:client_username
```

**Client notification:**
```
Receive: view_started:manager_id  (có người xem)
         view_stopped:manager_id  (người xem rời đi)
```

### 2. CONTROL Mode

**Manager request control:**
```
Command: control:client_username
Response: control_started:client_username  (thành công)
          control_denied:...               (client đang bị control)
          error:...                         (lỗi)
```

**Manager stop control:**
```
Command: stop_control
Response: control_stopped:client_username
```

**Client notification:**
```
Receive: control_started:manager_id  (bị điều khiển)
         control_stopped:manager_id  (không còn bị điều khiển)
```

## Protocol Flow

### VIEW Session

```
Manager                Server                  Client
   |                      |                       |
   |--view:client_name--->|                       |
   |                      |--view_started:mgr-->  |
   |<--view_started:cli---|                       |
   |                      |                       |
   |                      |<====VIDEO FRAMES=====|
   |<====VIDEO FRAMES=====|                       |
   |                      |                       |
   |--stop_view---------->|                       |
   |<--view_stopped:cli---|--view_stopped:mgr--> |
```

### CONTROL Session

```
Manager                Server                  Client
   |                      |                       |
   |--control:client----->|                       |
   |                      |--control_started:mgr->|
   |<--control_started:---|                       |
   |                      |                       |
   |====INPUT EVENTS=====>|====INPUT EVENTS=====>|
   |                      |                       |
   |<====VIDEO FRAMES=====|<====VIDEO FRAMES=====|
   |                      |                       |
   |--stop_control------->|                       |
   |<--control_stopped:---|--control_stopped:mgr->|
```

## Client List Update

Server sẽ broadcast danh sách client kèm trạng thái:

```json
[
  {
    "id": "client1",
    "name": "client1",
    "ip": "192.168.1.100",
    "is_controlled": false,
    "viewer_count": 2
  },
  {
    "id": "client2",
    "name": "client2",
    "ip": "192.168.1.101",
    "is_controlled": true,
    "viewer_count": 0
  }
]
```

- `is_controlled`: `true` nếu đang bị control (không thể control thêm)
- `viewer_count`: Số người đang view

## Manager Implementation

### 1. View Client

```python
# GUI: Button "Screen"
def on_screen_click(self, client_id):
    # Gửi request view
    self.manager.send_control_command(f"view:{client_id}")
    
    # Đợi response
    # → Nhận: view_started:client_id
    # → Bắt đầu nhận video frames
    
    # Mở window chỉ hiển thị video, không có input events
    self.view_window = ViewOnlyWindow(client_id)
    self.view_window.show()
```

### 2. Control Client

```python
# GUI: Button "Control"
def on_control_click(self, client_id):
    # Check xem client có bị control chưa
    if client.is_controlled:
        show_message("Client đang bị điều khiển bởi người khác")
        return
    
    # Gửi request control
    self.manager.send_control_command(f"control:{client_id}")
    
    # Đợi response
    # → Nhận: control_started:client_id  (thành công)
    # → Nhận: control_denied:...         (bị từ chối)
    
    # Mở window với cả video và input handling
    self.control_window = ControlWindow(client_id)
    self.control_window.show()
    
    # Bật input event listeners
    self.control_window.enable_input_control()
```

### 3. Stop

```python
# Stop view
def stop_view(self):
    self.manager.send_control_command("stop_view")
    # → Nhận: view_stopped:client_id
    self.view_window.close()

# Stop control
def stop_control(self):
    self.manager.send_control_command("stop_control")
    # → Nhận: control_stopped:client_id
    self.control_window.close()
    self.control_window.disable_input_control()
```

## GUI Design

### ManageClientsWindow

```python
# Danh sách clients với trạng thái
for client in client_list:
    item = QListWidgetItem(f"{client['id']} ({client['ip']})")
    
    # Thêm badge trạng thái
    if client['is_controlled']:
        item.setText(f"🔒 {client['id']} (Controlled)")
        item.setBackground(QColor("#ffcccc"))  # Màu đỏ nhạt
    
    if client['viewer_count'] > 0:
        item.setText(f"👁️ {client['id']} ({client['viewer_count']} viewers)")
    
    self.client_list.addItem(item)

# Buttons
self.screen_btn.clicked.connect(self.view_screen)   # VIEW mode
self.control_btn.clicked.connect(self.control_client)  # CONTROL mode
```

### ViewOnlyWindow

```python
class ViewOnlyWindow(QWidget):
    """Window chỉ hiển thị video, không có input"""
    
    def __init__(self, client_id):
        super().__init__()
        self.setWindowTitle(f"View: {client_id}")
        
        # Video label
        self.video_label = QLabel()
        
        # KHÔNG có input event handlers
        # Chỉ update video khi nhận frames
    
    def update_video(self, frame):
        self.video_label.setPixmap(frame)
```

### ControlWindow

```python
class ControlWindow(QWidget):
    """Window với video + input control"""
    
    def __init__(self, client_id):
        super().__init__()
        self.setWindowTitle(f"Control: {client_id}")
        
        # Video label
        self.video_label = QLabel()
        
        # BẬT input event handlers
        self.video_label.setMouseTracking(True)
        self.video_label.installEventFilter(self)
    
    def enable_input_control(self):
        """Bật input events"""
        self.input_enabled = True
    
    def disable_input_control(self):
        """Tắt input events"""
        self.input_enabled = False
    
    def mouseMoveEvent(self, event):
        if self.input_enabled:
            # Gửi input event tới client
            self.send_input(event)
```

## Use Cases

### 1. Demo/Presentation (VIEW)

```
Trường hợp: 1 client demo, nhiều người xem
- Client: Chia sẻ màn hình
- Manager 1, 2, 3: View cùng lúc
- Không ai điều khiển
```

### 2. Remote Support (CONTROL)

```
Trường hợp: IT support từ xa
- Client: Gặp vấn đề
- Manager: Control để fix
- Chỉ 1 người control tại 1 thời điểm
```

### 3. Giám sát (VIEW)

```
Trường hợp: Giám sát nhiều client
- Manager: View nhiều client cùng lúc
- Tách nhiều window
- Không điều khiển
```

### 4. Training (VIEW + CONTROL)

```
Trường hợp: Đào tạo nhân viên
- Trainer: Control để demo
- Trainees: View để xem
- Trainer có quyền độc quyền điều khiển
```

## Backward Compatibility

Legacy command `connect:client_name` vẫn hoạt động nhưng deprecated. Nó sẽ:
- Tạo old-style session (1-1)
- Hỗ trợ cả view và control
- Nên migrate sang `view:` hoặc `control:`

## Migration Guide

### Cũ (Session)
```python
# Kết nối (cả view và control)
manager.connect_to_client("client1")
```

### Mới (View/Control)
```python
# Chỉ xem
manager.view_client("client1")

# Hoặc điều khiển
manager.control_client("client1")
```

## Testing

```bash
# Test VIEW mode
python test_view_mode.py

# Test CONTROL mode  
python test_control_mode.py

# Test multiple viewers
python test_multi_view.py

# Test control exclusive
python test_control_exclusive.py
```
