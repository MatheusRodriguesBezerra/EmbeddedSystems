import logging

from comm.protocol import sanitize_cipher
from comm.serial_service import SerialService
from enigma.models import MachineConfig
from state.store import StateStore

logger = logging.getLogger(__name__)

# Linhas de debug do Arduino que sao ignoradas (nao fazem parte do protocolo).
_DEBUG_PREFIXES = (
    "ENIGMA:",
    "---",
    "KEYPAD",
    "LCD[",
    "LEDS ",
    "LED ",
    "SCAN ",
    "SE VE",
    "PLACA",
    "DISPOSITIVO",
    "MODE:",
    "ACK:",
    "ERR:",
)


class ArduinoHandler:
    """Traduz linhas Serial do Arduino para acoes de estado e respostas Serial."""

    def __init__(
        self,
        store: StateStore,
        serial_service: SerialService,
    ) -> None:
        self.store = store
        self.serial = serial_service

    def handle_line(self, line: str) -> None:
        clean = line.strip()
        if not clean:
            return

        upper = clean.upper()
        if self._is_debug_line(upper):
            return

        if upper == "SYNC":
            self._handle_sync()
            return

        if upper == "STATUS":
            self._handle_status()
            return

        if upper.startswith("MESSAGEFROMARDUINO:"):
            self._handle_message_from_arduino(clean.split(":", 1)[1])
            return

        logger.debug("Linha Serial ignorada: %s", clean)

    def push_config_to_arduino(self) -> None:
        config = self.store.get_config()
        self.serial.send_line(self._format_pos(config))

    def push_cipher_to_arduino(self, cipher: str) -> bool:
        clean = sanitize_cipher(cipher)
        if not clean:
            return False
        return self.serial.send_line(f"MESSAGEFROMMOBILE:{clean}")

    def _handle_sync(self) -> None:
        config = self.store.get_config()
        line = self._format_pos(config)
        self.serial.send_line(line)
        logger.info("SYNC -> %s", line)

    def _handle_status(self) -> None:
        self.serial.send_line("STATUS:OK")

    def _handle_message_from_arduino(self, payload: str) -> None:
        cipher = sanitize_cipher(payload)
        if not cipher:
            self.serial.send_line("ERR:PAYLOAD_VAZIO")
            return

        self.store.set_pending_cipher(cipher)
        self.serial.send_line(f"ACK:{cipher}")
        logger.info("MESSAGEFROMARDUINO armazenada: %s", cipher)

    @staticmethod
    def _format_pos(config: MachineConfig) -> str:
        if not config.rotors:
            return "POS:"
        parts = [f"{slot.id},{slot.position}" for slot in config.rotors]
        return f"POS:{','.join(parts)}"

    @staticmethod
    def _is_debug_line(upper_line: str) -> bool:
        return any(upper_line.startswith(prefix) for prefix in _DEBUG_PREFIXES)
