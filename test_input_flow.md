# Test Input Flow - Kiểm tra luồng điều khiển chuột/bàn phím

## Vấn đề đã phát hiện và sửa

### Nguyên nhân gốc rễ:
Server đang xử lý TẤT CẢ PDU có `type="input"` như keylog và return ngay lập tức, không cho session relay các PDU điều khiển từ manager tới client.

### Giải pháp:
Phân biệt keylog PDU (từ client) và control input PDU (từ manager) bằng cách kiểm tra field `KeyData`/`WindowTitle`:

```python
# Trong session_manager.py, hàm handle_pdu()
if pdu_type == "input":
    # Kiểm tra xem có phải keylog data không (có KeyData field)
    input_data = pdu.get('input', {})
    is_keylog = 'KeyData' in input_data or 'WindowTitle' in input_data
    
    # Nếu là keylog từ client → xử lý và forward tới manager
    if is_keylog:
        self._handle_input_pdu(client_id, pdu)
        return
    # Nếu là input điều khiển từ manager → forward tới client qua session
```

## Luồng điều khiển đúng:

1. **GUI (ManageScreenWindow)** → Bắt sự kiện chuột/bàn phím
   - Mouse: `handle_mouse_event()` → emit `input_event_generated`
   - Keyboard: `keyPressEvent()` / `keyReleaseEvent()` → emit `input_event_generated`

2. **Manager Logic** → Nhận từ GUI
   - Signal: `window.input_event_generated.connect(manager._on_gui_input)`
   - `_on_gui_input()` → `send_input_event()` → `input_handler.send_event()`

3. **ManagerInputHandler** → Gửi qua network
   - `send_event()` → `manager_app.send_input(event)`

4. **ManagerApp** → Đóng gói và gửi
   - `send_input()` → `builder.build_input_pdu()` → `_send_mcs_pdu(CHANNEL_INPUT, pdu)`

5. **Server (SessionManager)** → Nhận và phân loại
   - `handle_pdu()` → Kiểm tra `is_keylog`
   - Nếu KHÔNG phải keylog → Chuyển cho session

6. **ServerSession** → Relay tới client
   - `enqueue_pdu()` → Queue PDU
   - `run()` → `from_id == manager_id` → `MCSLite.build(CHANNEL_INPUT)` → `broadcaster.enqueue(client_id)`

7. **Client (ClientNetwork)** → Nhận và xử lý
   - Receiver → Parse PDU → `on_input_pdu()`
   - `ClientInputHandler.handle_input_pdu()` → `pyautogui.moveTo()` / `pyautogui.click()` / `pyautogui.press()`

## Cấu trúc PDU:

### Keylog PDU (từ Client):
```json
{
  "type": "input",
  "input": {
    "KeyData": "hello",
    "WindowTitle": "Notepad",
    "ClientID": "client123",
    "LoggedAt": "2025-12-21 10:30:00"
  }
}
```

### Control Input PDU (từ Manager):
```json
{
  "type": "input",
  "input": {
    "type": "mouse_move",
    "x_norm": 0.5,
    "y_norm": 0.5
  }
}
```

hoặc

```json
{
  "type": "input",
  "input": {
    "type": "key_press",
    "key": "a"
  }
}
```

## Kiểm tra:

1. ✅ GUI emit signal đúng
2. ✅ Manager nhận signal
3. ✅ ManagerApp gửi PDU
4. ✅ Server phân biệt keylog vs control input
5. ✅ Session relay input tới client
6. ❓ Client nhận và thực thi

## Cách test:

1. Chạy server: `python run_server.py`
2. Chạy client: `python run_client.py`
3. Chạy manager: `python run_manager.py`
4. Kết nối manager tới client
5. Mở màn hình remote (Screen button)
6. Di chuyển chuột/nhấn phím → Xem log console

### Log mong đợi:

**Manager:**
```
[ManageScreenWindow] 🖱️ Mouse event received, current_client_id=client123
[Manager] 🎮 Nhận được input event từ GUI: mouse_move
[Manager] ✅ Gửi input event tới input_handler
[ManagerApp] 📤 Gửi input event: mouse_move
```

**Server:**
```
[SessionManager] Nhận PDU type=input từ manager123
[SessionManager] INPUT không phải keylog, chuyển cho session
[ServerSession-manager123::client123] Relay input từ manager → client
```

**Client:**
```
[ClientInputHandler] 📥 Nhận được PDU input: type=input
[ClientInputHandler] 🎮 Xử lý input event: mouse_move
[ClientInputHandler] Mouse moved to (960, 540)
```

## Nếu vẫn không hoạt động:

1. Kiểm tra `current_session_client_id` có được set đúng không
2. Kiểm tra session có đang active không
3. Kiểm tra client có bật input handling không (permissions)
4. Xem log chi tiết ở console của cả 3 thành phần
