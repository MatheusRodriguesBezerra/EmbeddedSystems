import os
from pathlib import Path


APP_NAME = "Enigma Machine Raspberry"
HOST = "0.0.0.0"
PORT = 8000
STATE_FILE = Path("state/enigma_state.json")

# USB Serial (Arduino Mega). No Pi: ls -l /dev/ttyACM* /dev/ttyUSB*
SERIAL_PORT = os.getenv("ENIGMA_SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUD = int(os.getenv("ENIGMA_SERIAL_BAUD", "115200"))
SERIAL_ENABLED = os.getenv("ENIGMA_SERIAL_ENABLED", "1") == "1"

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
