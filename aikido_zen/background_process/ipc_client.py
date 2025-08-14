import multiprocessing.connection
import threading

from aikido_zen.helpers.logging import logger
from enum import Enum

class Actions(Enum):
    ATTACK = "ATTACK"

class SendResult:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
    def success(self):
        return self.error is None

class AikidoIPCClient:
    _thread_local = threading.local()

    def __init__(self, address):
        self.address = address
        self.client: multiprocessing.connection.Connection = None

        # Define instance for entire thread
        AikidoIPCClient._thread_local.instance = self

    @staticmethod
    def get():
        if not hasattr(AikidoIPCClient._thread_local, 'instance'):
            return None
        return AikidoIPCClient._thread_local.instance
    @staticmethod
    def reset():
        AikidoIPCClient._thread_local.instance = None

    def connect(self):
        try:
            self.client = multiprocessing.connection.Client(self.address)
        except Exception as e:
            logger.debug("Error establishing ipc client: %s", e)

    def close(self):
        if not self.client:
            return
        try:
            self.client.close()
        except Exception as e:
            logger.debug("Error closing ipc client: %s", e)
        finally:
            self.client = None

    def send(self, action: Actions, data, should_receive: bool) -> SendResult:
        if not self.client:
            return SendResult(error="Client not defined.")

        package = (action.value, data)
        self.client.send(package)

        if should_receive:
            data = self.client.recv()
            return SendResult(result=data)

        return SendResult()
