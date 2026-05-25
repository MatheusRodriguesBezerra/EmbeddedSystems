import json
from pathlib import Path
from threading import Lock

from enigma.models import (
    HistoryItem,
    MachineConfig,
    MachineState,
    PendingOutgoing,
    RotorSlot,
    StoredState,
    TransferRole,
)


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

    def set_slots_and_role(
        self,
        slots: list[RotorSlot],
        role: TransferRole,
    ) -> MachineState:
        with self._lock:
            self._state.config = self._state.config.model_copy(
                update={"slots": slots, "role": role}
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

    def set_pending_outgoing(
        self,
        payload: str,
        message_id: str,
    ) -> None:
        with self._lock:
            self._state.pendingPayload = payload
            self._state.pendingMessageId = message_id
            self._save()

    def get_pending_outgoing(self) -> PendingOutgoing:
        with self._lock:
            if not self._state.pendingPayload:
                return PendingOutgoing()
            return PendingOutgoing(
                available=True,
                payload=self._state.pendingPayload,
                messageId=self._state.pendingMessageId,
                role=self._state.config.role,
            )

    def clear_pending_outgoing(self) -> PendingOutgoing:
        with self._lock:
            if not self._state.pendingPayload:
                pending = PendingOutgoing()
            else:
                pending = PendingOutgoing(
                    available=True,
                    payload=self._state.pendingPayload,
                    messageId=self._state.pendingMessageId,
                    role=self._state.config.role,
                )
            self._state.pendingPayload = ""
            self._state.pendingMessageId = ""
            self._save()
            return pending

    def _load(self) -> StoredState:
        if not self.path.exists():
            return StoredState()

        with self.path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        # Migra estado antigo order/positions -> slots
        config = raw.get("config", {})
        if "order" in config and "slots" not in config:
            roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
            order = config.get("order", ["I", "II", "III"])
            positions = config.get("positions", [0, 0, 0])
            config["slots"] = [
                {"id": roman_map.get(rotor, 1), "position": positions[index]}
                for index, rotor in enumerate(order)
            ]
            config.pop("order", None)
            config.pop("positions", None)
            raw["config"] = config

        if "history" in raw:
            for item in raw["history"]:
                if "positions" in item and "slots" not in item:
                    item["slots"] = []
                    item.pop("positions", None)

        return StoredState.model_validate(raw)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self._state.model_dump(mode="json"), file, indent=2)
