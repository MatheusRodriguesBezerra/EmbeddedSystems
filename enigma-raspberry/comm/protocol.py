from config import ALPHABET


def sanitize_cipher(value: str) -> str:
    """Mantem apenas letras A-Z em maiusculas."""
    return "".join(char for char in value.upper() if char in ALPHABET)


def parse_pos_line(line: str) -> list[tuple[int, int]]:
    """Converte `POS:r1,p1,r2,p2,...` em lista de (id, position)."""
    if ":" not in line:
        return []
    _, rest = line.split(":", 1)
    rest = rest.strip()
    if not rest:
        return []

    parts = [item.strip() for item in rest.split(",") if item.strip()]
    if len(parts) % 2 != 0:
        raise ValueError("POS invalido: precisa de pares id,pos.")

    result: list[tuple[int, int]] = []
    for index in range(0, len(parts), 2):
        result.append((int(parts[index]), int(parts[index + 1])))
    return result
