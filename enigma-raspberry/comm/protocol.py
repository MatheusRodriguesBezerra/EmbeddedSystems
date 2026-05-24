from uuid import uuid4

from config import ALPHABET
from enigma.machine import EnigmaMachine
from enigma.models import HistoryItem, MachineConfig, MessageAck, TransferRole
from state.store import StateStore


def sanitize_payload(payload: str) -> str:
    return "".join(char for char in payload.upper() if char in ALPHABET)


def complementary_role(role: TransferRole) -> TransferRole:
    if role == TransferRole.SENDING:
        return TransferRole.RECEIVING
    if role == TransferRole.RECEIVING:
        return TransferRole.SENDING
    return TransferRole.IDLE


class MobileProtocol:
    def __init__(self, store: StateStore, machine: EnigmaMachine) -> None:
        self.store = store
        self.machine = machine

    def receive_payload(self, payload: str, message_id: str | None = None) -> MessageAck:
        clean_payload = sanitize_payload(payload)
        if not clean_payload:
            raise ValueError("Payload vazio ou sem caracteres A-Z.")

        config = self.store.get_config()
        if config.role != TransferRole.RECEIVING:
            raise ValueError("Raspberry não está em RECEIVING.")

        resolved_message_id = message_id or str(uuid4())
        if self.store.has_processed(resolved_message_id):
            raise ValueError("Mensagem duplicada.")

        plain_text, next_positions = self.machine.process_message(clean_payload, config)
        next_role = complementary_role(config.role)
        self.store.set_positions_and_role(next_positions, next_role)
        self.store.add_history(
            HistoryItem(
                messageId=resolved_message_id,
                direction="received",
                payload=clean_payload,
                plainText=plain_text,
                positions=next_positions,
                mode=config.mode,
            )
        )

        return MessageAck(
            payload=clean_payload,
            messageId=resolved_message_id,
            plainText=plain_text,
            positions=next_positions,
            role=next_role,
        )

    def build_outgoing_payload(self, plain_text: str) -> MessageAck:
        clean_text = sanitize_payload(plain_text)
        if not clean_text:
            raise ValueError("Mensagem vazia ou sem caracteres A-Z.")

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            raise ValueError("Raspberry não está em SENDING.")

        payload, next_positions = self.machine.process_message(clean_text, config)
        message_id = str(uuid4())
        next_role = complementary_role(config.role)
        self.store.set_positions_and_role(next_positions, next_role)
        self.store.add_history(
            HistoryItem(
                messageId=message_id,
                direction="sent",
                payload=payload,
                plainText=clean_text,
                positions=next_positions,
                mode=config.mode,
            )
        )

        return MessageAck(
            payload=payload,
            messageId=message_id,
            plainText=clean_text,
            positions=next_positions,
            role=next_role,
        )

    def accept_physical_outgoing(self, cipher_payload: str) -> MessageAck:
        """Payload ja cifrado no Arduino; alinha rotores no Pi e guarda para o app."""
        clean_payload = sanitize_payload(cipher_payload)
        if not clean_payload:
            raise ValueError("PAYLOAD_VAZIO")

        config = self.store.get_config()
        if config.role != TransferRole.SENDING:
            raise ValueError("NOT_SENDING")

        plain_text, next_positions = self.machine.process_message(clean_payload, config)
        message_id = str(uuid4())
        next_role = complementary_role(config.role)
        self.store.set_positions_and_role(next_positions, next_role)
        self.store.set_pending_outgoing(clean_payload, message_id, plain_text)
        self.store.add_history(
            HistoryItem(
                messageId=message_id,
                direction="sent",
                payload=clean_payload,
                plainText=plain_text,
                positions=next_positions,
                mode=config.mode,
            )
        )

        return MessageAck(
            status="received",
            payload=clean_payload,
            messageId=message_id,
            plainText=plain_text,
            positions=next_positions,
            role=next_role,
        )


def parse_serial_command(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split(":")
    return parts[0].upper(), parts[1:]
