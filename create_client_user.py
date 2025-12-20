import sys
import os
sys.path.insert(0, os.getcwd())

from src.server.core import auth_handler

print('Creating client user...')
try:
    result = auth_handler.sign_up('client', 'client', 'Client User', 'client@example.com')
    print(f'Result: {result}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()