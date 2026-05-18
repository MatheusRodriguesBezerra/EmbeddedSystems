from dataclasses import dataclass

from config import ALPHABET


@dataclass(frozen=True)
class Rotor:
    rotor_id: str
    wiring: str

    def forward(self, index: int, position: int) -> int:
        shifted = (index + position) % 26
        mapped = ALPHABET.index(self.wiring[shifted])
        return (mapped - position + 26) % 26

    def backward(self, index: int, position: int) -> int:
        shifted = (index + position) % 26
        mapped = self.wiring.index(ALPHABET[shifted])
        return (mapped - position + 26) % 26
