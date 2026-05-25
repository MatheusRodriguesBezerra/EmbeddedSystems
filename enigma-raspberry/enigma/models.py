from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MachineMode(str, Enum):
    ENC = "ENC"
    DEC = "DEC"


class TransferRole(str, Enum):
    IDLE = "IDLE"
    SENDING = "SENDING"
    RECEIVING = "RECEIVING"


class RotorSlot(BaseModel):
    id: int = Field(ge=1, le=6)
    position: int = Field(ge=0, le=25)


class MachineConfig(BaseModel):
    slots: list[RotorSlot] = Field(default_factory=list, max_length=4)
    mode: MachineMode = MachineMode.ENC
    role: TransferRole = TransferRole.IDLE

    @field_validator("slots")
    @classmethod
    def validate_slots(cls, value: list[RotorSlot]) -> list[RotorSlot]:
        if len(value) > 4:
            raise ValueError("No maximo 4 rotores podem estar ativos.")
        ids = [slot.id for slot in value]
        if len(set(ids)) != len(ids):
            raise ValueError("Cada rotor deve ser usado no maximo uma vez.")
        return value


class MachineState(MachineConfig):
    connectedArduino: bool = False


class PingResponse(BaseModel):
    status: str = "ok"
    connectedArduino: bool = False


class AppRoleUpdate(BaseModel):
    """Papel do app mobile; o Pi guarda o complementar."""
    role: TransferRole


class CipherTransfer(BaseModel):
    payload: str
    messageId: str | None = None


class MessageAck(BaseModel):
    status: str = "received"
    payload: str
    messageId: str
    plainText: str = ""
    role: TransferRole


class PendingOutgoing(BaseModel):
    available: bool = False
    payload: str = ""
    messageId: str = ""
    role: TransferRole = TransferRole.IDLE


class HistoryItem(BaseModel):
    messageId: str
    direction: Literal["sent", "received"]
    payload: str
    plainText: str
    slots: list[RotorSlot]
    mode: MachineMode


class StoredState(BaseModel):
    config: MachineConfig = Field(default_factory=MachineConfig)
    connectedArduino: bool = False
    history: list[HistoryItem] = Field(default_factory=list)
    processedMessageIds: list[str] = Field(default_factory=list)
    pendingPayload: str = ""
    pendingMessageId: str = ""
