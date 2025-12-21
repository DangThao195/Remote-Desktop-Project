# client/client_input.py

import pyautogui
import traceback
import time

class ClientInputHandler:
    """
    Lớp thụ động (passive), nhận PDU input đã được parse
    và thực thi chúng bằng pyautogui.
    """
    def __init__(self, logger=None):
        self.logger = logger or print

        pyautogui.FAILSAFE = False # Tắt tính năng đưa chuột về góc để dừng
        pyautogui.PAUSE = 0.0 # Tắt delay mặc định
        
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception as e:
            self.logger(f"Không thể lấy kích thước màn hình: {e}")
            self.screen_width, self.screen_height = 1920, 1080
        self.logger(f"Kích thước màn hình Client: {self.screen_width}x{self.screen_height}")
        
        # Track last mouse position để debug
        self.last_mouse_x = 0
        self.last_mouse_y = 0

    def handle_input_pdu(self, pdu: dict):
        """
        Được gọi bởi ClientNetwork khi có PDU input.
        """
        print(f"[ClientInputHandler] 📥 Nhận được PDU input: type={pdu.get('type')}")
        
        if pdu.get("type") != "input":
            print(f"[ClientInputHandler] ⚠️ PDU type không phải 'input': {pdu.get('type')}")
            return
            
        ev = pdu.get("input")
        if not ev:
            self.logger("[InputHandler] ⚠️ PDU input thiếu trường 'input'")
            return
        
        print(f"[ClientInputHandler] 🎮 Xử lý input event: {ev.get('type')}")
        
        # CRITICAL: Wrap toàn bộ logic trong try-catch để không crash
        try:
            t = ev.get("type")
            
            # --- XỬ LÝ TỌA ĐỘ CHUẨN HÓA ---
            norm_x = ev.get("x_norm")
            norm_y = ev.get("y_norm")
            
            abs_x, abs_y = None, None
            if norm_x is not None and norm_y is not None:
                # Validate normalized coordinates
                if not (0 <= norm_x <= 1 and 0 <= norm_y <= 1):
                    self.logger(f"[InputHandler] ⚠️ Tọa độ không hợp lệ: x={norm_x}, y={norm_y}")
                    return
                
                abs_x = int(norm_x * self.screen_width)
                abs_y = int(norm_y * self.screen_height)
                
                # [QUAN TRỌNG] Kẹp giá trị để không crash pyautogui
                abs_x = max(0, min(abs_x, self.screen_width - 1))
                abs_y = max(0, min(abs_y, self.screen_height - 1))
                
                # Update last position
                self.last_mouse_x = abs_x
                self.last_mouse_y = abs_y

            # --- XỬ LÝ CÁC LOẠI INPUT ---
            if t == "mouse_move":
                if abs_x is not None and abs_y is not None:
                    try:
                        pyautogui.moveTo(abs_x, abs_y, _pause=False)
                    except Exception as e:
                        self.logger(f"[InputHandler] ❌ Lỗi moveTo({abs_x}, {abs_y}): {e}")
            
            elif t == "mouse_click":
                try:
                    # Di chuyển chuột trước
                    if abs_x is not None and abs_y is not None:
                        pyautogui.moveTo(abs_x, abs_y, _pause=False)
                        # Thêm delay nhỏ để đảm bảo chuột đã đến vị trí
                        time.sleep(0.01)
                    
                    # Xử lý press/release
                    pressed = ev.get("pressed", True)
                    button = ev.get("button", "left")
                    
                    # Validate button
                    if button not in ["left", "right", "middle"]:
                        button = "left"
                    
                    if pressed:
                        pyautogui.mouseDown(button=button, _pause=False)
                        print(f"[ClientInputHandler] 🖱️ Mouse Down: {button} at ({abs_x}, {abs_y})")
                    else:
                        pyautogui.mouseUp(button=button, _pause=False)
                        print(f"[ClientInputHandler] 🖱️ Mouse Up: {button} at ({abs_x}, {abs_y})")
                        
                except Exception as e:
                    self.logger(f"[InputHandler] ❌ Lỗi mouse_click: {e}")
                    self.logger(f"[InputHandler] Debug: button={ev.get('button')}, pressed={ev.get('pressed')}, pos=({abs_x}, {abs_y})")
                    traceback.print_exc()

            elif t == "mouse_scroll":
                try:
                    delta = ev.get("delta", 0)
                    pyautogui.scroll(delta)
                except Exception as e:
                    self.logger(f"[InputHandler] ❌ Lỗi scroll: {e}")
            
            elif t == "key_press":
                key = ev.get("key", "")
                if key:
                    # print(f"[ClientInputHandler] 🎹 Key Press: {key}")  # Giảm spam
                    try:
                        pyautogui.keyDown(key, _pause=False)
                    except Exception as key_err:
                        # Nếu pyautogui không nhận diện key, thử press thay vì keyDown
                        try:
                            pyautogui.press(key, _pause=False)
                        except Exception as e:
                            self.logger(f"[InputHandler] ❌ Không thể nhấn phím: {key} - {e}")
            
            elif t == "key_release":
                key = ev.get("key", "")
                if key:
                    # print(f"[ClientInputHandler] 🎹 Key Release: {key}")  # Giảm spam
                    try:
                        pyautogui.keyUp(key, _pause=False)
                    except Exception as key_err:
                        # Một số phím không cần release (như press)
                        pass  # Bỏ qua lỗi release
            
            else:
                self.logger(f"[InputHandler] ⚠️ Loại input không xác định: {t}")
                
        except Exception as e:
            # CRITICAL: Bắt mọi lỗi để không crash connection
            self.logger(f"[InputHandler] ❌❌❌ LỖI NGHIÊM TRỌNG: {e}")
            self.logger(f"[InputHandler] PDU gây lỗi: {pdu}")
            traceback.print_exc()
            # KHÔNG raise exception để không crash ClientNetwork
