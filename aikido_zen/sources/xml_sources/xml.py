from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
    body_reader,
    add_parsed_tree_to_context,
    IterparseCollector,
)
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.sources.xml_sources.expat import CollectingParser


def _expat_hook_collects(args, kwargs):
    # A pure-Python parser such as defusedxml's runs on expat, so the expat hook
    # already stores this parse; walking the tree again would store it twice.
    try:
        parser = get_argument(args, kwargs, 1, "parser")
        return isinstance(getattr(parser, "parser", None), CollectingParser)
    except Exception:
        return False


def _fromstring(func, instance, args, kwargs):
    register_call("xml.etree.ElementTree.fromstring", "deserialize_op")
    # Checked before parsing, because a pure-Python parser drops its expat parser on close.
    expat_hook_collects = _expat_hook_collects(args, kwargs)
    root = func(*args, **kwargs)
    if not expat_hook_collects:
        text = get_argument(args, kwargs, 0, "text")
        extract_data_from_xml_body(user_input=text, root_element=root)
    return root


@after
def _fromstringlist(func, instance, args, kwargs, return_value):
    strings = get_argument(args, kwargs, 0, "sequence")
    register_call("xml.etree.ElementTree.fromstringlist", "deserialize_op")

    for text in strings:
        extract_data_from_xml_body(user_input=text, root_element=return_value)


def _parse(func, instance, args, kwargs):
    register_call("xml.etree.ElementTree.ElementTree.parse", "deserialize_op")
    if _expat_hook_collects(args, kwargs):
        return func(*args, **kwargs)
    reader, new_args, new_kwargs = body_reader(args, kwargs, "source")
    root = func(*new_args, **new_kwargs)
    add_parsed_tree_to_context(reader, root)
    return root


def _iterparse(func, instance, args, kwargs):
    register_call("xml.etree.ElementTree.iterparse", "deserialize_op")
    reader, new_args, new_kwargs = body_reader(args, kwargs, "source")
    events = func(*new_args, **new_kwargs)
    if reader is None:
        return events
    return IterparseCollector(events, reader)


@on_import("xml.etree.ElementTree")
def patch(m):
    """
    patching module xml.etree.ElementTree
    - patches function fromstring(text, ...) and XML(text, ...), the same function
    - patches function fromstringlist(sequence, ...)
    - patches method ElementTree.parse(source, ...), which parse(source, ...) calls
    - patches function iterparse(source, ...)
    (src: https://github.com/python/cpython/blob/bc1a6ecfab02075acea79f8460a2dce70c61b2fd/Lib/xml/etree/ElementTree.py#L1370)
    """
    patch_function(m, "fromstring", _fromstring)
    patch_function(m, "XML", _fromstring)
    patch_function(m, "fromstringlist", _fromstringlist)
    patch_function(m, "ElementTree.parse", _parse)
    patch_function(m, "iterparse", _iterparse)
