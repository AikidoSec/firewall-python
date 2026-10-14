from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
    body_reader,
    add_parsed_tree_to_context,
    IterparseCollector,
)
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, after, patch_function


@after
def _fromstring(func, instance, args, kwargs, return_value):
    text = get_argument(args, kwargs, 0, "text")
    register_call("lxml.etree.fromstring", "deserialize_op")

    if text:
        extract_data_from_xml_body(user_input=text, root_element=return_value)


@after
def _fromstringlist(func, instance, args, kwargs, return_value):
    strings = get_argument(args, kwargs, 0, "strings")
    register_call("lxml.etree.fromstringlist", "deserialize_op")

    for text in strings:
        extract_data_from_xml_body(user_input=text, root_element=return_value)


def _parse(func, instance, args, kwargs):
    register_call("lxml.etree.parse", "deserialize_op")
    reader, new_args, new_kwargs = body_reader(args, kwargs, "source")
    tree = func(*new_args, **new_kwargs)
    if reader is not None:
        add_parsed_tree_to_context(reader, tree.getroot())
    return tree


def _iterparse(func, instance, args, kwargs):
    register_call("lxml.etree.iterparse", "deserialize_op")
    reader, new_args, new_kwargs = body_reader(args, kwargs, "source")
    events = func(*new_args, **new_kwargs)
    if reader is None:
        return events
    return IterparseCollector(events, reader)


@on_import("lxml.etree", "lxml")
def patch(m):
    """
    patching module lxml.etree
    - patches function fromstring(text, ...) and XML(text, ...)
    - patches function fromstringlist(strings, ...)
    - patches function parse(source, ...)
    - patches class iterparse(source, ...)
    (github src: https://github.com/lxml/lxml/blob/fe271a4b5a32e6e54d10983683f2f32b0647209a/src/lxml/etree.pyx#L3411)
    """
    patch_function(m, "fromstring", _fromstring)
    patch_function(m, "XML", _fromstring)
    patch_function(m, "fromstringlist", _fromstringlist)
    patch_function(m, "parse", _parse)
    patch_function(m, "iterparse", _iterparse)
