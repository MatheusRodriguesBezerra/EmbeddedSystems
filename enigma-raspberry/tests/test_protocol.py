from pathlib import Path

import pytest

from comm.protocol import MobileProtocol
from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, TransferRole
from state.store import StateStore


def make_protocol(tmp_path: Path) -> MobileProtocol:
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.RECEIVING))
    return MobileProtocol(store, EnigmaMachine())


def test_receive_payload_requires_receiving_role(tmp_path: Path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(MachineConfig(role=TransferRole.SENDING))
    protocol = MobileProtocol(store, EnigmaMachine())

    with pytest.raises(ValueError):
        protocol.receive_payload("ABC")


def test_receive_payload_updates_role_and_positions(tmp_path: Path):
    protocol = make_protocol(tmp_path)

    ack = protocol.receive_payload("ABC", "msg-1")

    assert ack.status == "received"
    assert ack.role == TransferRole.SENDING
    assert ack.positions == (0, 0, 3)


def test_duplicate_message_id_is_rejected(tmp_path: Path):
    protocol = make_protocol(tmp_path)

    protocol.receive_payload("ABC", "msg-1")

    with pytest.raises(ValueError):
        protocol.receive_payload("ABC", "msg-1")
