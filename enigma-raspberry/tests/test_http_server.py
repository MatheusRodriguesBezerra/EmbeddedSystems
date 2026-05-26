from pathlib import Path

from fastapi.testclient import TestClient

from comm.mobile_server import create_app
from enigma.models import MachineConfig, RotorSlot
from state.store import StateStore


class FakeArduinoHandler:
    def __init__(self) -> None:
        self.config_pushes = 0
        self.ciphers: list[str] = []

    def push_config_to_arduino(self) -> None:
        self.config_pushes += 1

    def push_cipher_to_arduino(self, cipher: str) -> bool:
        self.ciphers.append(cipher)
        return True


def make_client(tmp_path: Path) -> tuple[TestClient, StateStore, FakeArduinoHandler]:
    store = StateStore(tmp_path / "state.json")
    fake_handler = FakeArduinoHandler()
    app = create_app(store, serial_service=None, arduino_handler=fake_handler)  # type: ignore[arg-type]
    return TestClient(app), store, fake_handler


def test_ping_returns_connected_state(tmp_path: Path) -> None:
    client, store, _ = make_client(tmp_path)
    store.set_arduino_connected(True)

    response = client.get("/ping")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["connectedArduino"] is True


def test_post_config_stores_rotors_and_notifies_arduino(tmp_path: Path) -> None:
    client, store, fake_handler = make_client(tmp_path)

    response = client.post(
        "/config",
        json={
            "rotors": [
                {"id": 1, "position": 5},
                {"id": 3, "position": 3},
                {"id": 4, "position": 10},
            ]
        },
    )

    assert response.status_code == 200
    saved = store.get_config()
    assert [slot.id for slot in saved.rotors] == [1, 3, 4]
    assert fake_handler.config_pushes == 1


def test_get_message_forwards_cipher_to_arduino(tmp_path: Path) -> None:
    client, _, fake_handler = make_client(tmp_path)

    response = client.get("/message/HELLO")

    assert response.status_code == 200
    body = response.json()
    assert body["cipher"] == "HELLO"
    assert body["status"] == "received"
    assert fake_handler.ciphers == ["HELLO"]


def test_get_message_rejects_invalid_payload(tmp_path: Path) -> None:
    client, _, fake_handler = make_client(tmp_path)

    response = client.get("/message/123")

    assert response.status_code == 400
    assert fake_handler.ciphers == []


def test_has_message_returns_null_when_empty(tmp_path: Path) -> None:
    client, _, _ = make_client(tmp_path)

    response = client.get("/has-message")

    assert response.status_code == 200
    assert response.json() == {"cipher": None}


def test_has_message_returns_pending_and_clears(tmp_path: Path) -> None:
    client, store, _ = make_client(tmp_path)
    store.set_pending_cipher("ABC")

    first = client.get("/has-message")
    second = client.get("/has-message")

    assert first.json() == {"cipher": "ABC"}
    assert second.json() == {"cipher": None}


def test_post_config_rejects_more_than_four_rotors(tmp_path: Path) -> None:
    client, _, _ = make_client(tmp_path)

    response = client.post(
        "/config",
        json={
            "rotors": [
                {"id": 1, "position": 0},
                {"id": 2, "position": 0},
                {"id": 3, "position": 0},
                {"id": 4, "position": 0},
                {"id": 5, "position": 0},
            ]
        },
    )

    assert response.status_code == 422


def test_post_config_rejects_duplicate_ids(tmp_path: Path) -> None:
    client, _, _ = make_client(tmp_path)

    response = client.post(
        "/config",
        json={"rotors": [{"id": 1, "position": 0}, {"id": 1, "position": 5}]},
    )

    assert response.status_code == 422
