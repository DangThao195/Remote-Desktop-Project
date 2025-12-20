# 🔐 Hướng Dẫn Sử Dụng Chức Năng Giám Sát Vi Phạm

## 📋 Tổng Quan

Hệ thống giám sát vi phạm tự động phát hiện khi Client truy cập các website/ứng dụng không được phép và gửi cảnh báo về Manager.

## 🎯 Luồng Hoạt Động

```
Client (Monitor Thread) → Server (Log + Forward) → Manager (Display + Log)
```

### 1. **Client Side** - Giám Sát Tự Động
- Thread `_monitor_loop()` chạy nền mỗi 2 giây
- Kiểm tra tiêu đề cửa sổ đang active
- So sánh với danh sách blacklist keywords
- Gửi cảnh báo khi phát hiện vi phạm

**Danh sách từ khóa cấm mặc định:**
```python
blacklist_keywords = [
    "phimmoi", "phim hay",           # Web phim lậu
    "bet88", "w88", "cá cược", "nhà cái",  # Web cá độ
    "xoilac", "trực tiếp bóng đá",   # Web bóng đá lậu
    "sex", "18+"                     # Web đồi trụy
]
```

**Mức độ giám sát theo Role:**
- `admin`: Không bị giám sát
- `user`: Giám sát cơ bản (medium level)
- `viewer`: Giám sát nghiêm ngặt (high level) - thêm game, facebook, youtube, netflix

### 2. **Server Side** - Ghi Log & Chuyển Tiếp

**Ghi log tại Server:**
- File: `log/security_alerts_YYYY-MM-DD.log`
- Format: `[timestamp] CLIENT: username | TYPE: violation_type | DETAIL: detail`
- Tự động tạo file mới mỗi ngày

**Chuyển tiếp về Manager:**
- ServerSession nhận PDU từ Client
- Ghi log vào file
- Forward PDU về Manager qua CHANNEL_CONTROL

### 3. **Manager Side** - Hiển Thị & Lưu Trữ

**Hiển thị trên GUI:**
- Cửa sổ "Keylogger" trong ManageClientsWindow
- Alert box màu đỏ với icon cảnh báo
- Hiển thị: Thời gian, Client, Loại vi phạm, Chi tiết

**Ghi log tại Manager:**
- File: `log/violations_YYYY-MM-DD.log`
- Format tương tự Server
- Tự động tạo file mới mỗi ngày

## 🚀 Cách Sử Dụng

### Bước 1: Khởi động hệ thống
```bash
# Terminal 1 - Server
python run_server.py

# Terminal 2 - Client (với user role)
python run_client.py

# Terminal 3 - Manager
python run_manager.py
```

### Bước 2: Kết nối Manager với Client
1. Chọn client trong danh sách
2. Click nút "Screen" để bắt đầu session
3. Click nút "Keylogger" để bật chế độ xem log

### Bước 3: Test chức năng
1. Trên máy Client, mở trình duyệt
2. Vào một trong các trang web trong blacklist:
   - VD: Tìm kiếm "xoilac" trên Google
   - Hoặc vào trang có từ "bóng đá" trong title
3. Quan sát Manager:
   - Alert màu đỏ xuất hiện trong vùng Keylogger
   - Hiển thị chi tiết vi phạm

### Bước 4: Kiểm tra log files

**Trên Server:**
```bash
cat log/security_alerts_2025-12-20.log
```

**Trên Manager:**
```bash
cat log/violations_2025-12-20.log
```

## 📊 Ví Dụ Output

### Manager GUI:
```
🚨 CẢNH BÁO VI PHẠM [14:30:45]
👤 Client: testuser
⚠️ Loại vi phạm: Web Cấm (xoilac)
📋 Chi tiết:
   Đang truy cập: Xem bóng đá trực tuyến - Xoilac TV
```

### Log File:
```
[2025-12-20 14:30:45] CLIENT: testuser | TYPE: Web Cấm (xoilac) | DETAIL: Đang truy cập: Xem bóng đá trực tuyến - Xoilac TV
```

## ⚙️ Tùy Chỉnh

### Thay đổi blacklist keywords:
File: `src/client/client.py` - Method `_monitor_loop()`

```python
blacklist_keywords = [
    "your_keyword_1",
    "your_keyword_2",
    # Thêm từ khóa của bạn
]
```

### Thay đổi tần suất kiểm tra:
```python
time.sleep(2)  # Thay đổi số giây giữa các lần kiểm tra
```

### Thêm mức độ giám sát cho role mới:
File: `src/client/client_permissions.py`

## 🐛 Troubleshooting

### Không thấy cảnh báo trên Manager?

**Kiểm tra:**
1. ✅ Client đã login với role `user` hoặc `viewer` (không phải `admin`)
2. ✅ Manager đã click nút "Keylogger" để bật hiển thị
3. ✅ Client đang trong session với Manager
4. ✅ Từ khóa có trong blacklist

**Debug:**
```bash
# Xem log trên Client
# Output sẽ có: "[Monitor] !!! PHÁT HIỆN VI PHẠM: ..."

# Xem log trên Server
tail -f log/security_alerts_*.log

# Xem log trên Manager
tail -f log/violations_*.log
```

### File log không được tạo?

**Nguyên nhân:** Thư mục `log/` chưa tồn tại hoặc không có quyền ghi

**Giải pháp:**
```bash
mkdir log
chmod 755 log
```

## 📝 Notes

- Chức năng chỉ hoạt động khi Client đang trong session với Manager
- Log files được tạo tự động theo ngày (YYYY-MM-DD)
- Mỗi vi phạm chỉ gửi cảnh báo 1 lần cho đến khi cửa sổ thay đổi
- Role `admin` không bị giám sát (bypass monitoring)

## 🔧 Các File Liên Quan

- `src/client/client.py` - Monitor loop logic
- `src/client/client_permissions.py` - Role-based monitoring levels
- `src/server/core/session.py` - Forward alerts to manager
- `src/server/server_logger.py` - Server-side logging
- `src/manager/gui/manage_clients.py` - Display alerts in GUI
- `src/manager/manager.py` - Handle alert signals

---

**Version:** 1.0  
**Last Updated:** December 20, 2025
