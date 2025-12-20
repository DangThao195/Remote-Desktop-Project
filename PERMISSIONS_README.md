# HỆ THỐNG PHÂN QUYỀN CLIENT

## Tổng quan

Hệ thống phân quyền dựa trên thông tin người dùng từ database (bảng `Users`), với 3 role chính:

## Các Role và Quyền hạn

### 1. ADMIN (Quản trị viên)
**Quyền hạn đầy đủ, không bị giám sát**

✅ **Được phép:**
- Chia sẻ màn hình
- Nhận điều khiển từ xa (keyboard, mouse)
- Truyền file
- Hiển thị con trỏ chuột

❌ **Không bị:**
- Giám sát nội dung web/cửa sổ
- Chặn truy cập bất kỳ trang web nào

**Monitoring Level:** `none`

---

### 2. USER (Người dùng thông thường)
**Quyền hạn đầy đủ nhưng bị giám sát mức trung bình**

✅ **Được phép:**
- Chia sẻ màn hình
- Nhận điều khiển từ xa (keyboard, mouse)
- Truyền file
- Hiển thị con trỏ chuột

⚠️ **Bị giám sát:**
- Nội dung web/cửa sổ đang truy cập
- Phát hiện truy cập web cấm (phim lậu, cá độ, 18+, ...)
- Gửi cảnh báo lên server khi vi phạm

**Monitoring Level:** `medium`

**Blacklist cơ bản:**
- Web phim lậu: phimmoi, phim hay
- Web cá độ: bet88, w88, cá cược, nhà cái
- Web bóng đá lậu: xoilac, trực tiếp bóng đá
- Nội dung 18+: sex, 18+

---

### 3. VIEWER (Người xem - quyền hạn giới hạn)
**Chỉ được xem, không được điều khiển, bị giám sát nghiêm ngặt**

✅ **Được phép:**
- Chia sẻ màn hình (để người khác xem)

❌ **KHÔNG được phép:**
- ❌ Nhận điều khiển từ xa
- ❌ Truyền file
- ❌ Hiển thị con trỏ chuột

⚠️ **Bị giám sát nghiêm ngặt:**
- Tất cả nội dung web/cửa sổ
- Blacklist mở rộng (thêm game, social media, giải trí)
- Cảnh báo ngay lập tức mọi vi phạm

**Monitoring Level:** `high`

**Blacklist mở rộng (thêm so với user):**
- Tất cả blacklist của user
- Game
- Facebook, YouTube
- Netflix, Spotify

---

## Cấu trúc Database

```sql
CREATE TABLE Users (
    UserID VARCHAR(50) PRIMARY KEY,
    Username VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(255),
    Email VARCHAR(255) UNIQUE,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,    
    LastLogin TIMESTAMP NULL,
    Role ENUM('admin', 'user', 'viewer') NOT NULL  -- ← PHÂN QUYỀN TẠI ĐÂY
);
```

## Cách thức hoạt động

### 1. Đăng nhập
```python
# User đăng nhập qua GUI/Auth
user_info = client_connection.client_profile(token)

# user_info chứa:
# {
#     'UserID': 'user_001',
#     'Username': 'john_doe',
#     'Role': 'user',        # ← Lấy từ database
#     'FullName': 'John Doe',
#     ...
# }
```

### 2. Khởi tạo Client với phân quyền
```python
from src.client.client import Client

# Truyền user_info vào Client
client = Client(
    host="localhost",
    port=5000,
    user_info=user_info  # ← Chứa Role từ database
)

# Client tự động:
# 1. Đọc role từ user_info
# 2. Khởi tạo ClientPermissions(role)
# 3. Áp dụng các ràng buộc tương ứng
```

### 3. Kiểm tra quyền trong code
```python
# Client class sử dụng permissions
if self.permissions.can_receive_remote_input():
    # Cho phép nhận điều khiển từ xa
    self.network.on_input_pdu = self.input_handler.handle_input_pdu
else:
    # Chặn điều khiển từ xa
    self.network.on_input_pdu = self._on_input_pdu_blocked
```

### 4. Gửi thông tin lên Server
```python
# Khi login, Client gửi: "login:user_id:username:role"
login_cmd = f"login:{self.user_id}:{self.username}:{self.role}"
self.network.send_control_pdu(login_cmd)

# Server nhận được và biết role của client để xử lý phù hợp
```

## Ví dụ sử dụng

### Test với các role khác nhau

```python
# Test với User
user_info = {
    'UserID': 'user_001',
    'Username': 'john_doe',
    'Role': 'user'
}
client = Client("localhost", 5000, user_info=user_info)
client.start()
# → Được phép điều khiển, bị giám sát mức medium

# Test với Admin
admin_info = {
    'UserID': 'admin_001',
    'Username': 'admin',
    'Role': 'admin'
}
client = Client("localhost", 5000, user_info=admin_info)
client.start()
# → Được phép mọi thứ, KHÔNG bị giám sát

# Test với Viewer
viewer_info = {
    'UserID': 'viewer_001',
    'Username': 'viewer',
    'Role': 'viewer'
}
client = Client("localhost", 5000, user_info=viewer_info)
client.start()
# → CHỈ chia sẻ màn hình, bị giám sát nghiêm ngặt
```

## Module ClientPermissions

File: `src/client/client_permissions.py`

```python
from src.client.client_permissions import ClientPermissions

# Tạo permissions object
perms = ClientPermissions('user')

# Kiểm tra quyền
perms.can_share_screen()           # True
perms.can_receive_remote_input()   # True
perms.can_transfer_file()          # True
perms.is_monitored()               # True
perms.get_monitoring_level()       # 'medium'
```

## Luồng hoạt động đầy đủ

```
1. User đăng nhập → Auth Server
   ↓
2. Auth Server xác thực → Trả về token + user_info (có Role)
   ↓
3. GUI tạo ClientWindow với user_info
   ↓
4. ClientWindow khởi động Client Service với user_info
   ↓
5. Client.__init__() nhận user_info
   ↓
6. Client tạo ClientPermissions(role)
   ↓
7. Client áp dụng permissions:
   - Nếu can_receive_remote_input() → Cho phép điều khiển
   - Nếu can_transfer_file() → Cho phép truyền file
   - Nếu is_monitored() → Bật monitoring
   - Nếu can_see_cursor() → Hiển thị cursor
   ↓
8. Client gửi login:user_id:username:role lên Server
   ↓
9. Server nhận role và xử lý tương ứng
```

## Thay đổi Role

### Trong Database
```sql
-- Thay đổi role của user
UPDATE Users 
SET Role = 'admin'  -- hoặc 'user', 'viewer'
WHERE UserID = 'user_001';
```

### Trong Code (Test)
```python
# Trong __main__ của client.py
test_user_info = {
    'UserID': 'test_user_001',
    'Username': 'test_client',
    'Role': 'viewer'  # ← Thay đổi tại đây để test
}
```

## Mở rộng

### Thêm Permission mới
Chỉnh sửa `src/client/client_permissions.py`:

```python
ROLE_PERMISSIONS = {
    'admin': {
        'can_share_screen': True,
        'can_receive_remote_input': True,
        'can_transfer_file': True,
        'can_record_screen': True,  # ← Permission mới
        # ...
    },
    # ...
}
```

### Thêm Role mới
```python
ROLE_PERMISSIONS = {
    'admin': {...},
    'user': {...},
    'viewer': {...},
    'guest': {  # ← Role mới
        'can_share_screen': False,
        'can_receive_remote_input': False,
        'can_transfer_file': False,
        'is_monitored': True,
        'monitoring_level': 'high',
    }
}
```

## Lưu ý

1. **Bảo mật:** Role được lưu trong database, Client chỉ nhận và áp dụng
2. **Validation:** Server cần validate lại role khi nhận login command
3. **Logging:** Mọi hành động bị chặn đều được log và gửi về server
4. **Monitoring:** Chỉ áp dụng cho user và viewer, admin không bị giám sát
5. **Testing:** Dùng `python -m src.client.client_permissions` để test module

## Troubleshooting

**Vấn đề:** Client không bị giám sát dù role là 'user'
**Giải pháp:** Kiểm tra `is_monitored()` trong permissions

**Vấn đề:** Viewer vẫn nhận được điều khiển từ xa
**Giải pháp:** Kiểm tra callback `on_input_pdu` có được gán đúng không

**Vấn đề:** Role không được nhận diện
**Giải pháp:** Kiểm tra database có trả về đúng field 'Role' không
