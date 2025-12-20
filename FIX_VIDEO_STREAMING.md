# 🔧 HƯỚNG DẪN SỬA LỖI VIDEO STREAMING

## ❌ CÁC LỖI ĐÃ TÌM THẤY

### 1. **Client không kết nối Main Server (Port 5000)**
- ✅ **ĐÃ SỬA**: Đã thêm logging và xử lý kết nối trong `client.py`
- ✅ **ĐÃ SỬA**: Đã cập nhật `server_config.py` để dùng IP `192.168.2.31`

### 2. **Manager đăng nhập thất bại**
- ❌ **ĐANG LỖI**: Manager đăng nhập với `Hung:123456` - user không tồn tại!
- ✅ **GIẢI PHÁP**: Dùng các user có sẵn trong database

### 3. **Client GUI crash**
- ✅ **ĐÃ SỬA**: Xử lý user_data có thể là tuple hoặc dict
- ✅ **ĐÃ SỬA**: Xử lý client_list trả về từ auth server

## 🔐 TÀI KHOẢN HỢP LỆ

### Cho Manager (có quyền quản lý):
```
Username: admin
Password: admin123
```

### Cho Client (người dùng bình thường):
```
Username: john_doe
Password: user123
```

## 📝 HƯỚNG DẪN CHẠY ĐÚNG

### **Bước 1: Khởi động Server**
```powershell
python run_server.py
```
Chờ thấy:
```
[ServerApp] Running on 0.0.0.0:5000
```

### **Bước 2: Chạy Client**
```powershell
python run_client.py
```

1. **Đăng nhập** với:
   - Username: `john_doe`
   - Password: `user123`

2. **Trong Client Panel**, click nút **"Bắt đầu dịch vụ"**
   - Sẽ thấy: `Trạng thái: Đang kết nối...`
   - Sau đó: `Trạng thái: Đã kết nối`

3. **Kiểm tra log server** - Phải thấy:
```
[ServerNetwork] Có kết nối thô từ ('IP', port)
[ServerNetwork] Handshake thành công cho DESKTOP-7KK6GLB@...
[SessionManager] Client registered: DESKTOP-7KK6GLB
```

### **Bước 3: Chạy Manager**
```powershell
python run_manager.py
```

1. **Đăng nhập** với:
   - Username: `admin`
   - Password: `admin123`

2. **Trong Manager**, bạn sẽ thấy client `DESKTOP-7KK6GLB` (hoặc tên máy client)

3. **Click vào client** để xem màn hình

4. **Kiểm tra log**:

**Log Manager:**
```
[ManagerReceiver] ✅ NHẬN VIDEO PDU: full Channel: 2
[ManagerApp] Xử lý VIDEO PDU: full
[Manager] Đang xử lý video PDU: full cho client: DESKTOP-7KK6GLB
[Manager] ✅ Đã xử lý và emit video frame, size: (1280, 720)
```

**Log Client:**
```
[Client] ==> Manager manager_gui_1 đã kết nối! Bắt đầu gửi video.
[Client] 📹 Gửi FULL frame #0, size: 45678 bytes
[Client] 📹 Gửi FULL frame #30, size: 34567 bytes
```

## 🐛 TROUBLESHOOTING

### Vấn đề 1: Client không xuất hiện trong danh sách Manager
**Nguyên nhân:** Client chưa kết nối main server (port 5000)

**Giải pháp:**
1. Kiểm tra Client đã click "Bắt đầu dịch vụ" chưa
2. Kiểm tra `config/server_config.py` - `CLIENT_PORT` phải là `5000`
3. Xem log server có dòng "Client registered" không

### Vấn đề 2: Manager không nhận được video
**Nguyên nhân:** Client chưa vào session

**Giải pháp:**
1. Kiểm tra log Client có dòng `==> Manager ... đã kết nối! Bắt đầu gửi video.` không
2. Nếu không có, kiểm tra server có gửi `session_started` không
3. Kiểm tra log server có lỗi forward PDU không

### Vấn đề 3: Đăng nhập thất bại
**Nguyên nhân:** Sai username/password hoặc chưa tạo user

**Giải pháp:**
1. Kiểm tra database có user không: `SELECT * FROM Users WHERE Username='admin';`
2. Dùng tài khoản trong phần "TÀI KHOẢN HỢP LỆ" ở trên
3. Hoặc tạo user mới bằng script trong `database/README_SAMPLE_DATA.md`

## ✅ CHECKLIST DEBUG

Khi gặp lỗi "không xem được màn hình", kiểm tra theo thứ tự:

- [ ] Server đã chạy và lắng nghe port 5000
- [ ] Client đã đăng nhập thành công
- [ ] Client đã click "Bắt đầu dịch vụ"
- [ ] Log server thấy "Client registered: DESKTOP-..."
- [ ] Manager đã đăng nhập thành công
- [ ] Manager thấy client trong danh sách
- [ ] Manager click vào client
- [ ] Log manager thấy "session_started"
- [ ] Log client thấy "Manager ... đã kết nối"
- [ ] Log client thấy "📹 Gửi FULL frame"
- [ ] Log manager thấy "✅ NHẬN VIDEO PDU"

Nếu bất kỳ bước nào FAIL, kiểm tra log chi tiết tại bước đó!

## 🎯 CODE ĐÃ THÊM DEBUG

Các file đã được thêm debug logging:
- `src/manager/manager_network/manager_receiver.py` - Log khi nhận video PDU
- `src/manager/manager_network/manager_app.py` - Log khi xử lý video PDU
- `src/manager/manager.py` - Log khi emit video frame
- `src/client/client.py` - Log khi gửi video frame

Những log này sẽ giúp bạn dễ dàng xác định vấn đề nằm ở đâu trong pipeline!
