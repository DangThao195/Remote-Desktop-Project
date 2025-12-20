# Tài liệu Client Đã Tích Hợp (Merged Client)

## Tổng quan

Client đã được tích hợp hoàn toàn giữa front-end (GUI) và back-end (dịch vụ client). Giờ đây, tất cả chức năng được quản lý từ một giao diện duy nhất.

## Cấu trúc Tích hợp

### 1. Entry Point - `chat_client.py`
- Khởi động ứng dụng PyQt6
- Quản lý kết nối authentication
- Xử lý đăng nhập/đăng xuất

### 2. Client GUI - `src/gui/client_gui.py`
File này đã được **tích hợp hoàn toàn** với back-end client service:

#### Chức năng Front-end:
- Hiển thị thông tin client (IP, username)
- Quản lý danh sách kết nối
- Cho phép/từ chối kết nối từ manager
- Profile và logout

#### Chức năng Back-end (Mới thêm):
- **Bắt đầu/Dừng dịch vụ client**: Nút điều khiển dịch vụ
- **Giám sát trạng thái**: Hiển thị trạng thái kết nối real-time
- **Screenshot service**: Tự động chụp màn hình khi manager kết nối
- **Network service**: Kết nối TLS với server
- **Input handler**: Nhận và xử lý lệnh từ manager
- **Cursor tracking**: Theo dõi và gửi vị trí con trỏ
- **Security monitoring**: Giám sát nội dung cửa sổ (phát hiện web cấm)

### 3. Client Backend - `src/client/client.py`
Class `Client` cung cấp các dịch vụ:
- `ClientNetwork`: Quản lý kết nối TLS
- `ClientScreenshot`: Chụp màn hình với delta compression
- `ClientSender`: Gửi frame qua network
- `ClientInputHandler`: Xử lý input từ manager
- `ClientCursorTracker`: Theo dõi con trỏ
- Security Monitor: Giám sát cửa sổ đang active

## Cách Sử dụng

### Khởi động Client:
```bash
python chat_client.py
```

### Quy trình sử dụng:
1. **Đăng nhập**: Nhập username/password
2. **Client Panel**: Màn hình chính hiển thị
   - Thông tin IP của bạn
   - Danh sách các manager đã yêu cầu kết nối
   - Trạng thái dịch vụ
3. **Bắt đầu dịch vụ**: Click "Bắt đầu dịch vụ"
   - Client sẽ kết nối với server
   - Bắt đầu các dịch vụ monitoring
   - Trạng thái hiển thị: "Đang kết nối..." → "Đã kết nối"
4. **Quản lý kết nối**:
   - Khi manager yêu cầu kết nối, tên sẽ xuất hiện trong danh sách
   - Click "Cho phép" để chấp nhận
   - Click "Từ chối" để ngắt kết nối
5. **Dừng dịch vụ**: Click "Dừng dịch vụ" để ngắt kết nối

## Cấu hình

File: `config/server_config.py`
```python
SERVER_IP = "localhost"      # IP của server
SERVER_HOST = 5000           # Port chính của server
AUTH_HOST = 5001             # Port authentication
CLIENT_PORT = 5000           # Port cho client backend service
```

## Tính năng đã Tích hợp

### 1. Quản lý Trạng thái
- **Chưa kết nối**: Dịch vụ chưa khởi động
- **Đang kết nối**: Đang thiết lập kết nối với server
- **Đã kết nối**: Kết nối thành công, sẵn sàng
- **Kết nối thất bại**: Không thể kết nối đến server

### 2. Tự động Xử lý
- Khi manager kết nối → tự động bật screenshot service
- Khi manager ngắt kết nối → tạm dừng screenshot
- Tự động reconnect khi mất kết nối (nếu được cấu hình)

### 3. Security Features
- Giám sát cửa sổ đang active
- Phát hiện từ khóa cấm (web cá độ, phim lậu, etc.)
- Gửi cảnh báo lên server khi phát hiện vi phạm

### 4. Tối ưu hóa
- Delta compression cho video streaming
- Chất lượng JPEG điều chỉnh được
- FPS có thể cấu hình
- Buffer management tự động

## Xử lý Lỗi

### Không kết nối được server:
- Kiểm tra `SERVER_IP` và `CLIENT_PORT` trong config
- Đảm bảo server đang chạy
- Kiểm tra firewall/antivirus

### Thiếu file CA (ca.crt):
- Sao chép `server.crt` từ server
- Đổi tên thành `ca.crt`
- Đặt trong thư mục `src/client/`

### Lỗi dependencies:
```bash
pip install pygetwindow pillow pynput PyQt6
```

## So sánh với Cấu trúc Cũ

### Trước đây:
- Front-end (GUI) và back-end (client service) **tách biệt**
- Phải chạy 2 file riêng: `chat_client.py` và `src/client/client.py`
- Không có UI để quản lý dịch vụ

### Bây giờ:
- **Tích hợp hoàn toàn** trong một ứng dụng
- Chỉ cần chạy `chat_client.py`
- UI điều khiển đầy đủ: bật/tắt, theo dõi trạng thái
- Trải nghiệm người dùng tốt hơn

## API của ClientWindow

### Methods chính:
```python
def start_client_service(self)
    # Khởi động backend service (network, screenshot, monitoring)

def stop_client_service(self)
    # Dừng tất cả backend services

def toggle_client_service(self)
    # Bật/tắt service

def log_message(self, message)
    # Log messages từ backend

def closeEvent(self, event)
    # Xử lý khi đóng cửa sổ (tự động dừng service)
```

## Thread Management

Application sử dụng nhiều threads:
- **Main Thread**: PyQt6 GUI event loop
- **Client Service Thread**: Chạy `Client.start()`
- **Screenshot Thread**: Capture màn hình
- **Network Thread**: Nhận data từ server
- **Sender Thread**: Gửi frames
- **Cursor Thread**: Track cursor
- **Monitor Thread**: Security monitoring
- **Request List Thread**: Cập nhật danh sách kết nối

Tất cả background threads được đánh dấu `daemon=True` để tự động dừng khi main thread kết thúc.

## Lưu ý Kỹ thuật

1. **Thread-safe UI Updates**: Sử dụng `pyqtSignal` để update UI từ background threads
2. **Resource Cleanup**: `closeEvent` đảm bảo tất cả resources được giải phóng
3. **Error Handling**: Try-catch ở mọi điểm quan trọng
4. **Logging**: Tất cả actions được log để debug

## Tương lai

Có thể mở rộng:
- Thêm settings panel (FPS, quality, compression)
- Log viewer trong GUI
- Network statistics
- Performance monitoring
- Notification system

## Hỗ trợ

Nếu có vấn đề, kiểm tra:
1. Log messages trong console
2. File config đúng chưa
3. Server có đang chạy không
4. Firewall/antivirus có block không

---
**Phiên bản**: 1.0  
**Ngày cập nhật**: December 15, 2025
