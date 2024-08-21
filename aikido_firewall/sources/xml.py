"""
Sink module for `xml`, python's built-in function
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.extract_strings_from_user_input import (
    reset_userinput_cache_for_given_source,
)
from aikido_firewall.context import get_current_context


def process_xml(user_input, root_element):
    """Extracts all attributes from the xml and adds them to context"""
    context = get_current_context()
    if not isinstance(context.body, str) or user_input != context.body:
        return

    extracted_xml_attrs = dict()
    for el in root_element:
        for k, v in el.items():
            if not extracted_xml_attrs.get(k):
                extracted_xml_attrs[k] = set()
            extracted_xml_attrs[k].add(v)
        extracted_xml_attrs.update(set(el.items()))

    reset_userinput_cache_for_given_source("xml")
    context.xml.append(extracted_xml_attrs)
    context.set_as_current_context()


@importhook.on_import("xml.etree.ElementTree")
def on_xml_import(eltree):
    """
    Hook 'n wrap on `xml.etree.ElementTree`, python's built-in xml lib
    Our goal is to create a new and mutable aikido parser class
    Returns : Modified ElementTree object
    """
    modified_eltree = importhook.copy_module(eltree)
    copy_xml_parser = copy.deepcopy(eltree.XMLParser)

    class MutableAikidoXMLParser:
        """Aikido's mutable connection class"""

        def __init__(self, *args, **kwargs):
            self._former_xml_parser = copy_xml_parser(*args, **kwargs)
            self._feed_func_copy = copy.deepcopy(self._former_xml_parser.feed)

        def __getattr__(self, name):
            if name != "feed":
                return getattr(self._former_xml_parser, name)

            # Return aa function dynamically
            def feed(data):
                former_feed_result = self._feed_func_copy(data)

                # Fetch the data, this should just return an internal attribute and not close a stream
                # Or something that is noticable by the end-user
                parsed_xml = self.target.close()
                process_xml(user_input=data, root_element=parsed_xml)

                return former_feed_result

            return feed

    # pylint: disable=no-member
    setattr(eltree, "XMLParser", MutableAikidoXMLParser)
    setattr(modified_eltree, "XMLParser", MutableAikidoXMLParser)

    logger.debug("Wrapped `xml` module")
    return modified_eltree
