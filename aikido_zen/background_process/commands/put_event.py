from .command import Command, CommandContext, Payload


class PutEventReq:
    def __init__(self, event):
        # Event is a dictionary containing data that is going to be reported to core
        # "time" and "agent" fields are added by default from the CloudConnectionManager
        self.event = event


class PutEventCommand(Command):
    @classmethod
    def identifier(cls) -> str:
        return "put_event"

    @classmethod
    def returns_data(cls) -> bool:
        return False

    @classmethod
    def run(cls, context: CommandContext, request: PutEventReq):
        context.queue.put(request.event)

    @classmethod
    def generate(cls, event) -> Payload:
        return Payload(cls, PutEventReq(event))
