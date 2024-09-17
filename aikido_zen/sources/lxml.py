"""
Sink module for `xml`, python's built-in function
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.extract_data_from_xml_body import (
    extract_data_from_xml_body,
)
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION


@importhook.on_import("lxml.etree")
def on_lxml_import(eltree):
    """
    Hook 'n wrap on `lxml.etree`.
    - Wrap on fromstring() function
    - Wrap on
    Returns : Modified `lxml.etree` object
    """
    if not pkg_compat_check("lxml", required_version=ANY_VERSION):
        return eltree
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
    return modified_eltree
