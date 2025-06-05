from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
)
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after


@after
def _fromstring(func, instance, args, kwargs, return_value):
    text = get_argument(args, kwargs, 0, "text")
    register_call("xml.etree.ElementTree.fromstring", "deserialize_op")

    extract_data_from_xml_body(user_input=text, root_element=return_value)


@after
def _fromstringlist(func, instance, args, kwargs, return_value):
    strings = get_argument(args, kwargs, 0, "sequence")
    register_call("xml.etree.ElementTree.fromstringlist", "deserialize_op")

    for text in strings:
        extract_data_from_xml_body(user_input=text, root_element=return_value)


@on_import("xml.etree.ElementTree")
def patch(m):
    """
    patching module xml.etree.ElementTree
    - patches function fromstring(text, ...)
    - patches function fromstringlist(sequence, ...)
    (src: https://github.com/python/cpython/blob/bc1a6ecfab02075acea79f8460a2dce70c61b2fd/Lib/xml/etree/ElementTree.py#L1370)
    """
    patch_function(m, "fromstring", _fromstring)
    patch_function(m, "fromstringlist", _fromstringlist)
