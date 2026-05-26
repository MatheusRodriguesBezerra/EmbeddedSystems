import json
from pathlib import Path
from threading import Lock

from enigma.models import MachineConfig, MachineState, StoredState


class StateStore:
    """Estado partilhado entre HTTP e Serial. Persistido em ficheiro JSON."""

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
                rotors=self._state.config.rotors,
                connectedArduino=self._state.connectedArduino,
            )

    def set_config(self, config: MachineConfig) -> MachineState:
        with self._lock:
            self._state.config = config
            self._save()
            return MachineState(
                rotors=config.rotors,
                connectedArduino=self._state.connectedArduino,
            )

    def set_arduino_connected(self, connected: bool) -> None:
        with self._lock:
            self._state.connectedArduino = connected
            self._save()

    def set_pending_cipher(self, cipher: str) -> None:
        with self._lock:
            self._state.pendingCipher = cipher
            self._save()

    def get_pending_cipher(self) -> str:
        with self._lock:
            return self._state.pendingCipher

    def consume_pending_cipher(self) -> str | None:
        """Devolve a cifra pendente (e limpa-a). None se nao houver."""
        with self._lock:
            cipher = self._state.pendingCipher
            if not cipher:
                return None
            self._state.pendingCipher = ""
            self._save()
            return cipher

    def _load(self) -> StoredState:
        if not self.path.exists():
            return StoredState()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (json.JSONDecodeError, OSError):
            return StoredState()

        config_raw = raw.get("config", {})

        # Migra formatos antigos para o novo (rotors).
        if "rotors" not in config_raw:
            if "slots" in config_raw:
                config_raw["rotors"] = config_raw.pop("slots")
            elif "order" in config_raw:
                roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
                order = config_raw.get("order", [])
                positions = config_raw.get("positions", [])
                config_raw["rotors"] = [
                    {"id": roman_map.get(item, 1), "position": positions[index] if index < len(positions) else 0}
                    for index, item in enumerate(order)
                ]
            else:
                config_raw["rotors"] = []
        # Remove campos legacy.
        for legacy in ("mode", "role", "order", "positions", "slots"):
            config_raw.pop(legacy, None)

        return StoredState(
            config=MachineConfig.model_validate({"rotors": config_raw.get("rotors", [])}),
            connectedArduino=bool(raw.get("connectedArduino", False)),
            pendingCipher=str(raw.get("pendingCipher", raw.get("pendingPayload", ""))),
        )

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self._state.model_dump(mode="json"), file, indent=2)
