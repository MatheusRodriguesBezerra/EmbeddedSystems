from fastapi import FastAPI, HTTPException, Query

from config import APP_NAME
from comm.protocol import MobileProtocol
from enigma.machine import EnigmaMachine
from enigma.models import MachineConfig, MessageAck, PingResponse
from state.store import StateStore


def create_app(store: StateStore, machine: EnigmaMachine) -> FastAPI:
    app = FastAPI(title=APP_NAME)
    protocol = MobileProtocol(store, machine)

    @app.get("/ping", response_model=PingResponse)
    def ping() -> PingResponse:
        state = store.get_machine_state()
        return PingResponse(connectedArduino=state.connectedArduino)

    @app.get("/state")
    def get_state():
        return store.get_machine_state()

    @app.post("/config")
    def set_config(config: MachineConfig):
        return store.set_config(config)

    @app.get("/message/{payload}", response_model=MessageAck)
    def receive_message(payload: str, messageId: str | None = Query(default=None)) -> MessageAck:
        try:
            return protocol.receive_payload(payload, messageId)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/outgoing/{plain_text}", response_model=MessageAck)
    def build_outgoing_message(plain_text: str) -> MessageAck:
        try:
            return protocol.build_outgoing_payload(plain_text)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return app
