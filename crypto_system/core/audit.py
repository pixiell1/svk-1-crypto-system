import json
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict


class LogFormat(Enum):
    JSON = "json"
    CSV = "csv"
    CEF = "cef"


class EventCategory(Enum):
    AUTH = "authentication"
    ACCOUNT = "account_management"
    OBJECT = "object_action"


class EventStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class EventAction(Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    ACCESS = "access"
    CANCEL = "cancel"


class EventLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class LogRecord:
    event_datetime: str
    source_name: str
    user_account: str
    source_ip: str = ""
    host_ip: str = ""
    operation_start: str = ""
    operation_end: str = ""
    description: str = ""
    category: str = ""
    status: str = ""
    action: str = ""
    level: str = "info"

    def to_dict(self) -> dict:
        return asdict(self)


class Audit:
    def __init__(self, log_path: str, log_format: LogFormat,
                 max_file_size_mb: int = 100, cleanup_period_days: int = 30):
        self._log_path = log_path
        self._format = log_format
        self._max_size = max_file_size_mb * 1024 * 1024
        self._cleanup_days = cleanup_period_days
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    def log(self, source: str, user: str, description: str,
            category: EventCategory, status: EventStatus = None,
            action: EventAction = None, level: EventLevel = EventLevel.INFO,
            source_ip: str = "", host_ip: str = "",
            operation_start: str = "", operation_end: str = ""):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        record = LogRecord(
            event_datetime=now,
            source_name=source,
            user_account=user,
            source_ip=source_ip,
            host_ip=host_ip,
            operation_start=operation_start or now,
            operation_end=operation_end or now,
            description=description,
            category=category.value,
            status=status.value if status else "",
            action=action.value if action else "",
            level=level.value,
        )
        self._rotate_if_needed()
        self._write(record)

    def _write(self, record: LogRecord) -> None:
        if self._format == LogFormat.JSON:
            line = json.dumps(record.to_dict(), ensure_ascii=False)
        elif self._format == LogFormat.CSV:
            line = ",".join(f'"{v}"' for v in record.to_dict().values())
        elif self._format == LogFormat.CEF:
            d = record.to_dict()
            line = (f"CEF:0|App|App|1.0|{d['category']}|{d['description']}|"
                    f"{d['level']}|src={d['source_ip']} "
                    f"suser={d['user_account']} "
                    f"rt={d['event_datetime']}")
        else:
            raise ValueError("неизвестный формат лога")

        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _rotate_if_needed(self) -> None:
        if not os.path.exists(self._log_path):
            return
        if os.path.getsize(self._log_path) >= self._max_size:
            backup = self._log_path + ".1"
            if os.path.exists(backup):
                os.remove(backup)
            os.rename(self._log_path, backup)

    # ---- обёртки ----
    def auth_success(self, user: str, source_ip: str = ""):
        self.log("auth", user, "успешная аутентификация",
                 EventCategory.AUTH, EventStatus.SUCCESS,
                 level=EventLevel.INFO, source_ip=source_ip)

    def auth_failure(self, user: str, source_ip: str = ""):
        self.log("auth", user, "неуспешная аутентификация",
                 EventCategory.AUTH, EventStatus.FAILURE,
                 level=EventLevel.WARNING, source_ip=source_ip)

    def object_modify(self, user: str, obj: str):
        self.log("app", user, f"изменение объекта: {obj}",
                 EventCategory.OBJECT, action=EventAction.MODIFY,
                 level=EventLevel.WARNING)

    def object_delete(self, user: str, obj: str):
        self.log("app", user, f"удаление объекта: {obj}",
                 EventCategory.OBJECT, action=EventAction.DELETE,
                 level=EventLevel.WARNING)

    def critical(self, user: str, msg: str):
        self.log("app", user, msg, EventCategory.OBJECT,
                 level=EventLevel.CRITICAL)

    # ---- чтение ----
    def read_records(self, limit: int = 100) -> list[dict]:
        if not os.path.exists(self._log_path):
            return []
        records = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    if self._format == LogFormat.JSON:
                        records.append(json.loads(line))
                    else:
                        records.append({"raw": line})
                except Exception:
                    continue
        return records[-limit:]
    def clear_log(self):
        """Полностью очищает файл логов"""
        try:
            # Открываем файл на запись (это автоматически очистит его)
            with open(self._log_path, "w", encoding="utf-8") as f:
                f.write("")
            return True
        except Exception as e:
            print(f"Ошибка очистки лога: {e}")
            return False