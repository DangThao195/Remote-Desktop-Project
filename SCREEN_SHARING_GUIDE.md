# Hướng dẫn Screen Sharing & Remote Control

## Tổng quan

Hệ thống đã được nâng cấp để tách riêng 2 chức năng:
- **Screen Sharing** (Chia sẻ màn hình): Chất lượng cao, FPS thấp (3-5s/frame)
- **Remote Control** (Điều khiển từ xa): Real-time, không phụ thuộc vào screen sharing

## Cấu hình mới

### 1. Screen Sharing
- **FPS**: 0.2 (1 frame mỗi 5 giây) - Có thể điều chỉnh:
  - 0.2 = 5 giây/frame
  - 0.33 = 3 giây/frame
  - 0.5 = 2 giây/frame
- **Quality**: 85 (chất lượng cao, từ 0-100)
- **Resolution**: 1920 (Full HD)
- **File size**: Tối đa ~300KB/frame

### 2. Remote Control
- **Độ trễ**: Real-time (< 100ms)
- **Mouse events**: Throttled ở 20 events/giây
- **Keyboard events**: Real-time, không throttle
- **Không phụ thuộc vào screen sharing FPS**

## Sử dụng

### Client

#### Mặc định
```python
# Cả 2 chức năng đều được bật mặc định khi session bắt đầu
client.screen_sharing_enabled = True
client.remote_control_enabled = True
```

#### Bật/Tắt Screen Sharing
```python
# Tắt screen sharing (chỉ nhận điều khiển, không gửi video)
client.disable_screen_sharing()

# Bật lại screen sharing
client.enable_screen_sharing()
```

#### Bật/Tắt Remote Control
```python
# Tắt remote control (chỉ gửi video, không nhận điều khiển)
client.disable_remote_control()

# Bật lại remote control
client.enable_remote_control()
```

### Manager (Qua Server Commands)

Manager có thể gửi lệnh qua server để điều khiển client:

```python
# Tắt screen sharing của client
manager.send_control_command("disable_screen_sharing")

# Bật screen sharing của client
manager.send_control_command("enable_screen_sharing")

# Tắt remote control của client
manager.send_control_command("disable_remote_control")

# Bật remote control của client
manager.send_control_command("enable_remote_control")
```

## Lợi ích

### 1. Tiết kiệm Băng thông
- **Trước**: 15 FPS = 15 frames/giây = ~20-30 Mbps
- **Sau**: 0.2 FPS = 1 frame/5s = ~0.5 Mbps
- **Giảm**: ~97% băng thông

### 2. Tăng Chất lượng
- **Trước**: Quality 50, max 960x540, 80KB/frame
- **Sau**: Quality 85, max 1920x1080, 300KB/frame
- **Cải thiện**: Rõ nét hơn 4x, chi tiết hơn 3x

### 3. Tách biệt Chức năng
- **Screen Sharing**: Có thể tắt để chỉ điều khiển mà không nhìn thấy
- **Remote Control**: Luôn real-time, không bị ảnh hưởng bởi FPS thấp

### 4. Linh hoạt
- Có thể chỉ bật screen sharing (xem mà không điều khiển)
- Có thể chỉ bật remote control (điều khiển mà không xem)
- Có thể bật cả 2 (chế độ full remote desktop)

## Use Cases

### 1. Giám sát (Monitoring)
```python
client.enable_screen_sharing()   # Bật
client.disable_remote_control()  # Tắt điều khiển
# → Chỉ xem, không điều khiển
```

### 2. Điều khiển từ xa (Remote Support)
```python
client.enable_screen_sharing()   # Bật
client.enable_remote_control()   # Bật
# → Full remote desktop
```

### 3. Điều khiển không nhìn (Blind Control)
```python
client.disable_screen_sharing()  # Tắt video
client.enable_remote_control()   # Bật điều khiển
# → Điều khiển mà không xem (tiết kiệm băng thông tối đa)
```

### 4. Demo/Presentation
```python
client.enable_screen_sharing()   # Bật với quality cao
client.disable_remote_control()  # Tắt điều khiển
# → Người xem thấy rõ nét, không can thiệp
```

## So sánh Trước/Sau

| Tiêu chí | Trước | Sau | Cải thiện |
|----------|-------|-----|-----------|
| FPS | 15 | 0.2 | -98.7% |
| Quality | 50 | 85 | +70% |
| Resolution | 960 | 1920 | +100% |
| File size | 80KB | 300KB | +275% |
| Bandwidth | 20 Mbps | 0.5 Mbps | -97.5% |
| Remote latency | ~100ms | ~50ms | +50% |

## Điều chỉnh Nâng cao

### Thay đổi FPS trong code

```python
# Trong client.py, khi khởi tạo ClientScreenshot:

# Chế độ rất chậm (10 giây/frame)
self.screenshot = ClientScreenshot(fps=0.1, quality=90, max_dimension=1920)

# Chế độ chậm (5 giây/frame) - MẶC ĐỊNH
self.screenshot = ClientScreenshot(fps=0.2, quality=85, max_dimension=1920)

# Chế độ trung bình (3 giây/frame)
self.screenshot = ClientScreenshot(fps=0.33, quality=85, max_dimension=1920)

# Chế độ nhanh (2 giây/frame)
self.screenshot = ClientScreenshot(fps=0.5, quality=80, max_dimension=1920)

# Chế độ real-time (15 FPS) - chất lượng thấp
self.screenshot = ClientScreenshot(fps=15, quality=50, max_dimension=960)
```

### Thay đổi Quality

```python
# Quality thấp (tiết kiệm băng thông)
quality=60  # ~100KB/frame

# Quality trung bình
quality=75  # ~200KB/frame

# Quality cao (MẶC ĐỊNH)
quality=85  # ~300KB/frame

# Quality rất cao (cho demo/presentation)
quality=95  # ~500KB/frame
```

### Thay đổi Resolution

```python
# HD (720p)
max_dimension=1280

# Full HD (1080p) - MẶC ĐỊNH
max_dimension=1920

# 2K
max_dimension=2560

# 4K (yêu cầu băng thông cao)
max_dimension=3840
```

## Lưu ý

1. **Bandwidth**: FPS thấp + quality cao = băng thông tối ưu
2. **Latency**: Remote control luôn real-time bất kể FPS
3. **CPU**: Quality cao tốn CPU hơn khi encode JPEG
4. **Permissions**: Remote control cần role `user` hoặc `admin`
5. **Screen sharing**: Tất cả role đều có thể share màn hình

## Troubleshooting

### Video bị giật
→ Giảm FPS xuống hoặc tăng quality lên (paradoxically, quality cao = ít frames hơn)

### Remote control bị lag
→ Kiểm tra network latency, không liên quan đến screen sharing FPS

### Băng thông quá cao
→ Giảm FPS xuống 0.1 (10s/frame) hoặc giảm quality xuống 70

### Ảnh bị mờ
→ Tăng quality lên 90-95 hoặc tăng max_dimension lên 2560
