from dataclasses import dataclass

from config import ALPHABET


@dataclass(frozen=True)
class Reflector:
    wiring: str

    def reflect(self, index: int) -> int:
        return ALPHABET.index(self.wiring[index])
