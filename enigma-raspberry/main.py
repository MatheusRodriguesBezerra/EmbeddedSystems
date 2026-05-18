import uvicorn

from comm.mobile_server import create_app
from config import HOST, PORT, STATE_FILE
from enigma.machine import EnigmaMachine
from state.store import StateStore


store = StateStore(STATE_FILE)
machine = EnigmaMachine()
app = create_app(store, machine)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
