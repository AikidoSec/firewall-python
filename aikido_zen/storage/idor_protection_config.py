class IdorProtectionConfig:
    def __init__(self, tenant_column_name, excluded_tables):
        self.tenant_column_name = tenant_column_name
        self.excluded_tables = excluded_tables


class IdorProtectionStore:
    def __init__(self):
        self.config = None

    def get(self):
        return self.config

    def set(self, config):
        self.config = config

    def clear(self):
        self.config = None


idor_protection_store = IdorProtectionStore()
