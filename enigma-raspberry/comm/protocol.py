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


def format_slots_csv(slots: list[RotorSlot]) -> str:
    return ",".join(f"{slot.id},{slot.position}" for slot in slots)


class MobileProtocol:
    """Ponte half-duplex: nao cifra/decifra; apenas estado e transporte."""

    def __init__(self, store: StateStore) -> None:
        self.store = store

    def relay_cipher_from_mobile(
        self,
        payload: str,
        slots_after: list[RotorSlot],
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

        next_role = complementary_role(config.role)
        self._apply_slots_after(slots_after, next_role)
        self.store.add_history(
            HistoryItem(
                messageId=resolved_message_id,
                direction="sent",
                payload=clean_payload,
                plainText="",
                slots=slots_after,
                mode=config.mode,
            )
        )

        return MessageAck(
            payload=clean_payload,
            messageId=resolved_message_id,
            plainText="",
            slots=slots_after,
            role=next_role,
        )

    def relay_cipher_from_arduino(
        self,
        payload: str,
        slots_after: list[RotorSlot],
    ) -> MessageAck:
        clean_payload = sanitize_payload(payload)
        if not clean_payload:
            raise ValueError("PAYLOAD_VAZIO")

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            raise ValueError("NOT_SENDING")

        message_id = str(uuid4())
        next_role = complementary_role(config.role)
        self._apply_slots_after(slots_after, next_role)
        self.store.set_pending_outgoing(clean_payload, message_id)
        self.store.add_history(
            HistoryItem(
                messageId=message_id,
                direction="sent",
                payload=clean_payload,
                plainText="",
                slots=slots_after,
                mode=config.mode,
            )
        )

        return MessageAck(
            status="received",
            payload=clean_payload,
            messageId=message_id,
            plainText="",
            slots=slots_after,
            role=next_role,
        )

    def _apply_slots_after(self, slots_after: list[RotorSlot], next_role: TransferRole) -> None:
        MachineConfig(slots=slots_after)
        self.store.set_slots_and_role(slots_after, next_role)


def parse_serial_command(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split(":")
    return parts[0].upper(), parts[1:]
