"""
Sink module for `xml`, python's built-in function
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
)


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

                # Fetch the data, this should just return an internal attribute
                # and not close a stream or something that is noticable by the end-user
                parsed_xml = self.target.close()
                extract_data_from_xml_body(user_input=data, root_element=parsed_xml)

                return former_feed_result

            return feed

    # pylint: disable=no-member
    setattr(eltree, "XMLParser", MutableAikidoXMLParser)
    setattr(modified_eltree, "XMLParser", MutableAikidoXMLParser)

    logger.debug("Wrapped `xml` module")
    return modified_eltree
