from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig


def test_enigma_is_symmetric_with_same_initial_config():
    machine = EnigmaMachine()
    config = MachineConfig(positions=(0, 0, 0))

    encrypted, _ = machine.process_message("OLA", config)
    decrypted, _ = machine.process_message(encrypted, config)

    assert decrypted == "OLA"


def test_enigma_advances_right_rotor_for_each_letter():
    machine = EnigmaMachine()
    config = MachineConfig(positions=(0, 0, 0))

    _, positions = machine.process_message("ABC", config)

    assert positions == (0, 0, 3)
