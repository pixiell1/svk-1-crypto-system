import json
import os
from dataclasses import dataclass


@dataclass
class LoggingConfig:
    log_path: str = "logs/security.log"
    log_format: str = "json"
    cleanup_period: str = "30d"
    max_file_size: str = "100MB"


@dataclass
class CryptoConfig:
    encryption: str = "AES-256-GCM"
    hashing: str = "SHA-256"
    digital_signature: str = "ECDSA-P256"


@dataclass
class AppConfig:
    logging: LoggingConfig
    crypto: CryptoConfig


class ConfigLoader:
    def __init__(self, path: str):
        self._path = path

    def load(self) -> AppConfig:
        if not os.path.exists(self._path):
            cfg = self.create_default()
            self.save(cfg)
            return cfg

        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return AppConfig(
            logging=LoggingConfig(**data.get("logging", {})),
            crypto=CryptoConfig(**data.get("crypto", {})),
        )

    def save(self, cfg: AppConfig) -> None:
        data = {
            "logging": cfg.logging.__dict__,
            "crypto": cfg.crypto.__dict__,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create_default() -> AppConfig:
        return AppConfig(
            logging=LoggingConfig(),
            crypto=CryptoConfig(),
        )