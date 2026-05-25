from pathlib import Path

import pytest

from comm.protocol import MobileProtocol, parse_slots_csv
from enigma.models import MachineConfig, RotorSlot, TransferRole
from state.store import StateStore


def default_slots() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=0),
    ]


def slots_after_three_letters() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=3),
    ]


def test_relay_mobile_outgoing_requires_sending_role(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.RECEIVING, slots=default_slots()))
    protocol = MobileProtocol(store)

    with pytest.raises(ValueError):
        protocol.relay_cipher_from_mobile("ABC", slots_after_three_letters())


def test_relay_mobile_outgoing_updates_slots_without_crypto(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store)

    ack = protocol.relay_cipher_from_mobile("XYZ", slots_after_three_letters(), "msg-1")

    assert ack.payload == "XYZ"
    assert ack.plainText == ""
    assert ack.role == TransferRole.RECEIVING
    assert store.get_config().slots[-1].position == 3


def test_relay_arduino_outgoing_sets_pending(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store)

    ack = protocol.relay_cipher_from_arduino("QWE", slots_after_three_letters())

    assert ack.payload == "QWE"
    pending = store.get_pending_outgoing()
    assert pending.available is True
    assert pending.payload == "QWE"


def test_parse_slots_csv():
    slots = parse_slots_csv("2,10,1,2,5,15,3,16")
    assert len(slots) == 4
    assert slots[0].id == 2
    assert slots[0].position == 10
