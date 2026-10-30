# Proxy members are supplied by wrapt's C extension.
# pylint: disable=abstract-method,no-member

from wrapt import ObjectProxy


class LazyBodyStream(ObjectProxy):
    _READ_METHODS = (
        "read",
        "readall",
        "read1",
        "readinto",
        "readinto1",
        "readline",
        "readlines",
        "peek",
    )

    def __init__(self, stream, before_read):
        super().__init__(stream)
        self._self_before_read = before_read

    def _prepare(self):
        callback = self._self_before_read
        # Body capture reads this stream too, so it must not trigger itself.
        self._self_before_read = None
        if callback is not None:
            callback()

    def __getattr__(self, name):
        value = getattr(self.__wrapped__, name)
        if name not in self._READ_METHODS or self._self_before_read is None:
            return value

        def read(*args, **kwargs):
            self._prepare()
            return getattr(self.__wrapped__, name)(*args, **kwargs)

        return read

    def __iter__(self):
        self._prepare()
        return iter(self.__wrapped__)

    def __next__(self):
        self._prepare()
        return next(self.__wrapped__)
