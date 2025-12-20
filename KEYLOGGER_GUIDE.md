# 🔐 Hướng Dẫn Sử Dụng Keylogger Manager

## 📋 Tổng Quan

Tính năng Keylogger cho phép Manager theo dõi và xem báo cáo vi phạm từ các phím được gõ trên máy Client trong thời gian thực.

## 🎯 Tính Năng

### ✅ Hiện Tại
- ✅ Hiển thị log keylog trong ô vuông dưới các button
- ✅ Theo dõi realtime keylog từ Client
- ✅ Hiển thị thông tin:
  - ⏰ Thời gian ghi log
  - 📱 Tên cửa sổ (Window Title)
  - ⌨️ Nội dung phím đã gõ (KeyData)
- ✅ Giao diện đẹp với HTML formatting
- ✅ Auto-scroll tự động
- ✅ Font monospace để dễ đọc

### 🚀 Cách Sử Dụng

#### 1. Khởi động Manager
```powershell
python run_manager.py
```

#### 2. Chọn Client
- Trong cửa sổ **"Server Control Panel"**
- Click vào tên client trong danh sách bên trái

#### 3. Bật Keylogger
- Click button **"Keylogger"** (button đầu tiên)
- Ô action_area sẽ hiển thị header:
  ```
  🔐 KEYLOGGER - LOG BÁO CÁO VI PHẠM
  Client: <tên_client>
  Trạng thái: Đang theo dõi...
  ```

#### 4. Xem Log
- Log sẽ tự động hiển thị khi Client gõ phím
- Mỗi log entry hiển thị:
  ```
  🔴 [2025-12-20 10:30:45]
  📱 Cửa sổ: Microsoft Word - Document1
  ⌨️ Hello World
  ```

## 🎨 Giao Diện

### Action Area (Ô Hiển Thị Log)
```
┌─────────────────────────────────────────────┐
│  🔐 KEYLOGGER - LOG BÁO CÁO VI PHẠM       │
│  Client: DESKTOP-ABC123                     │
│  Trạng thái: Đang theo dõi...               │
├─────────────────────────────────────────────┤
│                                              │
│  🔴 [10:30:45]                              │
│  📱 Cửa sổ: Visual Studio Code              │
│  ⌨️ def hello_world():                      │
│                                              │
│  🔴 [10:30:50]                              │
│  📱 Cửa sổ: Google Chrome                   │
│  ⌨️ python tutorial                         │
│                                              │
│  (auto-scroll to bottom)                    │
└─────────────────────────────────────────────┘
```

### Màu Sắc
- 🟢 **SPOTIFY_GREEN** (`#1DB954`): Header, thời gian
- ⚪ **TEXT_LIGHT**: Nội dung chính
- 🟡 **Yellow**: Nội dung phím gõ (KeyData)
- ⚫ **CARD_BG**: Background của action area

## 📝 Chi Tiết Kỹ Thuật

### 1. Luồng Dữ Liệu
```
Client (Keylogger)
    ↓ INPUT PDU
Server (Relay)
    ↓ INPUT PDU
Manager (Receiver)
    ↓ _on_input_pdu()
Manager (Logic)
    ↓ input_pdu_received signal
ManageClientsWindow
    ↓ display_keylog()
Action Area (GUI)
```

### 2. Cấu Trúc INPUT PDU
```python
{
    "type": "input",
    "input": {
        "KeyData": "Hello",
        "WindowTitle": "Notepad",
        "ViewID": "DESKTOP-123",
        "LoggedAt": "2025-12-20 10:30:45"
    }
}
```

### 3. File Đã Chỉnh Sửa

#### `src/manager/manager_network/manager_app.py`
- ✅ Thêm `self.on_input_pdu = None`
- ✅ Xử lý INPUT PDU trong `_handle_pdu()`

#### `src/manager/manager.py`
- ✅ Thêm signal `input_pdu_received = pyqtSignal(object)`
- ✅ Thêm callback `_on_input_pdu()`
- ✅ Kết nối `self.app.on_input_pdu = self._on_input_pdu`
- ✅ Connect signal với GUI

#### `src/manager/gui/manage_clients.py`
- ✅ Thêm `self.buttons["Keylogger"].clicked.connect(self.view_keylogger)`
- ✅ Thêm hàm `view_keylogger()` - Hiển thị header
- ✅ Thêm hàm `display_keylog(pdu)` - Hiển thị log entry
- ✅ Style action_area với font monospace
- ✅ Sử dụng HTML formatting cho log đẹp

## 🐛 Xử Lý Lỗi

### Lỗi: "⚠️ Vui lòng chọn client trước!"
- **Nguyên nhân**: Chưa chọn client trong danh sách
- **Giải pháp**: Click vào tên client bên trái trước khi click button Keylogger

### Lỗi: Không nhận được log
- **Kiểm tra**:
  1. Client có đang chạy keylogger không?
  2. Manager có kết nối với Server không?
  3. Xem console log: `[Manager] INPUT PDU từ client: ...`

### Debug Log
```python
# Trong manager.py
print(f"[Manager] INPUT PDU từ client: {pdu.get('input')}")

# Trong manage_clients.py
print(f"[ManageClientsWindow] Lỗi hiển thị keylog: {e}")
import traceback
traceback.print_exc()
```

## 🔒 Bảo Mật

### Ứng Dụng Được Theo Dõi
Keylogger chỉ theo dõi các ứng dụng được phép:
```python
ALLOWED_APPS = [
    "WINWORD.EXE",      # Microsoft Word
    "notepad.exe",       # Notepad
    "Code.exe",          # VS Code
    "MySQLWorkbench.exe",
    "heidisql.exe"
]
```

### Lưu Trữ
- Log được lưu vào database: `keystrokes` table
- Chứa: KeyData, WindowTitle, ViewID, LoggedAt

## 📊 Database Schema

```sql
CREATE TABLE keystrokes (
    KeystrokeID INT AUTO_INCREMENT PRIMARY KEY,
    KeyData VARCHAR(255),
    WindowTitle VARCHAR(255),
    ViewID VARCHAR(100),
    LoggedAt DATETIME
);
```

## 🎉 Hoàn Thành!

Keylogger Manager đã sẵn sàng! Click button "Keylogger" để bắt đầu theo dõi log vi phạm từ Client.

### Screenshot Ví Dụ
```
[Keylogger] [Screen] [Control] [File Transfer] [All History]
┌────────────────────────────────────────────────────────┐
│  🔐 KEYLOGGER - LOG BÁO CÁO VI PHẠM                  │
│  Client: john_doe                                      │
│  ────────────────────────────────────────────────────  │
│                                                         │
│  🔴 [10:35:20]                                         │
│  📱 Cửa sổ: Password Manager.exe                      │
│  ⌨️ MySecretPassword123                               │
│                                                         │
│  🔴 [10:35:25]                                         │
│  📱 Cửa sổ: notepad.exe                               │
│  ⌨️ Confidential meeting notes                        │
└────────────────────────────────────────────────────────┘
```

## 📞 Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. Console logs (`python run_manager.py`)
2. Server logs (`python run_server.py`)
3. Client logs (`python run_client.py`)
