"""Exports extract_data_from_xml_body helper function"""

import codecs

import aikido_zen.context as ctx
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.modify_arguments import modify_arguments


def extract_data_from_xml_body(user_input, root_element):
    """Extracts all attributes and text from the xml and adds them to context"""
    try:
        context = ctx.get_current_context()
        if not context or not isinstance(context.body, str):
            return

        if isinstance(user_input, (bytes, bytearray, memoryview)):
            user_input = bytes(user_input).decode("utf-8", errors="replace")
        if user_input != context.body:
            return

        add_elements_to_context(context, root_element.iter())
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)


def add_elements_to_context(context, elements):
    extracted_xml = context.xml
    tag = None
    for element in elements:
        if isinstance(element.tag, str):
            tag = element.tag
            texts = (element.text, element.tail)
            for key, value in element.items():
                extracted_xml.setdefault(key, set()).add(value)
        else:
            # The text after a comment or processing instruction is in its tail.
            texts = (element.tail,) if tag else ()
        for text in texts:
            if not text:
                continue
            stripped = text.strip()
            if not stripped:
                continue
            extracted_xml.setdefault(tag, set()).update((text, stripped))
    context.set_as_current_context()


class BodyMatcher:
    """Tells whether the chunks a parser was fed so far are the start of the request body"""

    __slots__ = ("body", "fed", "decoder")

    def __init__(self, body):
        self.body = body
        self.fed = 0
        # A chunk can end inside a multi-byte character, so decode across chunks.
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def continues_body(self, data, final):
        # Decoding the same way Context does keeps non-UTF-8 bodies matching.
        if not isinstance(data, str):
            data = self.decoder.decode(bytes(data), final)
        if not self.body.startswith(data, self.fed):
            return False
        self.fed += len(data)
        return True

    def is_whole_body(self):
        return self.fed == len(self.body)


class BodyReader:
    """Wraps the file a parser reads, so what it reads can be compared to the request body"""

    def __init__(self, source, context):
        self.source = source
        self.context = context
        self.matcher = BodyMatcher(context.body)
        self.matches = True

    def read(self, *args):
        data = self.source.read(*args)
        if self.matches:
            try:
                self.matches = self.matcher.continues_body(data, final=not data)
            except Exception as e:
                logger.debug("Exception occurred when extracting XML: %s", e)
                self.matches = False
        return data

    def read_whole_body(self):
        return self.matches and self.matcher.is_whole_body()

    def __getattr__(self, name):
        # lxml takes everything from getvalue() when it exists, which would skip read().
        if name == "getvalue":
            raise AttributeError(name)
        return getattr(self.source, name)


def body_reader(args, kwargs, name):
    """Puts a BodyReader in place of the source argument when this request has a text body

    The parser then reads through it, so what it reads can be compared to the body.
    """
    try:
        context = ctx.get_current_context()
        source = args[0] if args else kwargs.get(name)
        if (
            not context
            or not isinstance(context.body, str)
            or not hasattr(source, "read")
        ):
            return None, args, kwargs
        reader = BodyReader(source, context)
        return (reader,) + modify_arguments(args, kwargs, 0, name, reader)
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)
        return None, args, kwargs


def add_parsed_tree_to_context(reader, root_element):
    try:
        if reader is not None and reader.read_whole_body():
            add_elements_to_context(reader.context, root_element.iter())
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)


class IterparseCollector:
    """Yields what iterparse yields, adding each element to the context before the app gets it

    Apps query inside the loop and often clear elements as they go, so collecting at
    the end would be too late. The parser reads ahead, so text is already set at "start".
    """

    def __init__(self, events, reader):
        self._events = events
        self._reader = reader

    def __iter__(self):
        return self

    def __next__(self):
        event, element = next(self._events)
        if self._reader.matches and hasattr(element, "tag"):
            try:
                # Comments and processing instructions are not events, so their tails
                # are only reachable through the element that contains them.
                add_elements_to_context(
                    self._reader.context,
                    [element] + [c for c in element if not isinstance(c.tag, str)],
                )
                # Strings are cached on the first sink call, and iterparse apps query
                # inside the loop, so drop the cache to scan the new values.
                self._reader.context.parsed_userinput.pop("xml", None)
            except Exception as e:
                logger.debug("Exception occurred when extracting XML: %s", e)
        return event, element

    def __getattr__(self, name):
        return getattr(self._events, name)
