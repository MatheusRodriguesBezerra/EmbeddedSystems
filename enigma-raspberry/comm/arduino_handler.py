import logging

from comm.protocol import MobileProtocol, parse_slots_csv, sanitize_payload
from comm.serial_service import SerialService
from enigma.models import MachineConfig, MachineMode, TransferRole
from state.store import StateStore

logger = logging.getLogger(__name__)

_DEBUG_PREFIXES = (
    "ENIGMA:",
    "---",
    "KEYPAD",
    "LCD[",
    "LEDS ",
    "SCAN ",
    "SE VE",
    "PLACA",
    "DISPOSITIVO",
)


class ArduinoHandler:
    """Traduz eventos Serial do Arduino para estado HTTP e respostas Serial."""

    def __init__(
        self,
        store: StateStore,
        protocol: MobileProtocol,
        serial_service: SerialService,
    ) -> None:
        self.store = store
        self.protocol = protocol
        self.serial = serial_service

    def handle_line(self, line: str) -> None:
        upper = line.strip().upper()
        if not upper or self._is_debug_line(upper):
            return

        if upper == "SYNC":
            self._handle_sync()
            return

        if upper.startswith("SEND:"):
            self._handle_send(upper.split(":", 1)[1])
            return

        if upper.startswith("MODE:"):
            self._handle_mode(upper.split(":", 1)[1])
            return

        if upper == "STATUS":
            self._handle_status()
            return

        logger.debug("Linha Serial ignorada: %s", line)

    def push_config_to_arduino(self) -> None:
        config = self.store.get_config()
        self.serial.send_line(self._format_cfg(config))

    def push_config_slots_to_arduino(self, config: MachineConfig) -> None:
        self.serial.send_line(self._format_cfg(config))

    def push_cipher_to_arduino(self, cipher: str) -> None:
        clean = sanitize_payload(cipher)
        if not clean:
            return
        self.serial.send_line(f"IN:{clean}")

    def deliver_cipher_to_arduino(self, cipher: str, config_before: MachineConfig) -> None:
        """Alinha rotores PRE-mensagem, envia IN: e depois pos-posicao."""
        self.push_config_slots_to_arduino(config_before)
        self.push_cipher_to_arduino(cipher)
        self.push_config_to_arduino()

    def _handle_sync(self) -> None:
        config = self.store.get_config()
        line = self._format_cfg(config)
        self.serial.send_line(line)
        logger.info("SYNC -> %s", line)

    def _handle_send(self, payload: str) -> None:
        try:
            cipher, slots_after = self._parse_send_payload(payload)
        except ValueError as error:
            self.serial.send_line(f"ERR:{error}")
            return

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            self.serial.send_line("ERR:NOT_SENDING")
            logger.warning("SEND rejeitado: role=%s", config.role)
            return

        try:
            ack = self.protocol.relay_cipher_from_arduino(cipher, slots_after)
        except ValueError as error:
            self.serial.send_line(f"ERR:{error}")
            return

        self.serial.send_line(f"ACK:{ack.messageId}")
        self.push_config_to_arduino()
        logger.info(
            "SEND fisico aceite payload=%s role=%s",
            ack.payload,
            ack.role,
        )

    def _handle_mode(self, mode_text: str) -> None:
        try:
            mode = MachineMode(mode_text.strip().upper())
        except ValueError:
            self.serial.send_line("ERR:MODO_INVALIDO")
            return

        config = self.store.get_config()
        self.store.set_config(config.model_copy(update={"mode": mode}))
        self.serial.send_line(f"STATUS:MODE:{mode.value}")

    def _handle_status(self) -> None:
        state = self.store.get_machine_state()
        slot_text = self._format_cfg(
            MachineConfig(slots=state.slots, mode=state.mode, role=state.role)
        )
        self.serial.send_line(f"STATUS:{slot_text}:ROLE:{state.role.value}")

    @staticmethod
    def _parse_send_payload(payload: str) -> tuple[str, list]:
        clean = payload.strip()
        if "|" not in clean:
            raise ValueError("SLOTS_OBRIGATORIOS")

        cipher_text, slots_text = clean.split("|", 1)
        cipher = sanitize_payload(cipher_text)
        if not cipher:
            raise ValueError("PAYLOAD_VAZIO")

        slots_after = parse_slots_csv(slots_text)
        if not slots_after:
            raise ValueError("SLOTS_OBRIGATORIOS")

        return cipher, slots_after

    @staticmethod
    def _format_cfg(config: MachineConfig) -> str:
        if not config.slots:
            return "CFG:"
        parts = []
        for slot in config.slots:
            parts.append(f"{slot.id},{slot.position}")
        return f"CFG:{','.join(parts)}"

    @staticmethod
    def _is_debug_line(line: str) -> bool:
        if line.startswith("KEYPAD"):
            return True
        return any(line.startswith(prefix) for prefix in _DEBUG_PREFIXES)
