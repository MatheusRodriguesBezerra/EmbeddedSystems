import logging
from uuid import uuid4

from comm.protocol import MobileProtocol, complementary_role, sanitize_payload
from comm.serial_service import SerialService
from enigma.machine import EnigmaMachine
from enigma.models import HistoryItem, MachineMode, TransferRole
from state.store import StateStore

logger = logging.getLogger(__name__)

# Linhas de debug do firmware (nao sao comandos de protocolo)
_DEBUG_PREFIXES = (
    "ENIGMA:",
    "---",
    "KEYPAD",
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
        machine: EnigmaMachine,
        protocol: MobileProtocol,
        serial_service: SerialService,
    ) -> None:
        self.store = store
        self.machine = machine
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

        if upper.startswith("KEY:"):
            self._handle_key(upper.split(":", 1)[1])
            return

        if upper == "STATUS":
            self._handle_status()
            return

        logger.debug("Linha Serial ignorada: %s", line)

    def push_positions_to_arduino(self) -> None:
        config = self.store.get_config()
        self.serial.send_line(self._format_pos(config.positions))

    def push_cipher_to_arduino(self, cipher: str) -> None:
        clean = sanitize_payload(cipher)
        if not clean:
            return
        self.serial.send_line(f"IN:{clean}")

    def _handle_sync(self) -> None:
        config = self.store.get_config()
        self.serial.send_line(self._format_pos(config.positions))
        logger.info("SYNC -> %s", self._format_pos(config.positions))

    def _handle_send(self, payload: str) -> None:
        clean = sanitize_payload(payload)
        if not clean:
            self.serial.send_line("ERR:PAYLOAD_VAZIO")
            return

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            self.serial.send_line("ERR:NOT_SENDING")
            logger.warning("SEND rejeitado: role=%s", config.role)
            return

        try:
            ack = self.protocol.accept_physical_outgoing(clean)
        except ValueError as error:
            self.serial.send_line(f"ERR:{error}")
            return

        message_id = ack.messageId
        self.serial.send_line(f"ACK:{message_id}")
        logger.info(
            "SEND fisico aceite payload=%s plain=%s role=%s",
            ack.payload,
            ack.plainText,
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

    def _handle_key(self, letter: str) -> None:
        clean = sanitize_payload(letter)[:1]
        if not clean:
            return

        config = self.store.get_config()
        output, positions = self.machine.process_message(clean, config)
        self.store.set_positions_and_role(positions, config.role)
        self.serial.send_line(f"OUT:{output}")
        self.serial.send_line(self._format_pos(positions))

    def _handle_status(self) -> None:
        state = self.store.get_machine_state()
        self.serial.send_line(
            f"STATUS:POS:{','.join(map(str, state.positions))}:ROLE:{state.role.value}"
        )

    @staticmethod
    def _format_pos(positions: tuple[int, int, int]) -> str:
        return f"POS:{positions[0]},{positions[1]},{positions[2]}"

    @staticmethod
    def _is_debug_line(line: str) -> bool:
        if line.startswith("KEYPAD"):
            return True
        return any(line.startswith(prefix) for prefix in _DEBUG_PREFIXES)
