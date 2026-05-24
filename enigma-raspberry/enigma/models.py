from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


RotorId = Literal["I", "II", "III"]


class MachineMode(str, Enum):
    ENC = "ENC"
    DEC = "DEC"


class TransferRole(str, Enum):
    IDLE = "IDLE"
    SENDING = "SENDING"
    RECEIVING = "RECEIVING"


class MachineConfig(BaseModel):
    order: tuple[RotorId, RotorId, RotorId] = ("I", "II", "III")
    positions: tuple[int, int, int] = (0, 0, 0)
    mode: MachineMode = MachineMode.ENC
    role: TransferRole = TransferRole.IDLE

    @field_validator("order")
    @classmethod
    def validate_order(cls, value: tuple[RotorId, RotorId, RotorId]) -> tuple[RotorId, RotorId, RotorId]:
        if len(set(value)) != 3:
            raise ValueError("Cada rotor fixo deve ser usado exatamente uma vez.")
        return value

    @field_validator("positions")
    @classmethod
    def validate_positions(cls, value: tuple[int, int, int]) -> tuple[int, int, int]:
        if any(position < 0 or position > 25 for position in value):
            raise ValueError("As posições dos rotores devem estar entre 0 e 25.")
        return value


class MachineState(MachineConfig):
    connectedArduino: bool = False


class PingResponse(BaseModel):
    status: str = "ok"
    connectedArduino: bool = False


class MessageAck(BaseModel):
    status: str = "received"
    payload: str
    messageId: str
    plainText: str
    positions: tuple[int, int, int]
    role: TransferRole


class PendingOutgoing(BaseModel):
    available: bool = False
    payload: str = ""
    messageId: str = ""
    plainText: str = ""
    positions: tuple[int, int, int] = (0, 0, 0)
    role: TransferRole = TransferRole.IDLE


class HistoryItem(BaseModel):
    messageId: str
    direction: Literal["sent", "received"]
    payload: str
    plainText: str
    positions: tuple[int, int, int]
    mode: MachineMode


class StoredState(BaseModel):
    config: MachineConfig = Field(default_factory=MachineConfig)
    connectedArduino: bool = False
    history: list[HistoryItem] = Field(default_factory=list)
    processedMessageIds: list[str] = Field(default_factory=list)
    pendingPayload: str = ""
    pendingMessageId: str = ""
    pendingPlainText: str = ""
