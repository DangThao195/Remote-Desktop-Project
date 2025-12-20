"""
Test script để kiểm tra tích hợp client
Chạy script này để verify các thành phần đã được merge đúng cách
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_imports():
    """Test tất cả imports cần thiết"""
    print("🔍 Testing imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 imported")
    except ImportError as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False
    
    try:
        from src.client.client import Client
        print("✅ Client backend imported")
    except ImportError as e:
        print(f"❌ Client backend import failed: {e}")
        return False
    
    try:
        from src.client.client import ClientWindow
        print("✅ ClientWindow GUI imported")
    except ImportError as e:
        print(f"❌ ClientWindow import failed: {e}")
        return False
    
    try:
        from src.client.auth import ClientConnection
        print("✅ ClientConnection imported")
    except ImportError as e:
        print(f"❌ ClientConnection import failed: {e}")
        return False
    
    try:
        from config import server_config
        print("✅ server_config imported")
        print(f"   - SERVER_IP: {server_config.SERVER_IP}")
        print(f"   - CLIENT_PORT: {server_config.CLIENT_PORT}")
    except ImportError as e:
        print(f"❌ server_config import failed: {e}")
        return False
    
    return True

def test_client_class():
    """Test Client class structure"""
    print("\n🔍 Testing Client class...")
    
    try:
        from src.client.client import Client
        
        # Check if Client has required methods
        required_methods = ['start', 'stop', '_login_to_server', '_monitor_loop']
        for method in required_methods:
            if hasattr(Client, method):
                print(f"✅ Client.{method} exists")
            else:
                print(f"❌ Client.{method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Client class test failed: {e}")
        return False

def test_gui_integration():
    """Test ClientWindow integration"""
    print("\n🔍 Testing ClientWindow integration...")
    
    try:
        from src.client.client import ClientWindow
        
        # Check if ClientWindow has backend integration methods
        required_methods = [
            'start_client_service',
            'stop_client_service',
            'toggle_client_service',
            'log_message'
        ]
        
        for method in required_methods:
            if hasattr(ClientWindow, method):
                print(f"✅ ClientWindow.{method} exists")
            else:
                print(f"❌ ClientWindow.{method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ ClientWindow integration test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n🔍 Testing dependencies...")
    
    dependencies = {
        'PIL': 'Pillow',
        'pynput': 'pynput',
        'pygetwindow': 'pygetwindow'
    }
    
    all_ok = True
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed - run: pip install {package}")
            all_ok = False
    
    return all_ok

def test_file_structure():
    """Test required files exist"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        'chat_client.py',
        'src/client/client.py',
        'src/client/auth.py',
        'config/server_config.py'
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 60)
    print("  TEST TÍCH HỢP CLIENT (FRONT-END + BACK-END)")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Client Class", test_client_class),
        ("GUI Integration", test_gui_integration),
        ("Dependencies", test_dependencies)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("\n" + "=" * 60)
    print(f"  TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 Tất cả tests đều PASS! Client đã được tích hợp thành công!")
        print("\n📝 Các bước tiếp theo:")
        print("   1. Đảm bảo server đang chạy")
        print("   2. Chạy: python chat_client.py")
        print("   3. Đăng nhập và click 'Bắt đầu dịch vụ'")
        return 0
    else:
        print("\n⚠️ Một số tests FAILED. Vui lòng kiểm tra lại!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
