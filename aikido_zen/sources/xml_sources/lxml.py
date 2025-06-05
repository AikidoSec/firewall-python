from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
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


@on_import("lxml.etree", "lxml")
def patch(m):
    """
    patching module lxml.etree
    - patches function fromstring(text, ...)
    - patches function fromstringlist(strings, ...)
    (github src: https://github.com/lxml/lxml/blob/fe271a4b5a32e6e54d10983683f2f32b0647209a/src/lxml/etree.pyx#L3411)
    """
    patch_function(m, "fromstring", _fromstring)
    patch_function(m, "fromstringlist", _fromstringlist)
