from config import ALPHABET, REFLECTOR_B, ROTOR_WIRINGS
from enigma.models import MachineConfig
from enigma.reflector import Reflector
from enigma.rotor import Rotor


class EnigmaMachine:
    def __init__(self) -> None:
        self.rotors = {
            rotor_id: Rotor(rotor_id, wiring)
            for rotor_id, wiring in ROTOR_WIRINGS.items()
        }
        self.reflector = Reflector(REFLECTOR_B)

    def process_message(self, message: str, config: MachineConfig) -> tuple[str, tuple[int, int, int]]:
        positions = config.positions
        output = []

        for char in message.upper():
            if char not in ALPHABET:
                continue

            encoded, positions = self._process_letter(char, config, positions)
            output.append(encoded)

        return "".join(output), positions

    def _process_letter(
        self,
        letter: str,
        config: MachineConfig,
        positions: tuple[int, int, int],
    ) -> tuple[str, tuple[int, int, int]]:
        next_positions = self._step_positions(positions)
        index = ALPHABET.index(letter)

        for rotor_index in range(2, -1, -1):
            rotor = self.rotors[config.order[rotor_index]]
            index = rotor.forward(index, next_positions[rotor_index])

        index = self.reflector.reflect(index)

        for rotor_index in range(3):
            rotor = self.rotors[config.order[rotor_index]]
            index = rotor.backward(index, next_positions[rotor_index])

        return ALPHABET[index], next_positions

    @staticmethod
    def _step_positions(positions: tuple[int, int, int]) -> tuple[int, int, int]:
        first, second, third = positions
        return first, second, (third + 1) % 26
