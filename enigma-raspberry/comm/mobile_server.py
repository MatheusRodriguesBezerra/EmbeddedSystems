import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from comm.arduino_handler import ArduinoHandler
from comm.protocol import sanitize_cipher
from comm.serial_service import SerialService
from config import APP_NAME
from enigma.models import (
    HasMessageResponse,
    MachineConfig,
    MessageReceipt,
    PingResponse,
)
from state.store import StateStore

logger = logging.getLogger(__name__)


def create_app(
    store: StateStore,
    serial_service: SerialService | None = None,
    arduino_handler: ArduinoHandler | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if serial_service:
            serial_service.start()
        yield
        if serial_service:
            serial_service.stop()

    app = FastAPI(title=APP_NAME, lifespan=lifespan)

    @app.get("/ping", response_model=PingResponse)
    def ping() -> PingResponse:
        state = store.get_machine_state()
        return PingResponse(connectedArduino=state.connectedArduino)

    @app.post("/config")
    def set_config(config: MachineConfig):
        """Recebe a configuracao de rotores do app mobile."""
        updated = store.set_config(config)
        if arduino_handler:
            try:
                arduino_handler.push_config_to_arduino()
            except Exception as error:
                logger.warning("Falha a enviar POS ao Arduino: %s", error)
        return updated

    @app.get("/message/{cipher}", response_model=MessageReceipt)
    def relay_message(cipher: str) -> MessageReceipt:
        """Cifra vinda do app mobile, encaminhada ao Arduino."""
        clean = sanitize_cipher(cipher)
        if not clean:
            raise HTTPException(status_code=400, detail="Payload invalido.")

        if arduino_handler:
            arduino_handler.push_cipher_to_arduino(clean)

        return MessageReceipt(cipher=clean)

    @app.get("/has-message", response_model=HasMessageResponse)
    def has_message() -> HasMessageResponse:
        """Devolve a ultima cifra recebida do Arduino e limpa o buffer."""
        cipher = store.consume_pending_cipher()
        return HasMessageResponse(cipher=cipher)

    return app
