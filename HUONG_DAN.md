# HƯỚNG DẪN CHẠY ỨNG DỤNG

## 📋 Yêu cầu
1. Python 3.8+
2. MySQL Database đã cài đặt
3. Import dữ liệu: `mysql -u root -p < database/sample_data.sql`

## 🚀 CÁCH CHẠY

### Bước 1: Chạy Server
Mở terminal và chạy:
```bash
python run_server.py
```

Kết quả:
```
============================================================
KHOI DONG TAT CA SERVERS
============================================================

[Auth Server] Dang khoi dong tren port 5001...
[*] Server run 0.0.0.0:5001
[Main Server] Dang khoi dong tren port 5000...
[ServerApp] Running on 0.0.0.0:5000
```

### Bước 2: Chạy Client (Người bị giám sát)
Mở **terminal MỚI** và chạy:
```bash
python run_client.py
```

### Bước 3: Chạy Manager (Người giám sát)
Mở **terminal MỚI** và chạy:
```bash
python run_manager.py
```

Hoặc chạy trực tiếp:
```bash
python -m src.manager.manager
```

### Bước 4: Đăng nhập
**Client:**
- Màn hình đăng nhập sẽ hiện ra
- Nhập username/password (ví dụ: john_doe / user123)
- Click "Sign In"
- Chuyển sang màn hình Client Panel
- Click "Bắt đầu dịch vụ" để kết nối tới server

**Manager:**
- Nhập thông tin kết nối (host, port, username, password)
- Click "Connect"
- Chọn client muốn giám sát từ danh sách
- Click "Start Session" để bắt đầu giám sát

## 🔐 Tài khoản mẫu

### Admin (Full quyền, không bị giám sát)
```
Username: admin
Password: admin123
```

### User (Bị giám sát mức medium)
```
Username: john_doe
Password: user123
```

### Viewer (Chỉ xem, không điều khiển)
```
Username: guest_viewer
Password: viewer123
```

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Thứ tự chạy:** Server → Client → Manager
2. Database phải có dữ liệu mẫu
3. Nếu lỗi "Connection Refused", kiểm tra server đã chạy chưa
4. Server chạy 2 services:
   - Port 5001: Auth Server (đăng nhập)
   - Port 5000: Main Server (giám sát)
5. Client phải "Bắt đầu dịch vụ" TRƯỚC khi Manager có thể giám sát

## 🐛 Khắc phục lỗi

**Lỗi: Connection Refused**
→ Server chưa chạy, chạy lại: `python run_server.py`

**Lỗi: Port already in use**
→ Kill process: `taskkill /F /IM python.exe`

**Lỗi: Login failed**
→ Kiểm tra database có dữ liệu không

## 📚 Phân quyền
- **Admin:** Không bị giám sát, full quyền
- **User:** Bị giám sát web cấm (phim lậu, cá độ, 18+)
- **Viewer:** Chỉ xem, không điều khiển, giám sát nghiêm ngặt
