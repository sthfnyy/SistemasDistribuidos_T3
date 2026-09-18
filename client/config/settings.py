import os

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

API_URL = os.getenv("API_URL", f"http://{SERVER_HOST}:{SERVER_PORT}")