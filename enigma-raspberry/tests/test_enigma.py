from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, RotorSlot


def default_slots() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=0),
    ]


def test_enigma_is_symmetric_with_same_initial_config():
    machine = EnigmaMachine()
    config = MachineConfig(slots=default_slots())

    encrypted, _ = machine.process_message("OLA", config)
    decrypted, _ = machine.process_message(encrypted, config)

    assert decrypted == "OLA"


def test_enigma_advances_right_rotor_for_each_letter():
    machine = EnigmaMachine()
    config = MachineConfig(slots=default_slots())

    _, slots = machine.process_message("ABC", config)

    assert slots[-1].position == 3


def test_enigma_supports_up_to_four_rotors():
    machine = EnigmaMachine()
    config = MachineConfig(
        slots=[
            RotorSlot(id=2, position=10),
            RotorSlot(id=1, position=2),
            RotorSlot(id=5, position=15),
            RotorSlot(id=3, position=16),
        ]
    )

    encrypted, next_slots = machine.process_message("A", config)

    assert len(encrypted) == 1
    assert len(next_slots) == 4
    assert next_slots[-1].position == 17
