from comm.protocol import config_for_pi_from_app
from enigma.models import MachineConfig, RotorSlot, TransferRole
from state.store import StateStore


def test_role_endpoint_only_changes_pi_role(tmp_path):
    store = StateStore(tmp_path / "state.json")
    store.set_config(
        MachineConfig(
            slots=[
                RotorSlot(id=1, position=4),
                RotorSlot(id=2, position=6),
                RotorSlot(id=3, position=8),
            ],
            role=TransferRole.RECEIVING,
        )
    )

    current = store.get_config()
    pi_role = config_for_pi_from_app(
        current.model_copy(update={"role": TransferRole.RECEIVING})
    ).role
    store.set_config(current.model_copy(update={"role": pi_role}))

    result = store.get_config()
    assert result.role == TransferRole.SENDING
    assert result.slots[1].position == 6
