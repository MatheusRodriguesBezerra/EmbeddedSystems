import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from comm.arduino_handler import ArduinoHandler
from comm.protocol import MobileProtocol, config_for_pi_from_app
from comm.serial_service import SerialService
from config import APP_NAME
from enigma.models import (
    AppRoleUpdate,
    CipherTransfer,
    MachineConfig,
    MessageAck,
    PendingOutgoing,
    PingResponse,
    TransferRole,
)
from state.store import StateStore

logger = logging.getLogger(__name__)


def create_app(
    store: StateStore,
    protocol: MobileProtocol,
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

    @app.get("/state")
    def get_state():
        state = store.get_machine_state()
        pending = store.get_pending_outgoing()
        return {
            **state.model_dump(),
            "pending": pending.model_dump(),
        }

    @app.post("/config")
    def set_config(config: MachineConfig):
        """Sincronizacao explicita de rotores (app mobile -> Pi -> Arduino SYNC)."""
        pi_config = config_for_pi_from_app(config)
        updated = store.set_config(pi_config)
        if arduino_handler:
            arduino_handler.push_config_to_arduino()
        return updated

    @app.post("/role")
    def set_app_role(update: AppRoleUpdate):
        """Atualiza apenas o turno half-duplex, sem alterar posicoes dos rotores."""
        current = store.get_config()
        pi_role = update.role
        if update.role in (TransferRole.SENDING, TransferRole.RECEIVING):
            pi_role = config_for_pi_from_app(
                current.model_copy(update={"role": update.role})
            ).role
        updated = store.set_config(current.model_copy(update={"role": pi_role}))
        return updated

    @app.post("/message", response_model=MessageAck)
    def relay_message_post(body: CipherTransfer) -> MessageAck:
        """Encaminha payload cifrado (mobile -> Pi -> Arduino). Sem rotores."""
        return _relay_cipher(body.payload, body.messageId)

    @app.get("/message/{payload}", response_model=MessageAck)
    def relay_message_get(
        payload: str,
        messageId: str | None = Query(default=None),
    ) -> MessageAck:
        """Encaminha payload cifrado via GET (compatibilidade). Sem rotores."""
        return _relay_cipher(payload, messageId)

    def _relay_cipher(payload: str, message_id: str | None = None) -> MessageAck:
        try:
            ack = protocol.relay_cipher_from_mobile(payload, message_id)
            if arduino_handler:
                arduino_handler.push_cipher_to_arduino(ack.payload)
            return ack
        except ValueError as error:
            logger.warning("Relay /message rejeitado: %s", error)
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/pending", response_model=PendingOutgoing)
    def get_pending(consume: bool = Query(default=True)) -> PendingOutgoing:
        """Mensagem cifrada enviada pelo Arduino para o app (somente payload)."""
        if consume:
            return store.clear_pending_outgoing()
        return store.get_pending_outgoing()

    return app
