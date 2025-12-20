"""
Manager Launcher - Chạy Manager (Người giám sát)
Chạy: python run_manager.py
"""
import sys
import os

sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    try:
        # Chạy manager trực tiếp
        import subprocess
        subprocess.run([sys.executable, "-m", "src.manager.manager"])
    except Exception as e:
        print(f'[Manager] Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
