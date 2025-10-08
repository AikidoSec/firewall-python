class TimeoutExceeded(Exception):
    def __init__(self):
        super().__init__("Aikido internal requests library: timeout was exceeded.")
