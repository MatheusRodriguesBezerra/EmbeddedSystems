import os
from pathlib import Path


APP_NAME = "Enigma Machine Raspberry"
HOST = "0.0.0.0"
PORT = 8000
STATE_FILE = Path("state/enigma_state.json")

# USB Serial (Arduino Mega). No Pi: ls -l /dev/ttyACM* /dev/ttyUSB*
SERIAL_PORT = os.getenv("ENIGMA_SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUD = int(os.getenv("ENIGMA_SERIAL_BAUD", "115200"))
SERIAL_ENABLED = os.getenv("ENIGMA_SERIAL_ENABLED", "1") == "1"

# Fiacoes de rotor partilhadas entre Arduino, Mobile e Raspberry. O Raspberry
# nao cifra/decifra (e so ponte), mas mantem estas constantes como fonte de
# verdade para validacao e documentacao.
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ROTOR_WIRINGS: dict[int, str] = {
    1: "EKMFLGDQVZNTOWYHXUSPAIBRCJ",  # I
    2: "AJDKSIRUXBLHWTMCQGZNPYFVOE",  # II
    3: "BDFHJLCPRTXVZNYEIWGAKMUSQO",  # III
    4: "ESLPYHKWRDAVZFXNGMJCQIOBUT",  # IV
    5: "VZBRGITYUPSDNHLXAWMJQOFECK",  # V
    6: "JVMUBRFXDYZNTQEWHGLKOCPISA",  # VI
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"


def assert_valid_wirings() -> None:
    """Garante que cada fiacao e uma permutacao dos 26 caracteres A-Z."""
    expected = set(ALPHABET)
    for rotor_id, wiring in ROTOR_WIRINGS.items():
        if len(wiring) != 26 or set(wiring) != expected:
            raise ValueError(
                f"Fiacao do rotor R{rotor_id} invalida: deve ser permutacao A-Z (got {wiring!r})"
            )
    if len(REFLECTOR_B) != 26 or set(REFLECTOR_B) != expected:
        raise ValueError("Reflector B invalido: deve ser permutacao A-Z.")


assert_valid_wirings()
