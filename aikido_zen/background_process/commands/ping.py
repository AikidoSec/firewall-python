from aikido_zen.helpers.ipc.command_types import Command, Payload, CommandContext


class PingCommand(Command):
    @classmethod
    def identifier(cls) -> str:
        return "ping"

    @classmethod
    def returns_data(cls) -> bool:
        return True

    @classmethod
    def run(cls, context: CommandContext, request):
        return "recv"

    @classmethod
    def generate(cls) -> Payload:
        return Payload(cls, {})
