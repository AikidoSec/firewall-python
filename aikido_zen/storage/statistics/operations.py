SUPPORTED_KINDS = [
    "sql_op",
    "nosql_op",
    "outgoing_http_op",
    "fs_op",
    "exec_op",
    "deserialize_op",
    "ai_op",
]


class Operations(dict):
    def __init__(self):
        super().__init__()

    def ensure_operation(self, operation, kind):
        if not kind in SUPPORTED_KINDS:
            raise Exception(f"Kind {kind} is not supported for operations.")
        if not operation in self.keys():
            self[operation] = {
                "kind": kind,
                "total": 0,
                "attacksDetected": {
                    "total": 0,
                    "blocked": 0,
                },
            }

    def register_call(self, operation, kind):
        self.ensure_operation(operation, kind)
        self[operation]["total"] += 1

    def on_detected_attack(self, blocked, operation):
        if operation not in self.keys():
            return

        self[operation]["attacksDetected"]["total"] += 1
        if blocked:
            self[operation]["attacksDetected"]["blocked"] += 1

    def update(self, m, /, **kwargs):
        for operation in m.keys():
            self.ensure_operation(operation, kind=m[operation]["kind"])

            self[operation]["total"] += m[operation]["total"]

            imported_attacks_total = m[operation]["attacksDetected"]["total"]
            self[operation]["attacksDetected"]["total"] += imported_attacks_total

            imported_attacks_blocked = m[operation]["attacksDetected"]["blocked"]
            self[operation]["attacksDetected"]["blocked"] += imported_attacks_blocked
