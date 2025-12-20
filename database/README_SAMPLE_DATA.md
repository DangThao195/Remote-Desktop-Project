# HƯỚNG DẪN SỬ DỤNG DỮ LIỆU MẪU

## 📦 Dữ liệu đã tạo

### 👥 Users (11 users)

#### Admin (2 users)
- **admin** / admin123
  - Email: admin@pbl4.com
  - Full Name: System Administrator
  
- **superadmin** / admin123
  - Email: superadmin@pbl4.com
  - Full Name: Super Admin

#### User (4 users)
- **john_doe** / user123
  - Email: john.doe@pbl4.com
  - Full Name: John Doe
  
- **jane_smith** / user123
  - Email: jane.smith@pbl4.com
  - Full Name: Jane Smith
  
- **mike_johnson** / user123
  - Email: mike.j@pbl4.com
  - Full Name: Mike Johnson
  
- **sarah_williams** / user123
  - Email: sarah.w@pbl4.com
  - Full Name: Sarah Williams

#### Viewer (3 users)
- **guest_viewer** / viewer123
  - Email: guest@pbl4.com
  - Full Name: Guest Viewer
  
- **intern_viewer** / viewer123
  - Email: intern@pbl4.com
  - Full Name: Intern Viewer
  
- **readonly_user** / viewer123
  - Email: readonly@pbl4.com
  - Full Name: Read Only User

---

## 🚀 Cách sử dụng

### 1. Tạo database và schema
```bash
mysql -u root -p < database/schema.sql
```

### 2. Import dữ liệu mẫu
```bash
mysql -u root -p < database/sample_data.sql
```

Hoặc trong MySQL Workbench:
1. Mở file `sample_data.sql`
2. Execute (Ctrl+Shift+Enter)

---

## 📊 Thống kê dữ liệu

- **Users:** 11 (2 admin, 4 user, 3 viewer, 2 manager)
- **Sessions:** 9 (3 đang active)
- **Views:** 5 (3 đang active)
- **Keystrokes:** 9 records
- **Screenshots:** 10 records
- **RemoteControls:** 9 records
- **FileTransfers:** 7 records

---

## 🎯 Kịch bản test

### Test 1: Đăng nhập với các role khác nhau

```python
# Admin login
python demo_client_roles.py
# Chọn option 1 (Admin)
# Username: admin
# Password: admin123

# User login
python demo_client_roles.py
# Chọn option 2 (User)
# Username: john_doe
# Password: user123

# Viewer login
python demo_client_roles.py
# Chọn option 3 (Viewer)
# Username: guest_viewer
# Password: viewer123
```

### Test 2: Kiểm tra sessions đang active

```sql
SELECT 
    u.Username,
    u.Role,
    s.Ip,
    s.StartTime,
    TIMESTAMPDIFF(MINUTE, s.StartTime, NOW()) AS MinutesActive
FROM Session s
JOIN Users u ON s.UserID = u.UserID
WHERE s.EndTime IS NULL
ORDER BY s.StartTime DESC;
```

### Test 3: Xem ai đang giám sát ai

```sql
SELECT 
    v.ViewID,
    u_client.Username AS ClientUsername,
    u_client.Role AS ClientRole,
    u_server.Username AS ServerUsername,
    u_server.Role AS ServerRole,
    v.Status,
    v.Note
FROM View v
JOIN Session s_client ON v.SessionClientId = s_client.SessionID
JOIN Session s_server ON v.SessionServerId = s_server.SessionID
JOIN Users u_client ON s_client.UserID = u_client.UserID
JOIN Users u_server ON s_server.UserID = u_server.UserID
WHERE v.Status = 'active';
```

### Test 4: Xem keystrokes của một user

```sql
SELECT 
    k.KeyData,
    k.WindowTitle,
    k.LoggedAt,
    u.Username
FROM Keystrokes k
JOIN View v ON k.ViewID = v.ViewID
JOIN Session s ON v.SessionClientId = s.SessionID
JOIN Users u ON s.UserID = u.UserID
ORDER BY k.LoggedAt DESC;
```

### Test 5: Kiểm tra vi phạm (web cấm)

```sql
-- Tìm keystrokes có từ khóa cấm
SELECT 
    u.Username,
    u.Role,
    k.KeyData,
    k.WindowTitle,
    k.LoggedAt
FROM Keystrokes k
JOIN View v ON k.ViewID = v.ViewID
JOIN Session s ON v.SessionClientId = s.SessionID
JOIN Users u ON s.UserID = u.UserID
WHERE k.KeyData LIKE '%phimmoi%'
   OR k.KeyData LIKE '%bet88%'
   OR k.WindowTitle LIKE '%phimmoi%'
   OR k.WindowTitle LIKE '%bet88%'
ORDER BY k.LoggedAt DESC;
```

### Test 6: File transfers theo user

```sql
SELECT 
    u.Username,
    u.Role,
    f.FileName,
    f.Direction,
    f.FileSize / 1024 AS FileSizeKB,
    f.TransferredAt
FROM FileTransfers f
JOIN View v ON f.ViewID = v.ViewID
JOIN Session s ON v.SessionClientId = s.SessionID
JOIN Users u ON s.UserID = u.UserID
ORDER BY f.TransferredAt DESC;
```

### Test 7: Remote controls theo view

```sql
SELECT 
    v.ViewID,
    u_server.Username AS Controller,
    u_client.Username AS ControlledUser,
    r.ActionType,
    r.ActionData,
    r.ExecutedAt
FROM RemoteControls r
JOIN View v ON r.ViewID = v.ViewID
JOIN Session s_client ON v.SessionClientId = s_client.SessionID
JOIN Session s_server ON v.SessionServerId = s_server.SessionID
JOIN Users u_client ON s_client.UserID = u_client.UserID
JOIN Users u_server ON s_server.UserID = u_server.UserID
ORDER BY r.ExecutedAt DESC;
```

---

## 🔍 Queries hữu ích

### Xem tất cả thông tin của một user

```sql
-- Thay 'john_doe' bằng username bạn muốn xem
SET @username = 'john_doe';

SELECT '=== USER INFO ===' AS '';
SELECT * FROM Users WHERE Username = @username;

SELECT '=== SESSIONS ===' AS '';
SELECT * FROM Session WHERE UserID = (SELECT UserID FROM Users WHERE Username = @username);

SELECT '=== VIEWS AS CLIENT ===' AS '';
SELECT v.* 
FROM View v
JOIN Session s ON v.SessionClientId = s.SessionID
WHERE s.UserID = (SELECT UserID FROM Users WHERE Username = @username);
```

### Dashboard tổng quan

```sql
SELECT 
    'Total Users' AS Metric,
    COUNT(*) AS Value
FROM Users
UNION ALL
SELECT 
    'Active Sessions',
    COUNT(*)
FROM Session
WHERE EndTime IS NULL
UNION ALL
SELECT 
    'Active Views',
    COUNT(*)
FROM View
WHERE Status = 'active'
UNION ALL
SELECT 
    'Total Keystrokes Today',
    COUNT(*)
FROM Keystrokes
WHERE DATE(LoggedAt) = CURDATE()
UNION ALL
SELECT 
    'Total File Transfers Today',
    COUNT(*)
FROM FileTransfers
WHERE DATE(TransferredAt) = CURDATE();
```

### Top active users

```sql
SELECT 
    u.Username,
    u.Role,
    COUNT(DISTINCT s.SessionID) AS TotalSessions,
    COUNT(DISTINCT v.ViewID) AS TimesViewed,
    MAX(s.StartTime) AS LastActive
FROM Users u
LEFT JOIN Session s ON u.UserID = s.UserID
LEFT JOIN View v ON s.SessionID = v.SessionClientId
GROUP BY u.UserID
ORDER BY TotalSessions DESC, TimesViewed DESC
LIMIT 10;
```

---

## 🧪 Test phân quyền

### Admin permissions
```sql
-- Admin có thể làm mọi thứ
SELECT 
    'Admin can do everything' AS Permission,
    COUNT(*) AS Count
FROM RemoteControls r
JOIN View v ON r.ViewID = v.ViewID
JOIN Session s ON v.SessionServerId = s.SessionID
JOIN Users u ON s.UserID = u.UserID
WHERE u.Role = 'admin';
```

### User permissions
```sql
-- User bị giám sát
SELECT 
    u.Username,
    COUNT(DISTINCT k.KeystrokeID) AS KeystrokesLogged,
    COUNT(DISTINCT sc.ScreenshotID) AS ScreenshotsTaken
FROM Users u
JOIN Session s ON u.UserID = s.UserID
JOIN View v ON s.SessionID = v.SessionClientId
LEFT JOIN Keystrokes k ON v.ViewID = k.ViewID
LEFT JOIN Screenshots sc ON v.ViewID = sc.ViewID
WHERE u.Role = 'user'
GROUP BY u.UserID;
```

### Viewer restrictions
```sql
-- Viewer KHÔNG có remote control hoặc file transfer
SELECT 
    'Viewer should have NO remote controls' AS Check,
    COUNT(*) AS Count
FROM RemoteControls r
JOIN View v ON r.ViewID = v.ViewID
JOIN Session s ON v.SessionServerId = s.SessionID
JOIN Users u ON s.UserID = u.UserID
WHERE u.Role = 'viewer';
-- Kết quả phải là 0
```

---

## 🛠️ Reset dữ liệu

Nếu muốn reset và import lại:

```sql
-- Xóa tất cả dữ liệu
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE FileTransfers;
TRUNCATE TABLE RemoteControls;
TRUNCATE TABLE Screenshots;
TRUNCATE TABLE Keystrokes;
TRUNCATE TABLE View;
TRUNCATE TABLE Session;
TRUNCATE TABLE Users;
SET FOREIGN_KEY_CHECKS = 1;

-- Sau đó chạy lại sample_data.sql
```

---

## 📝 Notes

- **Password hash:** Tất cả password đều sử dụng bcrypt hash giả định
  - Trong thực tế, bạn cần hash password đúng cách
  - Có thể dùng: `python -c "import bcrypt; print(bcrypt.hashpw(b'password', bcrypt.gensalt()).decode())"`

- **Timestamps:** Sử dụng `DATE_SUB(NOW(), INTERVAL ...)` để tạo dữ liệu trong quá khứ
  - Điều chỉnh theo nhu cầu test của bạn

- **File paths:** Đường dẫn file là giả định
  - Cần điều chỉnh theo cấu trúc thư mục thực tế

- **IP addresses:** Sử dụng dải IP private (192.168.x.x)
  - Điều chỉnh theo mạng của bạn

---

## 🎓 Bài tập mở rộng

1. Thêm 5 users mới với role khác nhau
2. Tạo một view mới với admin giám sát user mới
3. Thêm keystrokes có từ khóa vi phạm (phimmoi, bet88, ...)
4. Tạo query tìm user có nhiều vi phạm nhất
5. Tạo stored procedure để tự động log keystroke
6. Tạo trigger để tự động update LastLogin khi có session mới

---

**File:** `database/sample_data.sql`  
**Last Updated:** 2025-01-15  
**Version:** 1.0
