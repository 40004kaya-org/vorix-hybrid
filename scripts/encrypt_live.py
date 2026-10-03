#!/usr/bin/env python3
"""VORIX — رمزنگاری live.json با AES-256-GCM"""
import json, base64, os, sys
from pathlib import Path

PASSWORD = b"Alikaya19981998/_#"
SALT = b"vorix_salt_16byte"

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    print("❌ cryptography نصب نیست")
    sys.exit(1)

def make_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password)

LIVE = Path.home() / "vorix-hybrid/docs/data/live.json"
ENC  = Path.home() / "vorix-hybrid/docs/data/live.enc.json"

if not LIVE.exists():
    print(f"❌ {LIVE} not found")
    sys.exit(1)

with open(LIVE, "rb") as f:
    plaintext = f.read()

key = make_key(PASSWORD, SALT)
aes = AESGCM(key)
nonce = os.urandom(12)
ciphertext = aes.encrypt(nonce, plaintext, None)

blob = base64.b64encode(nonce + ciphertext).decode()

with open(ENC, "w") as f:
    json.dump({"v": 1, "blob": blob}, f)

print(f"✅ encrypted: {len(plaintext)} → {len(blob)} bytes")
print(f"   output: {ENC}")
