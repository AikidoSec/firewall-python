from .command import Command, CommandContext


class PutEventReq:
    def __init__(self, event):
        # Event is a JSON object ready to be sent to core.
        self.event = event


class PutEventCommand(Command):
    @classmethod
    def identifier(cls) -> str:
        return "put_event"

    @classmethod
    def run(cls, context: CommandContext, request: PutEventReq):
        context.queue.put(request.event)
