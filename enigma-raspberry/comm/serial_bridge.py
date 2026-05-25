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
            output, slots = self.machine.process_message(letter, config)
            self.store.set_slots_and_role(slots, config.role)
            return f"OUT:{output}"

        if command.startswith("MODE:"):
            mode = command.split(":", 1)[1]
            next_config = config.model_copy(update={"mode": MachineMode(mode)})
            self.store.set_config(next_config)
            return f"STATUS:MODE:{mode}"

        if command == "STATUS":
            state = self.store.get_machine_state()
            parts = [f"{slot.id},{slot.position}" for slot in state.slots]
            cfg = f"CFG:{','.join(parts)}" if parts else "CFG:"
            return f"STATUS:{cfg}:ROLE:{state.role}"

        if command == "SEND":
            return "STATUS:SEND_READY"

        return "STATUS:UNKNOWN_COMMAND"
