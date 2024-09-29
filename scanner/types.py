from dataclasses import dataclass
from typing import Self


@dataclass
class FileInfo:
    lines: int = 0
    symbols: int = 0
    size: int = 0


@dataclass
class ScanResult:
    lines: int
    symbols: int
    size: int
    count: int

    @classmethod
    def create_empty(cls) -> Self:
        return cls(0, 0, 0, 0)
