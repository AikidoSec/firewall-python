class Payload:
    def __init__(self, identifier, request, timeout_in_sec):
        self.identifier = identifier
        self.request = request
        self.timeout_in_sec = timeout_in_sec
