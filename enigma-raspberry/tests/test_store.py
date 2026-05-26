from pathlib import Path

from enigma.models import MachineConfig, RotorSlot
from state.store import StateStore


def make_store(tmp_path: Path) -> StateStore:
    return StateStore(tmp_path / "state.json")


def test_set_and_get_config(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.set_config(
        MachineConfig(
            rotors=[
                RotorSlot(id=1, position=5),
                RotorSlot(id=3, position=10),
            ]
        )
    )

    config = store.get_config()
    assert [slot.id for slot in config.rotors] == [1, 3]
    assert [slot.position for slot in config.rotors] == [5, 10]


def test_pending_cipher_lifecycle(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    assert store.consume_pending_cipher() is None

    store.set_pending_cipher("XYZ")
    assert store.get_pending_cipher() == "XYZ"

    assert store.consume_pending_cipher() == "XYZ"
    assert store.consume_pending_cipher() is None


def test_persists_between_instances(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store_a = StateStore(path)
    store_a.set_config(MachineConfig(rotors=[RotorSlot(id=2, position=4)]))
    store_a.set_pending_cipher("AAA")

    store_b = StateStore(path)
    assert store_b.get_config().rotors[0].id == 2
    assert store_b.get_pending_cipher() == "AAA"


def test_legacy_state_migrates_slots_to_rotors(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text(
        '{"config": {"slots": [{"id": 1, "position": 7}], "mode": "ENC", "role": "IDLE"},'
        ' "connectedArduino": true, "pendingPayload": "QQQ"}',
        encoding="utf-8",
    )

    store = StateStore(path)
    config = store.get_config()
    assert len(config.rotors) == 1
    assert config.rotors[0].id == 1
    assert config.rotors[0].position == 7
    assert store.get_pending_cipher() == "QQQ"
