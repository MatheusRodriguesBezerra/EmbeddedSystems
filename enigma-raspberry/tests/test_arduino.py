from pathlib import Path

from comm.arduino_handler import ArduinoHandler
from comm.protocol import MobileProtocol
from comm.serial_service import SerialService
from enigma.models import MachineConfig, RotorSlot, TransferRole
from state.store import StateStore


class FakeSerial:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_line(self, line: str) -> bool:
        self.sent.append(line)
        return True


def default_slots() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=0),
    ]


def make_handler(tmp_path: Path, role: TransferRole = TransferRole.SENDING) -> tuple[ArduinoHandler, StateStore, FakeSerial]:
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=role, slots=default_slots()))
    protocol = MobileProtocol(store)
    fake_serial = FakeSerial()
    serial_service = SerialService("/dev/null", 115200, lambda _line: None)
    serial_service.send_line = fake_serial.send_line  # type: ignore[method-assign]
    handler = ArduinoHandler(store, protocol, serial_service)
    return handler, store, fake_serial


def test_sync_responds_with_cfg(tmp_path: Path):
    handler, _, fake = make_handler(tmp_path)

    handler.handle_line("SYNC")

    assert fake.sent == ["CFG:1,0,2,0,3,0"]


def test_send_from_physical_updates_pending_and_role(tmp_path: Path):
    handler, store, fake = make_handler(tmp_path, TransferRole.SENDING)

    handler.handle_line("SEND:ABC")

    assert any(line.startswith("ACK:") for line in fake.sent)
    assert store.get_config().role == TransferRole.RECEIVING
    pending = store.get_pending_outgoing()
    assert pending.available is True
    assert pending.payload == "ABC"


def test_send_rejected_when_not_sending(tmp_path: Path):
    handler, _, fake = make_handler(tmp_path, TransferRole.RECEIVING)

    handler.handle_line("SEND:ABC")

    assert fake.sent == ["ERR:NOT_SENDING"]


def test_relay_physical_outgoing(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store)

    ack = protocol.relay_cipher_from_arduino("HI")

    assert ack.payload == "HI"
