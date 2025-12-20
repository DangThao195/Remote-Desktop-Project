# 🚀 Hướng Dẫn Cấu Hình và Chạy Server

## ✅ Những Gì Đã Được Sửa

### 1. **Cấu Hình TLS Đầy Đủ**
   - Server giờ đã **BẬT TLS** theo mặc định
   - Kiểm tra file cert/key trước khi khởi động
   - Hỗ trợ tắt TLS qua config file

### 2. **Logging Chuyên Nghiệp**
   - Ghi log vào file: `log/server.log`
   - Hiển thị log ra console
   - Level: INFO (có thể thay đổi qua config)
   - Format: Timestamp + Name + Level + Message

### 3. **Config File JSON**
   - File: `config/server_config.json`
   - Quản lý tất cả cấu hình ở 1 nơi
   - Dễ thay đổi không cần sửa code

### 4. **Auth Server**
   - **GIỮ LẠI** - Đây là server riêng xử lý đăng nhập/đăng ký
   - Chạy trên port 5001 (riêng biệt với main server port 5000)
   - Có thể tắt qua config: `"enabled": false`

### 5. **Sửa Bug**
   - File `auth_server.py.py` → `auth_server.py`

---

## 📋 Cấu Trúc Config File

```json
{
  "server": {
    "host": "0.0.0.0",        // Lắng nghe tất cả interface
    "port": 5000,              // Port main server
    "use_tls": true,           // BẬT TLS (khuyến nghị)
    "cert_file": "src/server.crt",
    "key_file": "src/server.key"
  },
  "auth_server": {
    "enabled": true,           // Auth server (đăng nhập/đăng ký)
    "host": "0.0.0.0",
    "port": 5001
  },
  "database": {
    "host": "localhost",
    "user": "root",
    "password": "@Hung1012",
    "database": "pbl4"
  },
  "logging": {
    "level": "INFO",           // DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "log/server.log"
  },
  "limits": {
    "max_file_size": 10485760  // 10MB
  }
}
```

---

## 🔐 Tạo TLS Certificate (BẮT BUỘC)

### Windows (PowerShell):
```powershell
# Cài OpenSSL nếu chưa có:
# choco install openssl

openssl req -x509 -newkey rsa:2048 -keyout src/server.key -out src/server.crt -sha256 -days 365 -nodes -subj "/CN=localhost"
```

### Linux/Mac:
```bash
openssl req -x509 -newkey rsa:2048 -keyout src/server.key -out src/server.crt -sha256 -days 365 -nodes -subj "/CN=localhost"
```

**Lưu ý**: File cert phải ở đúng vị trí `src/server.crt` và `src/server.key` (hoặc sửa trong config)

---

## 🏃 Chạy Server

### 1. Kích hoạt Virtual Environment:
```powershell
D:\PBL\PBL4\venv\Scripts\Activate.ps1
```

### 2. Khởi động Server:
```powershell
python run_server.py
```

Hoặc trực tiếp:
```powershell
python src/server/server.py
```

### 3. Kiểm tra Log:
```powershell
# Xem log realtime
Get-Content log/server.log -Wait

# Hoặc mở file log/server.log trong VSCode
```

---

## 📊 Luồng Hoạt Động Hệ Thống

### **Server Startup:**
```
[server.py]
    ↓
main()
    ├── setup_logging() → Tạo logger
    ├── Check TLS cert/key files
    ├── Start Main Server (port 5000)
    │   ├── ServerApp.__init__()
    │   ├── ServerBroadcaster (thread gửi tin)
    │   ├── SessionManager (thread quản lý phiên)
    │   └── ServerNetwork (thread nhận kết nối)
    └── Start Auth Server (port 5001) [nếu enabled]
        └── Thread xử lý login/register
```

### **Client Connect:**
```
[Client] → Socket + X224 Handshake
    ↓
[Server] Accept connection
    ↓
Client send: "register:client"
    ↓
[Server] Lưu vào clients[client_id] = ROLE_CLIENT
    ↓
Broadcast client list → All managers
```

### **Manager Connect:**
```
[Manager] → Socket + X224 Handshake
    ↓
[Server] Accept connection
    ↓
Manager send: "register:manager"
    ↓
[Server] Lưu vào clients[manager_id] = ROLE_MANAGER
    ↓
Send client list → Manager này
```

### **Session (Manager ↔ Client):**
```
[Manager] Click "Connect to Client"
    ↓
Send: "connect:client_id"
    ↓
[Server] SessionManager
    ├── Check manager/client free
    └── Create ServerSession thread
        ├── Send "session_started" → Client
        └── Send "session_started" → Manager
            ↓
[Client] Start sending video frames
    ↓
[Server] Route frames: Client → Manager
    ↓
[Manager] Display video in ManagerViewer
```

---

## ⚙️ Tùy Chỉnh Config

### Tắt TLS (Chỉ để Test):
```json
{
  "server": {
    "use_tls": false,  // TẮT TLS
    ...
  }
}
```

### Tắt Auth Server:
```json
{
  "auth_server": {
    "enabled": false,  // TẮT auth server
    ...
  }
}
```

### Tăng Log Level:
```json
{
  "logging": {
    "level": "DEBUG",  // Chi tiết hơn
    ...
  }
}
```

---

## 🐛 Troubleshooting

### Lỗi: "Certificate file not found"
```bash
# Tạo cert mới:
openssl req -x509 -newkey rsa:2048 -keyout src/server.key -out src/server.crt -sha256 -days 365 -nodes
```

### Lỗi: "Address already in use"
```powershell
# Kiểm tra port đang dùng:
netstat -ano | findstr :5000

# Kill process:
taskkill /PID <PID> /F
```

### Lỗi: "Failed to start Auth Server"
- Kiểm tra port 5001 có bị dùng không
- Hoặc tắt auth server trong config: `"enabled": false`

### Client/Manager không kết nối được:
1. Kiểm tra TLS có **ĐỒNG BỘ** không (cả 3 phải cùng bật hoặc tắt)
2. Kiểm tra firewall cho phép port 5000 và 5001
3. Kiểm tra IP trong config của client/manager

---

## 📝 Auth Server - Giải Thích

### **Tác dụng:**
- Xử lý **đăng nhập** (login)
- Xử lý **đăng ký** (register)
- Quản lý **token** xác thực
- Lưu **MAC address** của client

### **Khi nào cần:**
- Hệ thống yêu cầu user phải login
- Cần quản lý quyền truy cập
- Cần theo dõi user nào đang online

### **Khi nào KHÔNG cần:**
- Test nội bộ không cần login
- Chỉ có 1-2 user cố định

### **Nếu không dùng:**
```json
{
  "auth_server": {
    "enabled": false
  }
}
```

---

## 📂 File Structure

```
PBL4/
├── config/
│   └── server_config.json         ← Config chính
├── src/
│   └── server/
│       ├── server.py              ← Main entry point
│       ├── server_constants.py    ← Load config + constants
│       ├── core/
│       │   ├── auth_server.py     ← Auth server (port 5001)
│       │   └── session_manager.py ← Quản lý phiên
│       └── network/
│           └── server_app.py      ← Main server (port 5000)
├── log/
│   └── server.log                 ← Log file
└── src/
    ├── server.crt                 ← TLS certificate
    └── server.key                 ← TLS private key
```

---

## ✅ Checklist Trước Khi Chạy Production

- [ ] Tạo TLS certificate
- [ ] `use_tls: true` trong config
- [ ] Đổi database password trong config
- [ ] `logging.level: INFO` hoặc `WARNING`
- [ ] Firewall cho phép port 5000, 5001
- [ ] Client và Manager **PHẢI DÙNG TLS** (đồng bộ với server)

---

## 🎯 Next Steps

1. **Test chạy server**: `python run_server.py`
2. **Kiểm tra log**: Xem `log/server.log`
3. **Test kết nối Client**: Chạy client từ máy khác
4. **Test kết nối Manager**: Chạy manager và xem danh sách client
5. **Test session**: Manager connect tới 1 client, xem video stream

Nếu có lỗi, kiểm tra log file hoặc hỏi tôi!
