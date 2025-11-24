from abc import ABC, abstractmethod


class CommandContext:
    def __init__(self, connection_manager, queue, connection):
        self.connection_manager = connection_manager
        self.queue = queue
        self.connection = connection

    def send(self, response):
        self.connection.send(response)


class Payload:
    def __init__(self, command, request):
        self.identifier = command.identifier()
        self.returns_data = command.returns_data()
        self.request = request


class Command(ABC):
    @classmethod
    @abstractmethod
    def identifier(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def returns_data(cls) -> bool:
        pass

    @classmethod
    @abstractmethod
    def run(cls, context: CommandContext, request):
        pass

    @classmethod
    @abstractmethod
    def generate(cls, request) -> Payload:
        pass
