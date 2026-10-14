import aikido_zen.context as ctx
from aikido_zen.helpers.extract_data_from_xml_body import BodyMatcher
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, before_modify_return, patch_function
from wrapt import ObjectProxy

HANDLERS = ("StartElementHandler", "EndElementHandler", "CharacterDataHandler")


class Collector:
    """Adds the values expat reads out of the request body to the context, then calls the app's handlers

    Apps see text cut differently: minidom keeps each piece expat delivers,
    ElementTree joins the pieces up to the next tag, xmltodict joins all of an
    element's text, and sax apps join what they receive. Values are added before
    the app's handler runs, because sax apps query inside them.
    """

    __slots__ = (
        "parser",
        "xml",
        "cache",
        "matcher",
        "tags",
        "text_before_children",
        "pieces_since_last_tag",
        "collecting",
        "StartElementHandler",
        "EndElementHandler",
        "CharacterDataHandler",
    )

    def __init__(self, parser, context):
        self.parser = parser
        self.xml = context.xml
        self.cache = context.parsed_userinput
        self.matcher = BodyMatcher(context.body)
        self.tags = []
        self.text_before_children = []
        self.pieces_since_last_tag = []
        self.collecting = True
        self.StartElementHandler = None
        self.EndElementHandler = None
        self.CharacterDataHandler = None
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.character_data

    def stop(self):
        """Gives the parser back to the app's handlers, so the rest of the parse costs nothing"""
        # With buffer_text on, setting CharacterDataHandler flushes the buffered text
        # through the handler, which can call stop() again from inside this loop.
        if not self.collecting:
            return
        self.collecting = False
        for name in HANDLERS:
            setattr(self.parser, name, getattr(self, name))

    def fail(self, e):
        logger.debug("Exception occurred when extracting XML: %s", e)
        self.stop()

    def add(self, key, value):
        stripped = value.strip()
        if stripped:
            self.xml.setdefault(key, set()).update((value, stripped))
            # Strings are cached on the first sink call, and sax and pulldom apps
            # query while parsing, so drop the cache to scan the new value.
            self.cache.pop("xml", None)

    def end_text_run(self):
        pieces = self.pieces_since_last_tag
        if len(pieces) == 1:
            text = pieces[0]
            if len(text) == 1:
                self.add(self.tags[-1], text)
        else:
            text = "".join(pieces)
            self.add(self.tags[-1], text)
        pieces.clear()
        return text

    def start_element(self, name, attributes):
        try:
            if self.pieces_since_last_tag:
                text = self.end_text_run()
                earlier = self.text_before_children[-1]
                if earlier is None:
                    self.text_before_children[-1] = [text]
                else:
                    earlier.append(text)
            self.tags.append(name)
            # None until a child element splits this element's text, which keeps
            # elements that hold one text node from allocating a list.
            self.text_before_children.append(None)
            if attributes:
                if isinstance(attributes, dict):
                    for key, value in attributes.items():
                        self.add(key, value)
                else:
                    # With ordered_attributes the handler gets [key, value, key, value, ...]
                    for i in range(0, len(attributes), 2):
                        self.add(attributes[i], attributes[i + 1])
        except Exception as e:
            self.fail(e)
        handler = self.StartElementHandler
        if handler is not None:
            handler(name, attributes)

    def end_element(self, name):
        try:
            if self.tags:
                text = self.end_text_run() if self.pieces_since_last_tag else ""
                earlier = self.text_before_children.pop()
                tag = self.tags.pop()
                if earlier is not None:
                    self.add(tag, "".join(earlier) + text)
        except Exception as e:
            self.fail(e)
        handler = self.EndElementHandler
        if handler is not None:
            handler(name)

    def character_data(self, data):
        try:
            if self.tags:
                self.pieces_since_last_tag.append(data)
                # Character references arrive one character per call; the checks
                # skip single characters, and the joined run is added at the next tag.
                if len(data) > 1:
                    self.add(self.tags[-1], data)
        except Exception as e:
            self.fail(e)
        handler = self.CharacterDataHandler
        if handler is not None:
            handler(data)

    def track(self, data, isfinal):
        try:
            if not self.matcher.continues_body(data, isfinal):
                self.stop()
        except Exception as e:
            self.fail(e)


class CollectingParser(ObjectProxy):  # pylint: disable=abstract-method
    """Wraps an expat parser so the Collector sees every value before the app does

    minidom, sax, pulldom, xmltodict and defusedxml all parse through expat, so
    collecting here covers them with one hook.
    """

    def __init__(self, parser, context):
        super().__init__(parser)
        self._self_collector = Collector(parser, context)

    def __getattr__(self, name):
        if name in HANDLERS:
            return getattr(self._self_collector, name)
        return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name in HANDLERS:
            collector = self._self_collector
            setattr(collector, name, value)
            if not collector.collecting:
                setattr(collector.parser, name, value)
        else:
            super().__setattr__(name, value)

    def Parse(self, data, isfinal=False):
        collector = self._self_collector
        if collector.collecting:
            collector.track(data, isfinal)
        return collector.parser.Parse(data, isfinal)

    def ParseFile(self, file):
        collector = self._self_collector
        if collector.collecting:
            collector.stop()
        return collector.parser.ParseFile(file)


@before_modify_return
def _parser_create(func, instance, args, kwargs):
    register_call("xml.parsers.expat.ParserCreate", "deserialize_op")

    context = ctx.get_current_context()
    if not context or not isinstance(context.body, str):
        return None
    return CollectingParser(func(*args, **kwargs), context)


@on_import("xml.parsers.expat")
def patch(m):
    """
    patching module xml.parsers.expat
    - patches function ParserCreate(encoding, namespace_separator)
    (src: https://github.com/python/cpython/blob/main/Modules/pyexpat.c)
    """
    patch_function(m, "ParserCreate", _parser_create)
