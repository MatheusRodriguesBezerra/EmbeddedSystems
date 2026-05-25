from enigma.models import MachineConfig, MachineMode
from state.store import StateStore


class SerialBridge:
    def __init__(self, store: StateStore) -> None:
        self.store = store

    def handle_command(self, command: str) -> str:
        command = command.strip().upper()
        config = self.store.get_config()

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
