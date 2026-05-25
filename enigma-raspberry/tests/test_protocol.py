from pathlib import Path

import pytest

from comm.protocol import MobileProtocol
from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, RotorSlot, TransferRole
from state.store import StateStore


def default_slots() -> list[RotorSlot]:
    return [
        RotorSlot(id=1, position=0),
        RotorSlot(id=2, position=0),
        RotorSlot(id=3, position=0),
    ]


def make_protocol(tmp_path: Path) -> MobileProtocol:
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.RECEIVING, slots=default_slots()))
    return MobileProtocol(store, EnigmaMachine())


def test_receive_payload_requires_receiving_role(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING, slots=default_slots()))
    protocol = MobileProtocol(store, EnigmaMachine())

    with pytest.raises(ValueError):
        protocol.receive_payload("ABC")


def test_receive_payload_updates_role_and_slots(tmp_path: Path):
    protocol = make_protocol(tmp_path)

    ack = protocol.receive_payload("ABC", "msg-1")

    assert ack.status == "received"
    assert ack.role == TransferRole.SENDING
    assert ack.slots[-1].position == 3


def test_duplicate_message_id_is_rejected(tmp_path: Path):
    protocol = make_protocol(tmp_path)

    protocol.receive_payload("ABC", "msg-1")

    with pytest.raises(ValueError):
        protocol.receive_payload("ABC", "msg-1")
