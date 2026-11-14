from dataclasses import dataclass


@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    build_date: str

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def full(self) -> str:
        return f"Версия ПО: {self}\nДата сборки: {self.build_date}"


APP_VERSION = VersionInfo(
    major=1, minor=0, patch=0,
    build_date="2025-04-28 14:32:00",
)


def print_version() -> None:
    print(APP_VERSION.full())