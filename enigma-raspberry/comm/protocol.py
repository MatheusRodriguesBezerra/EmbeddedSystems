from uuid import uuid4

from config import ALPHABET
from enigma.models import HistoryItem, MachineConfig, MessageAck, RotorSlot, TransferRole
from state.store import StateStore


def sanitize_payload(payload: str) -> str:
    return "".join(char for char in payload.upper() if char in ALPHABET)


def complementary_role(role: TransferRole) -> TransferRole:
    if role == TransferRole.SENDING:
        return TransferRole.RECEIVING
    if role == TransferRole.RECEIVING:
        return TransferRole.SENDING
    return TransferRole.IDLE


def config_for_pi_from_app(config: MachineConfig) -> MachineConfig:
    """O body de POST /config traz o role do app; o Pi guarda o complementar."""
    if config.role in (TransferRole.SENDING, TransferRole.RECEIVING):
        return config.model_copy(update={"role": complementary_role(config.role)})
    return config


def parse_slots_csv(value: str) -> list[RotorSlot]:
    clean = value.strip()
    if not clean:
        return []

    parts = [part.strip() for part in clean.split(",") if part.strip()]
    if len(parts) % 2 != 0:
        raise ValueError("Slots invalidos: use pares id,pos.")

    slots: list[RotorSlot] = []
    for index in range(0, len(parts), 2):
        slots.append(
            RotorSlot(
                id=int(parts[index]),
                position=int(parts[index + 1]),
            )
        )
    MachineConfig(slots=slots)
    return slots


class MobileProtocol:
    """Ponte half-duplex: transporte de mensagens e turno; sem cifra/decifra."""

    def __init__(self, store: StateStore) -> None:
        self.store = store

    def relay_cipher_from_mobile(
        self,
        payload: str,
        message_id: str | None = None,
    ) -> MessageAck:
        clean_payload = sanitize_payload(payload)
        if not clean_payload:
            raise ValueError("Payload vazio ou sem caracteres A-Z.")

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            raise ValueError("Raspberry nao esta em SENDING.")

        resolved_message_id = message_id or str(uuid4())
        if self.store.has_processed(resolved_message_id):
            raise ValueError("Mensagem duplicada.")

        next_role = self._flip_role()
        self.store.add_history(
            HistoryItem(
                messageId=resolved_message_id,
                direction="sent",
                payload=clean_payload,
                plainText="",
                slots=[],
                mode=config.mode,
            )
        )

        return MessageAck(
            payload=clean_payload,
            messageId=resolved_message_id,
            plainText="",
            role=next_role,
        )

    def relay_cipher_from_arduino(self, payload: str) -> MessageAck:
        clean_payload = sanitize_payload(payload)
        if not clean_payload:
            raise ValueError("PAYLOAD_VAZIO")

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            raise ValueError("NOT_SENDING")

        message_id = str(uuid4())
        next_role = self._flip_role()
        self.store.set_pending_outgoing(clean_payload, message_id)
        self.store.add_history(
            HistoryItem(
                messageId=message_id,
                direction="sent",
                payload=clean_payload,
                plainText="",
                slots=[],
                mode=config.mode,
            )
        )

        return MessageAck(
            status="received",
            payload=clean_payload,
            messageId=message_id,
            plainText="",
            role=next_role,
        )

    def _flip_role(self) -> TransferRole:
        config = self.store.get_config()
        next_role = complementary_role(config.role)
        self.store.set_config(config.model_copy(update={"role": next_role}))
        return next_role


def parse_serial_command(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split(":")
    return parts[0].upper(), parts[1:]
