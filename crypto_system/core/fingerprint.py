import hashlib
import subprocess
import platform
import uuid

class SystemFingerprint:
    def __init__(self):
        self._components = {}
        self._fingerprint = None

    def _run_wmic(self, query: str) -> str:
        """Выполняет WMIC-запрос и возвращает результат (только для Windows)"""
        try:
            # Используем PowerShell для надежности (WMIC устарел в Win11)
            cmd = ["powershell", "-Command", f"Get-CimInstance {query} | Select-Object -ExpandProperty SerialNumber"]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
            return result.strip()
        except Exception:
            return "UNKNOWN"

    def collect(self) -> str:
        """Собирает данные о железе и возвращает SHA-256 хэш"""
        parts = []

        # 1. Имя компьютера и ОС
        parts.append(platform.node())
        parts.append(platform.system())

        # 2. MAC-адрес (используем uuid.getnode(), который берет MAC первой сетевой карты)
        mac = f"{uuid.getnode():012X}"
        parts.append(mac)

        # 3. Серийный номер материнской платы (Windows)
        if platform.system() == "Windows":
            baseboard_sn = self._run_wmic("Win32_BaseBoard")
            parts.append(baseboard_sn)

            # 4. UUID системы (уникальный ID от производителя)
            system_uuid = self._run_wmic("Win32_ComputerSystemProduct")
            parts.append(system_uuid)

            # 5. Серийный номер процессора
            cpu_id = self._run_wmic("Win32_Processor")
            parts.append(cpu_id)

            # 6. Серийный номер диска C:
            disk_sn = self._run_wmic("Win32_DiskDrive")
            parts.append(disk_sn)
        else:
            # Для Linux (если будешь тестировать там)
            try:
                with open("/etc/machine-id", "r") as f:
                    parts.append(f.read().strip())
            except Exception:
                parts.append("UNKNOWN_LINUX_ID")

        # Объединяем всё в одну строку
        raw_string = "|".join(parts)
        self._components = {
            "hostname": parts[0],
            "os": parts[1],
            "mac": parts[2],
            "board_sn": parts[3] if len(parts) > 3 else "",
            "system_uuid": parts[4] if len(parts) > 4 else "",
            "cpu_sn": parts[5] if len(parts) > 5 else "",
            "disk_sn": parts[6] if len(parts) > 6 else ""
        }

        # Хэшируем по SHA-256
        h = hashlib.sha256(raw_string.encode("utf-8"))
        self._fingerprint = h.hexdigest()
        return self._fingerprint

    def get_fingerprint(self) -> str:
        if not self._fingerprint:
            self.collect()
        return self._fingerprint

    def get_details(self) -> dict:
        """Возвращает сырые данные (для отладки или вывода в интерфейс)"""
        if not self._fingerprint:
            self.collect()
        return self._components