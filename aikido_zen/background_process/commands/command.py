from abc import ABC, abstractmethod


class CommandContext:
    def __init__(self, connection_manager, queue, connection):
        self.connection_manager = connection_manager
        self.queue = queue
        self.connection = connection

    def send(self, response):
        self.connection.send(response)


class Command(ABC):
    @classmethod
    @abstractmethod
    def identifier(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def run(cls, context: CommandContext, request):
        pass
