import logging
import threading
import time
from collections.abc import Callable

import serial
from serial import SerialException

logger = logging.getLogger(__name__)


class SerialService:
    """Leitura/escrita USB Serial com o Arduino (linhas terminadas em \\n)."""

    def __init__(
        self,
        port: str,
        baud: int,
        on_line: Callable[[str], None],
        on_connection_change: Callable[[bool], None] | None = None,
    ) -> None:
        self.port = port
        self.baud = baud
        self._on_line = on_line
        self._on_connection_change = on_connection_change
        self._serial: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._write_lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def start(self) -> bool:
        try:
            self._serial = serial.Serial(self.port, self.baud, timeout=0.1)
            time.sleep(2.0)
        except SerialException as error:
            logger.warning("Serial indisponivel em %s: %s", self.port, error)
            self._notify_connection(False)
            return False

        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, name="enigma-serial", daemon=True)
        self._thread.start()
        self._notify_connection(True)
        logger.info("Serial aberta: %s @ %s baud", self.port, self.baud)
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        with self._write_lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = None
        self._notify_connection(False)

    def send_line(self, line: str) -> bool:
        payload = f"{line.strip()}\n".encode("ascii", errors="ignore")
        with self._write_lock:
            if not self.is_connected or self._serial is None:
                logger.warning("Serial nao conectada; ignorado envio: %s", line)
                return False
            try:
                self._serial.write(payload)
                self._serial.flush()
                logger.debug("Serial -> %s", line)
                return True
            except SerialException as error:
                logger.error("Falha ao escrever na Serial: %s", error)
                return False

    def _notify_connection(self, connected: bool) -> None:
        if self._on_connection_change:
            self._on_connection_change(connected)

    def _read_loop(self) -> None:
        buffer = ""
        while not self._stop.is_set():
            try:
                if self._serial is None:
                    break
                chunk = self._serial.read(256)
                if not chunk:
                    continue
                buffer += chunk.decode("ascii", errors="ignore")
            except SerialException as error:
                logger.error("Erro na leitura Serial: %s", error)
                break

            while "\n" in buffer or "\r" in buffer:
                for separator in ("\r\n", "\n", "\r"):
                    if separator in buffer:
                        line, buffer = buffer.split(separator, 1)
                        line = line.strip()
                        if line:
                            self._on_line(line)
                        break

        self._notify_connection(False)
