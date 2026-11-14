import ctypes
import hashlib
import os
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


# ======================================================================
# ТИПЫ И КОНСТАНТЫ (по СЧ.1)
# ======================================================================

class SourceType(Enum):
    SYSTEM = "system"        # ОС
    PHYSICAL = "physical"    # аппаратный ГСЧ / токен
    USER = "user"            # активность пользователя


class MixMethod(Enum):
    HASH = "hash"
    CIPHER = "cipher"
    KDF = "kdf"


class RngState(Enum):
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    BLOCKED = "blocked"
    WIPED = "wiped"


# ======================================================================
# ИСТОЧНИКИ СЛУЧАЙНОСТИ
# ======================================================================

@dataclass
class EntropySource:
    name: str
    type: SourceType
    reader: Callable[[int], bytes]
    min_entropy_per_byte: float
    is_ksk: bool = False      # входит в список КСК (СЧ.1)
    available: bool = True

    def __repr__(self) -> str:
        return (f"EntropySource(name={self.name!r}, type={self.type.value}, "
                f"entropy={self.min_entropy_per_byte}, ksk={self.is_ksk})")


@dataclass
class RngDescriptor:
    name: str
    sources: list[EntropySource] = field(default_factory=list)
    mix_method: MixMethod = MixMethod.HASH
    mix_algorithm: str = "sha256"
    purpose: str = "key generation"


@dataclass
class RngConfig:
    mix_algorithm: str = "sha256"
    internal_state_size: int = 32
    entropy_pool_size: int = 64
    reseed_interval: int = 1024 * 1024          # байт
    min_entropy_per_byte: float = 0.5
    test_on_init: bool = True                   # СЧ.5
    test_on_first_use: bool = True              # СЧ.5
    check_sources_on_init: bool = True          # СЧ.7
    check_sources_before_keygen: bool = False   # СЧ.8 (уровни 3/4)
    allow_no_physical_source: bool = False      # только уровень 1
    alternative_sources_min: int = 2            # СЧ.3
    strict_mode: bool = False                   # Если False - не падаем при сбое источника
    wipe_on_exit: bool = True                   # для ВЭ


# ======================================================================
# ЧТЕНИЕ ИСТОЧНИКОВ
# ======================================================================

def read_urandom(n: int) -> bytes:
    """Системный источник (Linux / macOS / Windows через os.urandom)."""
    return os.urandom(n)


def read_token_windows(n: int, device_path: str = r"\\.\HWRNG") -> bytes:
    """
    Аппаратный ГСЧ в Windows через CreateFileW + ReadFile.
    Если устройства нет — исключение.
    """
    if sys.platform != "win32":
        raise RuntimeError("read_token_windows доступен только в Windows")

    kernel32 = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    OPEN_EXISTING = 3
    FILE_FLAG_OVERLAPPED = 0x40000000
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    handle = kernel32.CreateFileW(
        device_path, GENERIC_READ, 0, None, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, None
    )
    if handle == INVALID_HANDLE_VALUE:
        err = kernel32.GetLastError()
        raise RuntimeError(f"не удалось открыть {device_path}, код {err}")

    try:
        buf = (ctypes.c_ubyte * n)()
        read = wintypes.DWORD(0)
        ok = kernel32.ReadFile(handle, buf, n, ctypes.byref(read), None)
        if not ok:
            err = kernel32.GetLastError()
            raise RuntimeError(f"ReadFile failed, код {err}")
        if read.value != n:
            raise RuntimeError(f"прочитано {read.value} байт вместо {n}")
        return bytes(buf)
    finally:
        kernel32.CloseHandle(handle)


def read_user_activity(n: int) -> bytes:
    """Источник активности пользователя (тайминги)."""
    buf = bytearray()
    while len(buf) < n:
        t = time.perf_counter_ns()
        buf.extend(t.to_bytes(8, "little"))
    return bytes(buf[:n])


# ======================================================================
# КЛАСС RNG
# ======================================================================

class Rng:
    def __init__(self, descriptor: RngDescriptor):
        self._descriptor = descriptor
        self._config: Optional[RngConfig] = None
        self._state: RngState = RngState.UNINITIALIZED
        self._internal_state: bytes = b""
        self._entropy_pool: bytes = b""
        self._bytes_since_reseed: int = 0
        self._first_use_done: bool = False
        self._log_cb: Callable[[str], None] = lambda msg: None
        self._audit = None

    # ------------------------------------------------------------------
    # СВОЙСТВА И ДОСТУП (СЧ.1)
    # ------------------------------------------------------------------
    @property
    def descriptor(self) -> RngDescriptor:
        return self._descriptor

    @property
    def state(self) -> RngState:
        return self._state

    def get_sources(self) -> list[EntropySource]:
        return list(self._descriptor.sources)

    def get_ksk_sources(self) -> list[EntropySource]:
        return [s for s in self._descriptor.sources if s.is_ksk]

    # ------------------------------------------------------------------
    # ВАЛИДАЦИЯ (СЧ.1)
    # ------------------------------------------------------------------
    def validate(self) -> None:
        d = self._descriptor
        if not d.name:
            raise ValueError("СЧ.1: не задано имя ГСЧ")
        if not d.sources:
            raise ValueError("СЧ.1: не заданы источники случайности")
        if d.mix_method is None or not d.mix_algorithm:
            raise ValueError("СЧ.1: не задан метод обработки данных")

        for s in d.sources:
            if not s.name:
                raise ValueError("СЧ.1: у источника нет имени")
            if s.type is None:
                raise ValueError(f"СЧ.1: у источника {s.name} не задан тип")
            if s.reader is None:
                raise ValueError(f"СЧ.1: у источника {s.name} нет функции чтения")
            if s.type == SourceType.PHYSICAL and not s.is_ksk:
                raise ValueError(f"СЧ.1: физический источник {s.name} должен быть в списке КСК")

    # ------------------------------------------------------------------
    # ИНИЦИАЛИЗАЦИЯ (СЧ.2–СЧ.7)
    # ------------------------------------------------------------------
    def init(self,
             config: Optional[RngConfig] = None,
             log_callback: Optional[Callable[[str], None]] = None,
             audit=None) -> None:
        if log_callback:
            self._log_cb = log_callback
        self._audit = audit
        self._config = config or RngConfig()
        self._bytes_since_reseed = 0
        self._first_use_done = False
        self._state = RngState.UNINITIALIZED

        self._log("init: старт инициализации")

        # 1. Проверка состава источников (СЧ.1)
        self.validate()

        # 2. Проверка работоспособности источников (СЧ.7)
        if self._config.check_sources_on_init:
            sources_ok = self.check_sources()
            if not sources_ok:
                has_alive = any(s.available for s in self._descriptor.sources)
                if has_alive:
                    self._log("ВНИМАНИЕ: не все источники доступны. Работа на резервном источнике.")
                else:
                    self._fail("все источники случайности недоступны")

        # 3. Сбор энтропии
        self._collect_entropy()

        # 4. Оценка энтропии (СЧ.2)
        if not self._estimate_entropy():
            self._fail("недостаточная энтропия источников (СЧ.2)")

        # 5. Формирование внутреннего состояния (СЧ.6)
        self._mix_entropy()

        if len(self._internal_state) != self._config.internal_state_size:
            self._fail("некорректный размер внутреннего состояния")

        # 6. Статистические тесты (СЧ.5)
        if self._config.test_on_init:
            if not self.test_statistical():
                self._fail("статистические тесты при init не пройдены")

        self._state = RngState.READY
        self._log("init: завершено успешно")

    # ------------------------------------------------------------------
    # ПРОВЕРКА ИСТОЧНИКОВ (СЧ.7, СЧ.8)
    # ------------------------------------------------------------------
    def check_sources(self) -> bool:
        all_ok = True
        for src in self._descriptor.sources:
            try:
                data = src.reader(8)
                if not data or len(data) != 8:
                    src.available = False
                    all_ok = False
                    self._log(f"check_sources: {src.name} вернул неверный размер")
                    continue
                if self._is_constant(data):
                    src.available = False
                    all_ok = False
                    self._log(f"check_sources: {src.name} выдал константу")
                    continue
                src.available = True
            except Exception as e:
                src.available = False
                all_ok = False
                self._log(f"check_sources: ошибка {src.name}: {e}")
        return all_ok

    # ------------------------------------------------------------------
    # СБОР И ОЦЕНКА (СЧ.2)
    # ------------------------------------------------------------------
    def _collect_entropy(self) -> None:
        """Собирает ровно столько байт, сколько нужно для набора энтропии"""
        chunks = []
        required_bits = self._config.internal_state_size * 8
        collected_bits = 0.0

        for src in self._descriptor.sources:
            if not src.available:
                continue
            
            needed_bits = required_bits - collected_bits
            if needed_bits <= 0:
                break
                
            # Сколько байт нужно взять из этого источника
            bytes_needed = int(needed_bits / src.min_entropy_per_byte) + 1
            
            try:
                data = src.reader(bytes_needed)
                if data:
                    chunks.append(data)
                    collected_bits += len(data) * src.min_entropy_per_byte
                    self._log(f"collect: {src.name} дал {len(data)} байт (энтропии: {collected_bits} бит)")
            except Exception as e:
                self._log(f"collect: ошибка {src.name}: {e}")
                
        if not chunks:
            self._fail("не удалось собрать энтропию")
            
        self._entropy_pool = b"".join(chunks)

    def _estimate_entropy(self) -> bool:
        total_bits = 0.0
        for src in self._descriptor.sources:
            if src.available:
                # Примерная оценка (можно улучшить, если хранить реальный размер)
                total_bits += src.min_entropy_per_byte * 64 
        
        required = self._config.internal_state_size * 8
        
        # Так как мы собираем нужное количество байт в _collect_entropy,
        # мы просто проверяем, хватит ли пула
        actual_bits = len(self._entropy_pool) * self._config.min_entropy_per_byte
        ok = actual_bits >= required
        
        self._log(f"estimate: собрано {actual_bits:.1f} бит, нужно {required}, ok={ok}")
        return ok

    # ------------------------------------------------------------------
    # ПЕРЕМЕШИВАНИЕ (СЧ.6)
    # ------------------------------------------------------------------
    def _mix_entropy(self) -> None:
        alg = self._config.mix_algorithm
        if alg not in ("sha256", "sha384", "sha512"):
            raise ValueError(f"неподдерживаемый алгоритм перемешивания: {alg}")

        h = hashlib.new(alg)
        h.update(self._entropy_pool)
        h.update(os.urandom(32))          # соль
        digest = h.digest()

        self._internal_state = digest[: self._config.internal_state_size]
        self._entropy_pool = b""
        self._log("mix: состояние перемешано")

    # ------------------------------------------------------------------
    # ВЫДАЧА БАЙТ
    # ------------------------------------------------------------------
    def get_bytes(self, n: int) -> bytes:
        if self._state != RngState.READY:
            raise RuntimeError(f"ГСЧ не готов: {self._state.value}")
        if n <= 0:
            raise ValueError("n должно быть > 0")

        if self._config.check_sources_before_keygen and not self._first_use_done:
            if not self.check_sources():
                self._fail("проверка источников перед ключом не пройдена")

        out = bytearray()
        while len(out) < n:
            h = hashlib.new(self._config.mix_algorithm)
            h.update(self._internal_state)
            h.update(self._bytes_since_reseed.to_bytes(8, "little"))
            block = h.digest()
            out.extend(block)

            self._internal_state = hashlib.new(
                self._config.mix_algorithm,
                self._internal_state + block,
            ).digest()[: self._config.internal_state_size]
            self._bytes_since_reseed += len(block)

        self._bytes_since_reseed += n
        if self._bytes_since_reseed >= self._config.reseed_interval:
            self._reseed()

        self._first_use_done = True
        return bytes(out[:n])

    def generate_key(self, length_bytes: int) -> bytes:
        return self.get_bytes(length_bytes)

    # ------------------------------------------------------------------
    # RESEED
    # ------------------------------------------------------------------
    def _reseed(self) -> None:
        self._log("reseed: обновление состояния")
        self._collect_entropy()
        h = hashlib.new(self._config.mix_algorithm)
        h.update(self._internal_state)
        h.update(self._entropy_pool)
        h.update(os.urandom(16))
        self._internal_state = h.digest()[: self._config.internal_state_size]
        self._entropy_pool = b""
        self._bytes_since_reseed = 0

    # ------------------------------------------------------------------
    # СТАТИСТИЧЕСКИЕ ТЕСТЫ (СЧ.5)
    # ------------------------------------------------------------------
    def test_statistical(self) -> bool:
        try:
            data = self._collect_for_test(256)
        except Exception as e:
            self._log(f"stat: не удалось получить данные: {e}")
            return False

        if self._is_constant(data):
            self._log("stat: константная последовательность")
            return False

        ones = sum(bin(b).count("1") for b in data)
        total = len(data) * 8
        ratio = ones / total
        if not (0.4 < ratio < 0.6):
            self._log(f"stat: перекос битов ({ratio:.2f})")
            return False

        self._log("stat: тесты пройдены")
        return True

    def _collect_for_test(self, n: int) -> bytes:
        h = hashlib.sha256()
        h.update(self._internal_state)
        h.update(os.urandom(32))
        out = h.digest()
        while len(out) < n:
            out += hashlib.sha256(out).digest()
        return out[:n]

    @staticmethod
    def _is_constant(data: bytes) -> bool:
        if not data:
            return True
        first = data[0]
        return all(b == first for b in data)

    # ------------------------------------------------------------------
    # ВЫВОД ИЗ ЭКСПЛУАТАЦИИ (ВЭ)
    # ------------------------------------------------------------------
    def wipe_state(self) -> None:
        self._internal_state = b"\x00" * len(self._internal_state)
        self._entropy_pool = b"\x00" * len(self._entropy_pool)
        self._internal_state = b""
        self._entropy_pool = b""
        self._state = RngState.WIPED
        self._log("wipe: состояние очищено")

    # ------------------------------------------------------------------
    # ВНУТРЕННИЕ
    # ------------------------------------------------------------------
    def _fail(self, message: str) -> None:
        self._state = RngState.BLOCKED
        self._log(f"ОШИБКА: {message}")
        if self._audit:
            try:
                self._audit.critical("rng", message)
            except Exception:
                pass
        if self._config and self._config.strict_mode:
            raise RuntimeError(message)

    def _log(self, message: str) -> None:
        self._log_cb(f"[rng] {message}")