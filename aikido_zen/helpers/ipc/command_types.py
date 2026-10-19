from abc import ABC, abstractmethod


class CommandContext:
    def __init__(self, connection_manager, queue):
        self.connection_manager = connection_manager
        self.queue = queue


class Payload:
    def __init__(self, command, request):
        self.identifier = command.identifier()
        self.request = request


class Command(ABC):
    @classmethod
    @abstractmethod
    def identifier(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def run(cls, context: CommandContext, request):
        pass

    @classmethod
    @abstractmethod
    def generate(cls, request) -> Payload:
        pass
