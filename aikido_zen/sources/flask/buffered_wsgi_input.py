import io

# Bigger bodies pass through unscanned, so large uploads the app streams aren't copied.
MAX_BUFFERED_BODY_SIZE = 20 * 1024 * 1024

# Some servers' streams reserve the full requested size before any data arrives, so
# read in pieces and let memory grow only with the bytes the client sent.
READ_CHUNK_SIZE = 64 * 1024

# Flask parses these itself and the form hook stores the parsed fields. Copying them
# here as well would also copy every uploaded file.
FORM_CONTENT_TYPES = ("multipart/form-data", "application/x-www-form-urlencoded")


def buffer_wsgi_input(environ, context):
    """Lets the context see a body that the app reads straight from wsgi.input"""
    from werkzeug.wsgi import get_content_length

    stream = environ.get("wsgi.input")
    content_type = environ.get("CONTENT_TYPE", "").lower()
    if stream is None or content_type.startswith(FORM_CONTENT_TYPES):
        return
    environ["wsgi.input"] = BufferedWsgiInput(
        stream,
        context,
        get_content_length(environ),
        # Werkzeug only checks that the key is present, so a False value counts too.
        "wsgi.input_terminated" in environ,
    )


class BufferedWsgiInput:
    """Reads the body into memory on the first read, gives it to the context once and
    serves every read from that copy"""

    def __init__(self, stream, context, content_length, terminated):
        self._stream = stream
        self._context = context
        self._content_length = content_length
        self._terminated = terminated
        self._source = None

    def read(self, *args):
        return self._load().read(*args)

    def readline(self, *args):
        return self._load().readline(*args)

    def readlines(self, *args):
        return self._load().readlines(*args)

    def readinto(self, buffer):
        source = self._load()
        if hasattr(source, "readinto"):
            return source.readinto(buffer)
        # WSGI servers such as uWSGI only provide read.
        data = source.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)

    def __iter__(self):
        return iter(self._load())

    def __next__(self):
        return next(self._load())

    def __getattr__(self, name):
        # Copying looks up _stream before __init__ ran, which would recurse forever,
        # and on Python 3.10 and older would take __getstate__ from the server's stream.
        if name in ("_stream", "_source") or name.startswith("__"):
            raise AttributeError(name)
        # Attributes come from the server's stream, so one it lacks stays missing as
        # without Zen. Every read method loads the body first, and after the first
        # read seek and tell use the copy.
        attribute = getattr(self._stream, name)
        if name == "read1":
            return lambda *args: self._load().read1(*args)
        if name == "readinto1":
            return lambda *args: self._load().readinto1(*args)
        if name == "readall":
            # io.BytesIO has no readall, and read() returns the same rest of the body.
            return lambda: self._load().read()
        if name == "peek":
            return lambda *args: peek(self._load(), *args)
        if name in ("seek", "tell") and self._source is not None:
            return getattr(self._source, name)
        return attribute

    def _load(self):
        if self._source is None:
            self._source = self._open_source()
            # Werkzeug iterates a stream one byte per call, so later reads go straight
            # to the source instead of through these Python methods.
            for name in ("read", "readline", "readlines", "readinto"):
                if hasattr(self._source, name):
                    setattr(self, name, getattr(self._source, name))
        return self._source

    def _open_source(self):
        if (
            self._content_length is not None
            and self._content_length > MAX_BUFFERED_BODY_SIZE
        ):
            return self._stream
        if self._terminated:
            # The server ends the stream itself, so read to the end and ignore
            # Content-Length like werkzeug does: a chunked or decoded body can differ.
            body = read_up_to(self._stream, MAX_BUFFERED_BODY_SIZE + 1)
            if len(body) > MAX_BUFFERED_BODY_SIZE:
                return io.BufferedReader(PrefixedStream(body, self._stream))
        elif self._content_length:
            body = read_up_to(self._stream, self._content_length)
        else:
            # Without a usable length the server may not end the stream, so reading
            # ahead could block. Werkzeug gives the app an empty body here too.
            return self._stream
        # The get_data and form hooks may already have stored the parsed body.
        if body and self._context.body is None:
            self._context.set_body(body)
        return io.BytesIO(body)


def peek(stream, size=0):
    """Returns the next bytes without consuming them, like BufferedReader.peek"""
    if hasattr(stream, "peek"):
        return stream.peek(size)
    # BufferedReader.peek returns its whole buffer, whatever size is asked for.
    data = stream.read(io.DEFAULT_BUFFER_SIZE)
    stream.seek(-len(data), io.SEEK_CUR)
    return data


def read_up_to(stream, size):
    chunks = []
    while size > 0:
        chunk = stream.read(min(size, READ_CHUNK_SIZE))
        if not chunk:
            break
        chunks.append(chunk)
        size -= len(chunk)
    return b"".join(chunks)


class PrefixedStream(io.RawIOBase):
    """Serves bytes that were already read, then the rest of the stream"""

    def __init__(self, prefix, stream):
        super().__init__()
        self._prefix = io.BytesIO(prefix)
        self._stream = stream

    def readable(self):
        return True

    def readinto(self, buffer):
        size = self._prefix.readinto(buffer)
        if size:
            return size
        data = self._stream.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)
