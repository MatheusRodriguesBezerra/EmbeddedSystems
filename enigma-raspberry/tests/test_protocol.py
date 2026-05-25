from pathlib import Path

import pytest

from comm.protocol import MobileProtocol
from enigma.models import MachineConfig, RotorSlot, TransferRole
from state.store import StateStore


def default_slots() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=0),
    ]


def test_relay_mobile_outgoing_requires_sending_role(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.RECEIVING, slots=default_slots()))
    protocol = MobileProtocol(store)

    with pytest.raises(ValueError):
        protocol.relay_cipher_from_mobile("ABC")


def test_relay_mobile_outgoing_flips_role_without_changing_slots(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store)

    ack = protocol.relay_cipher_from_mobile("XYZ", "msg-1")

    assert ack.payload == "XYZ"
    assert ack.role == TransferRole.RECEIVING
    assert store.get_config().slots == default_slots()
    assert store.get_config().role == TransferRole.RECEIVING


def test_relay_arduino_outgoing_sets_pending(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store)

    ack = protocol.relay_cipher_from_arduino("QWE")

    assert ack.payload == "QWE"
    pending = store.get_pending_outgoing()
    assert pending.available is True
    assert pending.payload == "QWE"
    assert not hasattr(pending, "slots") or getattr(pending, "slots", None) in (None, [])
