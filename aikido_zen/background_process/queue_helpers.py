from aikido_zen.context import Context


class ReportingQueueAttackWaveEvent:
    def __init__(self, context: Context, metadata):
        self.context = context
        self.metadata = metadata
