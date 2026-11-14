import json
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
import os

def generate_keys_and_manifest():
    # Определяем базовую директорию (где лежит скрипт)
    base_dir = Path(__file__).parent.resolve()
    
    # 1. Генерируем ключи ECDSA
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    with open(base_dir / "public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    # 2. Считаем хэш main.py
    target = base_dir / "main.py"
    if not target.exists():
        print("Ошибка: main.py не найден!")
        return

    file_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    print(f"Хэш main.py: {file_hash}")

    # 3. Создаем и подписываем манифест
    manifest_data = {
        "version": "2.1.3",
        "files": {
            "main.py": file_hash
        }
    }
    manifest_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")

    with open(base_dir / "manifest.json", "wb") as f:
        f.write(manifest_bytes)

    signature = private_key.sign(manifest_bytes, ec.ECDSA(hashes.SHA256()))
    with open(base_dir / "manifest.sig", "wb") as f:
        f.write(signature)

    # 4. Обновляем SBOM
    components = [
        {
            "type": "file",
            "name": "main.py",
            "version": "2.1.3",
            "hashes": [
                {"alg": "SHA-256", "content": file_hash}
            ]
        }
    ]

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "timestamp": "2025-04-28T14:32:00Z",
            "component": {
                "name": "SVK-1",
                "version": "2.1.3",
                "type": "application"
            }
        },
        "components": components
    }

    with open(base_dir / "sbom.json", "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2, ensure_ascii=False)

    print(f"✅ Файлы созданы в: {base_dir}")

if __name__ == "__main__":
    generate_keys_and_manifest()