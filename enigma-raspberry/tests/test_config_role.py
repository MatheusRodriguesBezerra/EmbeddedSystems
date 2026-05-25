from comm.protocol import config_for_pi_from_app
from enigma.models import MachineConfig, RotorSlot, TransferRole


def test_config_maps_app_sending_to_pi_receiving():
    app_config = MachineConfig(
        slots=[
            RotorSlot(id=1, position=4),
            RotorSlot(id=2, position=6),
            RotorSlot(id=3, position=8),
        ],
        mode="DEC",
        role=TransferRole.SENDING,
    )

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.RECEIVING
    assert pi_config.slots[0].position == 4


def test_config_maps_app_receiving_to_pi_sending():
    app_config = MachineConfig(role=TransferRole.RECEIVING)

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.SENDING


def test_config_idle_stays_idle():
    app_config = MachineConfig(role=TransferRole.IDLE)

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.IDLE
