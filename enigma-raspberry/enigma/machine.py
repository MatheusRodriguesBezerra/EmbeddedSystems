from config import ALPHABET, REFLECTOR_B, ROTOR_WIRINGS
from enigma.models import MachineConfig, RotorSlot
from enigma.reflector import Reflector
from enigma.rotor import Rotor


class EnigmaMachine:
    def __init__(self) -> None:
        self.rotors = {
            rotor_id: Rotor(rotor_id, wiring)
            for rotor_id, wiring in ROTOR_WIRINGS.items()
        }
        self.reflector = Reflector(REFLECTOR_B)

    def process_message(self, message: str, config: MachineConfig) -> tuple[str, list[RotorSlot]]:
        if not config.slots:
            raise ValueError("Sem rotores configurados.")

        positions = [slot.position for slot in config.slots]
        output = []

        for char in message.upper():
            if char not in ALPHABET:
                continue

            encoded, positions = self._process_letter(char, config.slots, positions)
            output.append(encoded)

        next_slots = [
            RotorSlot(id=config.slots[index].id, position=positions[index])
            for index in range(len(config.slots))
        ]
        return "".join(output), next_slots

    def _process_letter(
        self,
        letter: str,
        slots: list[RotorSlot],
        positions: list[int],
    ) -> tuple[str, list[int]]:
        next_positions = self._step_positions(positions)
        index = ALPHABET.index(letter)
        count = len(slots)

        for rotor_index in range(count - 1, -1, -1):
            rotor = self.rotors[str(slots[rotor_index].id)]
            index = rotor.forward(index, next_positions[rotor_index])

        index = self.reflector.reflect(index)

        for rotor_index in range(count):
            rotor = self.rotors[str(slots[rotor_index].id)]
            index = rotor.backward(index, next_positions[rotor_index])

        return ALPHABET[index], next_positions

    @staticmethod
    def _step_positions(positions: list[int]) -> list[int]:
        if not positions:
            return positions
        next_positions = list(positions)
        next_positions[-1] = (next_positions[-1] + 1) % 26
        return next_positions
