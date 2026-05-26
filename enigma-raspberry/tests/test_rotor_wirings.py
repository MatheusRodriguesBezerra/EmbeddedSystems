"""Garante que as fiacoes dos 3 projetos estao sincronizadas e validas.

Se este teste falhar, significa que uma das fiacoes (Arduino, Mobile ou
Raspberry) divergiu das outras, ou que alguma deixou de ser uma permutacao
valida de A-Z. A consequencia pratica e o roundtrip cifrar->decifrar falhar
em algumas letras (assimetria da maquina Enigma).
"""

import re
from pathlib import Path

from config import ALPHABET, REFLECTOR_B, ROTOR_WIRINGS, assert_valid_wirings

REPO_ROOT = Path(__file__).resolve().parents[2]
ARDUINO_CPP = REPO_ROOT / "enigma-arduino" / "enigma_machine" / "enigma.cpp"
MOBILE_TS = REPO_ROOT / "enigma-mobile" / "src" / "services" / "enigmaMachine.ts"


def _extract_quoted_strings(text: str) -> list[str]:
    return re.findall(r'"([A-Z]+)"|\'([A-Z]+)\'', text)


def test_raspberry_wirings_are_valid_permutations() -> None:
    assert_valid_wirings()
    assert set(ROTOR_WIRINGS.keys()) == {1, 2, 3, 4, 5, 6}


def test_arduino_wirings_match_raspberry() -> None:
    text = ARDUINO_CPP.read_text(encoding="utf-8")
    # Captura strings de 26 letras maiusculas dentro de aspas duplas.
    matches = re.findall(r'"([A-Z]{20,30})"', text)
    # Esperamos exatamente 6 fiacoes de rotor + 1 reflector + 1 alfabeto.
    rotor_strings = [m for m in matches if m not in (ALPHABET,)]
    # O ficheiro tem o alfabeto, o reflector e 6 rotores em ordem.
    rotors_from_arduino = rotor_strings[: 6 + 1]
    reflector_from_arduino = rotors_from_arduino[-1]
    rotors_from_arduino = rotors_from_arduino[:-1]

    for rotor_id, wiring in zip(range(1, 7), rotors_from_arduino):
        assert wiring == ROTOR_WIRINGS[rotor_id], (
            f"R{rotor_id} do Arduino diverge do config.py do Raspberry"
        )
    assert reflector_from_arduino == REFLECTOR_B


def test_mobile_wirings_match_raspberry() -> None:
    text = MOBILE_TS.read_text(encoding="utf-8")
    # Capture os valores apos `n:` no objeto literal.
    pattern = re.compile(r"(\d):\s*'([A-Z]{26})'")
    found = {int(rotor_id): wiring for rotor_id, wiring in pattern.findall(text)}

    for rotor_id in range(1, 7):
        assert found.get(rotor_id) == ROTOR_WIRINGS[rotor_id], (
            f"R{rotor_id} do Mobile diverge do config.py do Raspberry"
        )

    # Reflector entre apostrofos.
    reflector_match = re.search(r"REFLECTOR_B\s*=\s*'([A-Z]{26})'", text)
    assert reflector_match is not None
    assert reflector_match.group(1) == REFLECTOR_B


def test_corrupted_wiring_is_rejected(monkeypatch) -> None:
    """Sanity-check: se alguem voltar a meter uma fiacao invalida, assert falha."""
    import config

    monkeypatch.setitem(config.ROTOR_WIRINGS, 5, "VZBRGRIYWATUKQCMLHPFDJNCXESO")
    try:
        config.assert_valid_wirings()
    except ValueError:
        return
    raise AssertionError("assert_valid_wirings deveria ter falhado.")
