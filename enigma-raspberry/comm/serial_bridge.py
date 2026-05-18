from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, MachineMode
from state.store import StateStore


class SerialBridge:
    def __init__(self, store: StateStore, machine: EnigmaMachine) -> None:
        self.store = store
        self.machine = machine

    def handle_command(self, command: str) -> str:
        command = command.strip().upper()
        config = self.store.get_config()

        if command.startswith("KEY:"):
            letter = command.split(":", 1)[1][:1]
            output, positions = self.machine.process_message(letter, config)
            self.store.set_positions_and_role(positions, config.role)
            return f"OUT:{output}"

        if command.startswith("ROTOR:"):
            return self._handle_rotor(command, config)

        if command.startswith("MODE:"):
            mode = command.split(":", 1)[1]
            next_config = config.model_copy(update={"mode": MachineMode(mode)})
            self.store.set_config(next_config)
            return f"STATUS:MODE:{mode}"

        if command == "STATUS":
            state = self.store.get_machine_state()
            return f"STATUS:POS:{','.join(map(str, state.positions))}:ROLE:{state.role}"

        if command == "SEND":
            return "STATUS:SEND_READY"

        return "STATUS:UNKNOWN_COMMAND"

    def _handle_rotor(self, command: str, config: MachineConfig) -> str:
        _, index_text, delta_text = command.split(":")
        index = int(index_text)
        delta = int(delta_text)
        positions = list(config.positions)
        positions[index] = (positions[index] + delta) % 26
        next_config = config.model_copy(update={"positions": tuple(positions)})
        self.store.set_config(next_config)
        return f"POS:{','.join(map(str, positions))}"
