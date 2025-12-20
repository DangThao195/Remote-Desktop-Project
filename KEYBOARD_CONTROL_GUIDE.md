# 🎹 Hướng Dẫn Sử Dụng Điều Khiển Bàn Phím Remote

## 📋 Tổng Quan

Manager có thể điều khiển bàn phím của Client thông qua Server, giống như đang gõ trực tiếp trên máy Client.

## 🎯 Luồng Hoạt Động

```
Manager (Keyboard) → ManagerApp → Server → Client → pyautogui
```

### Chi tiết:
1. **Manager** nhấn phím trong cửa sổ Remote Desktop
2. **ManageScreenWindow** bắt sự kiện qua `keyPressEvent`/`keyReleaseEvent`
3. **Signal** `input_event_generated` được emit với data:
   ```python
   {
       "type": "key_press",  # hoặc "key_release"
       "key": "a"            # tên phím
   }
   ```
4. **ManagerApp** gửi INPUT PDU qua CHANNEL_INPUT
5. **Server** forward PDU từ Manager → Client
6. **ClientInputHandler** nhận và thực thi bằng `pyautogui.keyDown()`/`keyUp()`

## ⌨️ Các Phím Được Hỗ Trợ

### Phím Ký Tự (A-Z, 0-9)
- Tất cả ký tự chữ cái và số
- Ký tự đặc biệt: `!@#$%^&*()_+-=[]{}|;':",.<>?/~`
- Tự động chuyển về lowercase

### Phím Chức Năng
```python
# Modifier Keys
'ctrl', 'shift', 'alt', 'win'

# Navigation
'left', 'right', 'up', 'down'
'home', 'end', 'pageup', 'pagedown'

# Editing
'backspace', 'delete', 'insert'
'enter', 'tab', 'space', 'esc'

# Lock Keys
'capslock', 'numlock', 'scrolllock'

# Function Keys
'f1', 'f2', 'f3', ..., 'f12'

# Special
'printscreen', 'pause'
```

## 🚀 Cách Sử Dụng

### Bước 1: Khởi động hệ thống
```bash
# Terminal 1 - Server
python run_server.py

# Terminal 2 - Client
python run_client.py

# Terminal 3 - Manager
python run_manager.py
```

### Bước 2: Kết nối và điều khiển
1. Manager chọn Client trong danh sách
2. Click nút **"Screen"** để mở Remote Desktop
3. Đợi kết nối thành công (màn hình hiện video từ Client)
4. Click vào cửa sổ Remote Desktop để focus
5. Gõ phím bình thường → phím sẽ được gửi tới Client

### Bước 3: Test các phím
```
Test Case 1: Gõ text
- Mở Notepad trên Client
- Gõ "Hello World" trên Manager
- Kết quả: Text xuất hiện trên Notepad của Client

Test Case 2: Phím tắt
- Nhấn Ctrl+A trên Manager
- Kết quả: Chọn tất cả text trên Client

Test Case 3: Navigation
- Nhấn Arrow keys (← → ↑ ↓)
- Kết quả: Di chuyển cursor trên Client
```

## 🎨 Ví Dụ Thực Tế

### 1. Mở Notepad và gõ text
```
Manager: Win + R        → Mở Run dialog
Manager: notepad[Enter] → Mở Notepad
Manager: Hello World    → Gõ text
Manager: Ctrl + S       → Lưu file
```

### 2. Điều hướng File Explorer
```
Manager: Win + E        → Mở File Explorer
Manager: Arrow Down ↓   → Di chuyển xuống
Manager: Enter          → Mở folder
Manager: Alt + Left     → Quay lại
```

### 3. Copy-Paste
```
Manager: Ctrl + A       → Chọn tất cả
Manager: Ctrl + C       → Copy
Manager: Ctrl + V       → Paste
```

## 🔧 Kỹ Thuật Implementation

### Manager Side (manage_screen.py)

```python
def keyPressEvent(self, event: QKeyEvent):
    """Bắt sự kiện nhấn phím"""
    if event.isAutoRepeat():  # Tránh repeat
        return
    
    key_name = self._get_key_name(event)
    if key_name:
        self.input_event_generated.emit({
            "type": "key_press",
            "key": key_name
        })

def keyReleaseEvent(self, event: QKeyEvent):
    """Bắt sự kiện nhả phím"""
    if event.isAutoRepeat():
        return
    
    key_name = self._get_key_name(event)
    if key_name:
        self.input_event_generated.emit({
            "type": "key_release",
            "key": key_name
        })
```

### Client Side (client_input.py)

```python
def handle_input_pdu(self, pdu: dict):
    """Xử lý INPUT PDU từ Manager"""
    ev = pdu.get("input")
    t = ev.get("type")
    
    if t == "key_press":
        key = ev.get("key")
        pyautogui.keyDown(key, _pause=False)
    
    elif t == "key_release":
        key = ev.get("key")
        pyautogui.keyUp(key, _pause=False)
```

## 📊 Debug & Logging

### Console Output

**Manager:**
```
[ManageScreenWindow] Key Press: a
[ManageScreenWindow] Key Release: a
[Manager] Gửi input event: {'type': 'key_press', 'key': 'a'}
```

**Server:**
```
[ServerSession] Forward INPUT PDU: manager1 -> testuser
```

**Client:**
```
[DEBUG Input] Nhận PDU: {'type': 'input', 'input': {'type': 'key_press', 'key': 'a'}}
[ClientInputHandler] 🎹 Key Press: a
[ClientInputHandler] 🎹 Key Release: a
```

## ⚠️ Lưu Ý Quan Trọng

### 1. Focus Window
- Cửa sổ Remote Desktop phải được focus (click vào)
- Nếu không focus, phím sẽ không được bắt

### 2. Auto-Repeat
- Hệ thống tự động bỏ qua auto-repeat của phím giữ lâu
- Chỉ gửi 1 key_press và 1 key_release

### 3. Modifier Keys (Ctrl, Shift, Alt)
- Phải nhả đúng thứ tự: Ctrl + A → nhả A trước → nhả Ctrl sau
- pyautogui tự động xử lý các phím modifier

### 4. Special Characters
- Một số ký tự đặc biệt có thể cần Shift
- VD: "!" = Shift + 1 (tự động xử lý bởi pyautogui)

### 5. Keyboard Layout
- Sử dụng layout của Client
- Manager gửi key name, Client tự map theo layout

## 🐛 Troubleshooting

### Phím không hoạt động?

**Kiểm tra:**
1. ✅ Cửa sổ Remote Desktop đã focus chưa?
2. ✅ Session đã kết nối thành công chưa?
3. ✅ Console có log "Key Press" không?
4. ✅ Client có quyền `can_receive_remote_input()` không?

**Debug:**
```python
# Thêm log trong client_input.py
print(f"[DEBUG] Received key event: {ev}")
print(f"[DEBUG] Key type: {t}, Key: {ev.get('key')}")
```

### Phím bị "dính"?

**Nguyên nhân:** Key press gửi đi nhưng key release bị mất

**Giải pháp:**
1. Đóng/mở lại cửa sổ Remote Desktop
2. Hoặc nhấn phím đó lại 1 lần trên Client

### Phím đặc biệt không hoạt động?

**Nguyên nhân:** pyautogui không hỗ trợ một số phím OS-specific

**Giải pháp:**
- Kiểm tra tài liệu pyautogui: https://pyautogui.readthedocs.io/
- Thêm mapping đặc biệt trong `_get_key_name()`

## 📈 Performance

- **Latency:** ~50-100ms (network dependent)
- **Key rate:** Unlimited (throttle tự động bởi human typing speed)
- **Resource:** Minimal CPU/RAM usage

## 🔒 Security

- ✅ Kiểm tra permissions: `can_receive_remote_input()`
- ✅ Role-based access control
- ✅ Chỉ admin và user mới được điều khiển
- ✅ Viewer bị block

## 📝 Test Checklist

```
[ ] Gõ text bình thường (a-z, 0-9)
[ ] Phím đặc biệt (!@#$%^)
[ ] Phím tắt (Ctrl+A, Ctrl+C, Ctrl+V)
[ ] Navigation (Arrow keys, Home, End)
[ ] Function keys (F1-F12)
[ ] Modifier keys (Ctrl, Shift, Alt, Win)
[ ] Enter, Backspace, Delete
[ ] Tab, Space, Esc
[ ] Capslock, Numlock
```

---

**Version:** 1.0  
**Last Updated:** December 20, 2025  
**Status:** ✅ Production Ready
