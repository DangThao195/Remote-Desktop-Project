import sys
import os
import signal
import time
import threading
import logging
from pathlib import Path

# Lấy đường dẫn tuyệt đối của file server.py hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
# Thêm đường dẫn gốc của dự án vào sys.path nếu chưa có
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.server.server_constants import (
    SERVER_HOST, 
    SERVER_PORT, 
    CERT_FILE, 
    KEY_FILE, 
    USE_TLS,
    AUTH_SERVER_ENABLED,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE
)
from src.server.core.auth_server import start_server as start_auth_server 
from src.server.network.server_app import ServerApp

# ===== Setup Logging =====
def setup_logging():
    """Configure logging for the server"""
    # Create log directory if not exists
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
app = None

def main():
    global app
    
    logger.info("=" * 80)
    logger.info("Starting Unified Server")
    logger.info("=" * 80)
    
    # Check TLS configuration
    if USE_TLS:
        if not os.path.exists(CERT_FILE):
            logger.error(f"TLS enabled but certificate file not found: {CERT_FILE}")
            logger.error("Please create SSL certificate before running:")
            logger.error(f"  openssl req -x509 -newkey rsa:2048 -keyout {KEY_FILE} -out {CERT_FILE} -sha256 -days 365 -nodes")
            sys.exit(1)
        if not os.path.exists(KEY_FILE):
            logger.error(f"TLS enabled but key file not found: {KEY_FILE}")
            sys.exit(1)
        logger.info(f"TLS enabled - Using certificate: {CERT_FILE}")
    else:
        logger.warning("TLS disabled - Running in insecure mode (NOT recommended for production)")
    
    # Start Main Server
    try:
        logger.info(f"Starting Main Server at {SERVER_HOST}:{SERVER_PORT}")
        app = ServerApp(
            host=SERVER_HOST, 
            port=SERVER_PORT,
            certfile=CERT_FILE if USE_TLS else None,
            keyfile=KEY_FILE if USE_TLS else None
        )
        app.start()
        logger.info("Main Server started successfully")
    except Exception as e:
        logger.error(f"Failed to start Main Server: {e}", exc_info=True)
        sys.exit(1)

    # Start Auth Server (if enabled)
    if AUTH_SERVER_ENABLED:
        try:
            logger.info("Starting Auth Server in separate thread")
            auth_thread = threading.Thread(target=start_auth_server, daemon=True, name="AuthServer")
            auth_thread.start()
            logger.info("Auth Server thread started")
        except Exception as e:
            logger.error(f"Failed to start Auth Server: {e}", exc_info=True)
            logger.warning("Continuing without Auth Server")
    else:
        logger.info("Auth Server disabled in configuration")

    # Signal handlers for graceful shutdown
    def _term(signum, frame):
        logger.info("\n" + "=" * 80)
        logger.info("Shutdown signal received")
        logger.info("=" * 80)
        if app:
            logger.info("Stopping Main Server...")
            app.stop()
            logger.info("Main Server stopped")
        logger.info("Server shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGINT, _term)
    signal.signal(signal.SIGTERM, _term)

    logger.info("Server is running. Press Ctrl+C to stop.")
    
    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _term(None, None)

if __name__ == "__main__":
    main()