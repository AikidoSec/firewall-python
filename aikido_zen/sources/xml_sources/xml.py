from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
)
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, after


@after
def _feed(func, instance, args, kwargs, return_value):
    # Fetches XML data, this should just return an internal attribute
    # and not close a stream or something that is noticable by the end-user
    parsed_xml = instance.target.close()
    data = get_argument(args, kwargs, 0, "data")
    extract_data_from_xml_body(user_input=data, root_element=parsed_xml)


@on_import("xml.etree.ElementTree")
def patch(m):
    patch_function(m, "XMLParser.feed", _feed)
