import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from comm.arduino_handler import ArduinoHandler
from comm.protocol import MobileProtocol, config_for_pi_from_app
from comm.serial_service import SerialService
from config import APP_NAME
from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, MessageAck, PendingOutgoing, PingResponse
from state.store import StateStore

logger = logging.getLogger(__name__)


def create_app(
    store: StateStore,
    machine: EnigmaMachine,
    serial_service: SerialService | None = None,
    arduino_handler: ArduinoHandler | None = None,
) -> FastAPI:
    protocol = MobileProtocol(store, machine)

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
        pi_config = config_for_pi_from_app(config)
        updated = store.set_config(pi_config)
        if arduino_handler:
            arduino_handler.push_positions_to_arduino()
        return updated

    @app.get("/message/{payload}", response_model=MessageAck)
    def receive_message(payload: str, messageId: str | None = Query(default=None)) -> MessageAck:
        try:
            ack = protocol.receive_payload(payload, messageId)
            if arduino_handler:
                arduino_handler.push_cipher_to_arduino(ack.payload)
                arduino_handler.push_positions_to_arduino()
            return ack
        except ValueError as error:
            logger.warning("GET /message/%s rejeitado: %s", payload, error)
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/outgoing/{plain_text}", response_model=MessageAck)
    def build_outgoing_message(plain_text: str) -> MessageAck:
        try:
            ack = protocol.build_outgoing_payload(plain_text)
            if arduino_handler:
                arduino_handler.push_cipher_to_arduino(ack.payload)
                arduino_handler.push_positions_to_arduino()
            return ack
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/pending", response_model=PendingOutgoing)
    def get_pending(consume: bool = Query(default=True)) -> PendingOutgoing:
        """Mensagem cifrada enviada pela maquina fisica (Arduino) para o app."""
        if consume:
            return store.clear_pending_outgoing()
        return store.get_pending_outgoing()

    return app
