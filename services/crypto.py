from cryptography.fernet import Fernet
import os

KEY_FILE = 'crypto.key'

def get_key():
    # Get or generate encryption key
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def encrypt_value(value: float) -> bytes:
    key = get_key()
    f = Fernet(key)
    return f.encrypt(str(value).encode())

def decrypt_value(token: bytes) -> float:
    key = get_key()
    f = Fernet(key)
    return float(f.decrypt(token).decode()) 