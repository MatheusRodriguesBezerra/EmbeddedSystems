from comm.protocol import config_for_pi_from_app
from enigma.models import MachineConfig, TransferRole


def test_config_maps_app_sending_to_pi_receiving():
    app_config = MachineConfig(
        positions=(4, 6, 8),
        mode="DEC",
        role=TransferRole.SENDING,
    )

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.RECEIVING
    assert pi_config.positions == (4, 6, 8)


def test_config_maps_app_receiving_to_pi_sending():
    app_config = MachineConfig(role=TransferRole.RECEIVING)

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.SENDING


def test_config_idle_stays_idle():
    app_config = MachineConfig(role=TransferRole.IDLE)

    pi_config = config_for_pi_from_app(app_config)

    assert pi_config.role == TransferRole.IDLE
