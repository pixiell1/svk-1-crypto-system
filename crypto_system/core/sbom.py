import json
from pathlib import Path


class SbomChecker:
    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self._data = {}

    def load(self) -> bool:
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            return True
        except Exception:
            return False

    def check_required_fields(self) -> bool:
        """Проверяет, что в SBOM есть базовые поля (формат CycloneDX)."""
        required = ["bomFormat", "specVersion", "components"]
        return all(k in self._data for k in required)

    def check_components_hashes(self, base_dir: str = ".") -> dict:
        """Сверяет хэши компонентов с реальными файлами."""
        results = {}
        for comp in self._data.get("components", []):
            name = comp.get("name")
            version = comp.get("version")
            hashes = comp.get("hashes", [])
            
            if not hashes:
                results[name] = False
                continue
                
            expected = next((h["content"] for h in hashes if h.get("alg") == "SHA-256"), None)
            if not expected:
                results[name] = False
                continue
                
            file_path = Path(base_dir) / name
            if not file_path.exists():
                results[name] = False
                continue

            import hashlib
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            results[name] = (h.hexdigest() == expected)

        return results