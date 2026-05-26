from pydantic import BaseModel, Field, field_validator


class RotorSlot(BaseModel):
    id: int = Field(ge=1, le=6)
    position: int = Field(ge=0, le=25)


class MachineConfig(BaseModel):
    rotors: list[RotorSlot] = Field(default_factory=list, max_length=4)

    @field_validator("rotors")
    @classmethod
    def validate_rotors(cls, value: list[RotorSlot]) -> list[RotorSlot]:
        if len(value) > 4:
            raise ValueError("No maximo 4 rotores podem estar ativos.")
        ids = [slot.id for slot in value]
        if len(set(ids)) != len(ids):
            raise ValueError("Cada rotor deve aparecer no maximo uma vez.")
        return value


class MachineState(MachineConfig):
    connectedArduino: bool = False


class PingResponse(BaseModel):
    status: str = "ok"
    connectedArduino: bool = False


class MessageReceipt(BaseModel):
    status: str = "received"
    cipher: str


class HasMessageResponse(BaseModel):
    cipher: str | None = None


class StoredState(BaseModel):
    config: MachineConfig = Field(default_factory=MachineConfig)
    connectedArduino: bool = False
    pendingCipher: str = ""
