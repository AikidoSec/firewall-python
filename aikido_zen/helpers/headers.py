from typing import List, Optional


class AlternateReading(str):
    """A second decoding of the same header field. get_fields skips it."""


class Headers(dict):
    def store_headers(self, key: str, values: List[str]):
        normalized_key = self.normalize_header_key(key)
        if self.get(normalized_key, []):
            self[normalized_key] += values
        else:
            self[normalized_key] = values

    def store_header(self, key: str, value: str):
        self.store_headers(key, [value])

    def get_header(self, key: str) -> Optional[str]:
        self.validate_header_key(key)
        if self.get(key, []):
            return self.get(key)[-1]
        return None

    def get_fields(self, key: str) -> List[str]:
        return [v for v in self.get(key, []) if not isinstance(v, AlternateReading)]

    @staticmethod
    def validate_header_key(key: str):
        if not key.isupper():
            raise ValueError("Header key must be uppercase.")
        if "-" in key:
            raise ValueError("Header key must use underscores instead of dashes.")

    @staticmethod
    def normalize_header_key(key: str) -> str:
        result = str(key)
        result = result.replace("-", "_")
        result = result.upper()
        return result
