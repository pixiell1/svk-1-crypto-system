import hashlib
import json
from pathlib import Path
from typing import Optional

# Для подписи используем cryptography (или bee2, если есть)
try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class IntegrityChecker:
    def __init__(self):
        self.algo = "sha256"

    def hash_file(self, path: str) -> str:
        h = hashlib.new(self.algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify_hash(self, path: str, expected_hash: str) -> bool:
        if not Path(path).exists():
            return False
        return self.hash_file(path) == expected_hash

    def verify_signature(self, data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
        """Проверка ЭЦП манифеста по открытому ключу (ECDSA P-256)."""
        if not HAS_CRYPTO:
            raise RuntimeError("Установите cryptography: pip install cryptography")
        
        try:
            public_key = serialization.load_pem_public_key(public_key_pem)
            public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False