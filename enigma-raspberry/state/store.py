import json
from pathlib import Path
from threading import Lock

from enigma.models import HistoryItem, MachineConfig, MachineState, StoredState, TransferRole


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self._state = self._load()

    def get_config(self) -> MachineConfig:
        with self._lock:
            return self._state.config.model_copy()

    def get_machine_state(self) -> MachineState:
        with self._lock:
            return MachineState(
                **self._state.config.model_dump(),
                connectedArduino=self._state.connectedArduino,
            )

    def set_config(self, config: MachineConfig) -> MachineState:
        with self._lock:
            self._state.config = config
            self._save()
            return MachineState(
                **config.model_dump(),
                connectedArduino=self._state.connectedArduino,
            )

    def set_positions_and_role(
        self,
        positions: tuple[int, int, int],
        role: TransferRole,
    ) -> MachineState:
        with self._lock:
            self._state.config = self._state.config.model_copy(
                update={"positions": positions, "role": role}
            )
            self._save()
            return MachineState(
                **self._state.config.model_dump(),
                connectedArduino=self._state.connectedArduino,
            )

    def set_arduino_connected(self, connected: bool) -> None:
        with self._lock:
            self._state.connectedArduino = connected
            self._save()

    def add_history(self, item: HistoryItem) -> None:
        with self._lock:
            self._state.history = [item, *self._state.history][:50]
            self._state.processedMessageIds = [
                item.messageId,
                *self._state.processedMessageIds,
            ][:100]
            self._save()

    def has_processed(self, message_id: str) -> bool:
        with self._lock:
            return message_id in self._state.processedMessageIds

    def _load(self) -> StoredState:
        if not self.path.exists():
            return StoredState()

        with self.path.open("r", encoding="utf-8") as file:
            return StoredState.model_validate(json.load(file))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self._state.model_dump(mode="json"), file, indent=2)
