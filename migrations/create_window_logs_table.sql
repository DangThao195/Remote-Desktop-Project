-- Tạo bảng window_logs để lưu window titles
CREATE TABLE IF NOT EXISTS window_logs (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    WindowTitle VARCHAR(500) NOT NULL,
    ProcessName VARCHAR(255) NOT NULL,
    ViewID VARCHAR(100) NOT NULL,
    LoggedAt DATETIME NOT NULL,
    INDEX idx_view_id (ViewID),
    INDEX idx_logged_at (LoggedAt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Thêm index cho query nhanh hơn
CREATE INDEX idx_view_logged ON window_logs(ViewID, LoggedAt);
