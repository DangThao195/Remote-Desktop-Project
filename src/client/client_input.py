# client/client_input.py

import pyautogui
import traceback

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

    def handle_input_pdu(self, pdu: dict):
        """
        Được gọi bởi ClientNetwork khi có PDU input.
        """
        print(f"[DEBUG Input] Nhận PDU: {pdu}")
        if pdu.get("type") != "input":
            return
            
        ev = pdu.get("input")
        if not ev:
            return
            
        try:
            t = ev.get("type")
            
            # --- NÂNG CẤP: XỬ LÝ TỌA ĐỘ CHUẨN HÓA ---
            norm_x = ev.get("x_norm")
            norm_y = ev.get("y_norm")
            
            abs_x, abs_y = None, None
            if norm_x is not None and norm_y is not None:
                abs_x = int(norm_x * self.screen_width)
                abs_y = int(norm_y * self.screen_height)
                
                # [QUAN TRỌNG] Kẹp giá trị để không crash pyautogui
                # Nếu abs_x = screen_width, pyautogui sẽ báo lỗi "out of bounds"
                abs_x = max(0, min(abs_x, self.screen_width - 1))
                abs_y = max(0, min(abs_y, self.screen_height - 1))

            if t == "mouse_move":
                if abs_x is not None and abs_y is not None:
                    # Tắt fail-safe của pyautogui để di chuột lên góc
                    pyautogui.moveTo(abs_x, abs_y, _pause=False)
            
            elif t == "mouse_click":
                # Sửa lỗi: pyautogui.click không nhận x, y trực tiếp
                # Chúng ta phải moveTo trước rồi click
                if abs_x is not None and abs_y is not None:
                    pyautogui.moveTo(abs_x, abs_y, _pause=False)
                
                # Xử lý press/release thay vì click
                pressed = ev.get("pressed", True)
                button = ev.get("button", "left")
                if pressed:
                    pyautogui.mouseDown(button=button, _pause=False)
                else:
                    pyautogui.mouseUp(button=button, _pause=False)

            elif t == "mouse_scroll":
                pyautogui.scroll(ev.get("delta", 0))
            
            elif t == "key_press":
                key = ev.get("key", "")
                if key:
                    print(f"[ClientInputHandler] 🎹 Key Press: {key}")
                    try:
                        pyautogui.keyDown(key, _pause=False)
                    except Exception as key_err:
                        # Nếu pyautogui không nhận diện key, thử press thay vì keyDown
                        try:
                            pyautogui.press(key, _pause=False)
                        except:
                            self.logger(f"[InputHandler] Không thể nhấn phím: {key} - {key_err}")
            
            elif t == "key_release":
                key = ev.get("key", "")
                if key:
                    print(f"[ClientInputHandler] 🎹 Key Release: {key}")
                    try:
                        pyautogui.keyUp(key, _pause=False)
                    except Exception as key_err:
                        # Một số phím không cần release (như press)
                        self.logger(f"[InputHandler] Không thể nhả phím: {key} - {key_err}")
                
        except Exception as e:
            self.logger(f"[InputHandler] Lỗi thực thi: {e}")
            traceback.print_exc()