"""
Sink module for `xml`, python's built-in function
"""

import copy
import importhook
from aikido_firewall.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
)
from aikido_firewall.background_process.packages import add_wrapped_package


@importhook.on_import("lxml.etree")
def on_lxml_import(eltree):
    """
    Hook 'n wrap on `lxml.etree`.
    - Wrap on fromstring() function
    - Wrap on
    Returns : Modified `lxml.etree` object
    """
    modified_eltree = importhook.copy_module(eltree)

    former_fromstring = copy.deepcopy(eltree.fromstring)

    def aikido_fromstring(text, *args, **kwargs):
        res = former_fromstring(text, *args, **kwargs)
        extract_data_from_xml_body(user_input=text, root_element=res)
        return res

    former_fromstringlist = copy.deepcopy(eltree.fromstringlist)

    def aikido_fromstringlist(strings, *args, **kwargs):
        res = former_fromstringlist(strings, *args, **kwargs)
        for string in strings:
            extract_data_from_xml_body(user_input=string, root_element=res)
        return res

    # pylint: disable=no-member
    setattr(eltree, "fromstring", aikido_fromstring)
    setattr(modified_eltree, "fromstring", aikido_fromstring)

    # pylint: disable=no-member
    setattr(eltree, "fromstringlist", aikido_fromstringlist)
    setattr(modified_eltree, "fromstringlist", aikido_fromstringlist)
    add_wrapped_package("lxml")
    return modified_eltree
