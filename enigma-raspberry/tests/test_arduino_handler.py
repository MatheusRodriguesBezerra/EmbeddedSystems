from pathlib import Path

from comm.arduino_handler import ArduinoHandler
from comm.serial_service import SerialService
from enigma.models import MachineConfig, RotorSlot
from state.store import StateStore


class FakeSerial:
    """SerialService falso usado para inspecionar linhas enviadas nos testes."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_line(self, line: str) -> bool:
        self.sent.append(line)
        return True


def make_handler(tmp_path: Path) -> tuple[ArduinoHandler, StateStore, FakeSerial]:
    store = StateStore(tmp_path / "state.json")
    fake = FakeSerial()
    serial_service = SerialService("/dev/null", 115200, lambda _line: None)
    serial_service.send_line = fake.send_line  # type: ignore[method-assign]
    handler = ArduinoHandler(store, serial_service)
    return handler, store, fake


def test_sync_responds_with_pos(tmp_path: Path) -> None:
    handler, store, fake = make_handler(tmp_path)
    store.set_config(
        MachineConfig(
            rotors=[
                RotorSlot(id=1, position=0),
                RotorSlot(id=2, position=3),
            ]
        )
    )

    handler.handle_line("SYNC")

    assert fake.sent == ["POS:1,0,2,3"]


def test_sync_empty_when_no_rotors(tmp_path: Path) -> None:
    handler, _, fake = make_handler(tmp_path)

    handler.handle_line("SYNC")

    assert fake.sent == ["POS:"]


def test_status_responds_ok(tmp_path: Path) -> None:
    handler, _, fake = make_handler(tmp_path)

    handler.handle_line("STATUS")

    assert fake.sent == ["STATUS:OK"]


def test_message_from_arduino_stores_pending(tmp_path: Path) -> None:
    handler, store, fake = make_handler(tmp_path)

    handler.handle_line("MESSAGEFROMARDUINO:XYZ")

    assert store.get_pending_cipher() == "XYZ"
    assert any(line.startswith("ACK:") for line in fake.sent)


def test_message_from_arduino_rejects_empty_payload(tmp_path: Path) -> None:
    handler, store, fake = make_handler(tmp_path)

    handler.handle_line("MESSAGEFROMARDUINO:")

    assert store.get_pending_cipher() == ""
    assert fake.sent == ["ERR:PAYLOAD_VAZIO"]


def test_push_cipher_to_arduino_uses_messagefrommobile(tmp_path: Path) -> None:
    handler, _, fake = make_handler(tmp_path)

    handler.push_cipher_to_arduino("hello")

    assert fake.sent == ["MESSAGEFROMMOBILE:HELLO"]


def test_debug_lines_are_ignored(tmp_path: Path) -> None:
    handler, store, fake = make_handler(tmp_path)

    handler.handle_line("ENIGMA: boot")
    handler.handle_line("LCD[0]: ola")
    handler.handle_line("--- Scan I2C ---")

    assert fake.sent == []
    assert store.get_pending_cipher() == ""
