import logging

import uvicorn

from comm.arduino_handler import ArduinoHandler
from comm.mobile_server import create_app
from comm.protocol import MobileProtocol
from comm.serial_service import SerialService
from config import HOST, PORT, SERIAL_BAUD, SERIAL_ENABLED, SERIAL_PORT, STATE_FILE
from enigma.machine import EnigmaMachine
from state.store import StateStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class _SkipPendingAccessLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/pending" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(_SkipPendingAccessLog())

store = StateStore(STATE_FILE)
machine = EnigmaMachine()
protocol = MobileProtocol(store, machine)

serial_service: SerialService | None = None
arduino_handler: ArduinoHandler | None = None

if SERIAL_ENABLED:
    serial_service = SerialService(
        port=SERIAL_PORT,
        baud=SERIAL_BAUD,
        on_line=lambda line: arduino_handler.handle_line(line) if arduino_handler else None,
        on_connection_change=store.set_arduino_connected,
    )
    arduino_handler = ArduinoHandler(store, machine, protocol, serial_service)

app = create_app(store, machine, serial_service, arduino_handler)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
