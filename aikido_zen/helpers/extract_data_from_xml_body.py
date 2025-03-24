"""Exports extract_data_from_xml_body helper function"""

import aikido_zen.context as ctx
from aikido_zen.helpers.logging import logger


def extract_data_from_xml_body(user_input, root_element):
    """Extracts all attributes from the xml and adds them to context"""
    try:
        context = ctx.get_current_context()
        if (
            not context
            or not isinstance(context.body, str)
            or user_input != context.body
        ):
            return

        extracted_xml_attrs = context.xml
        for el in root_element:
            for k, v in el.items():
                if not extracted_xml_attrs.get(k):
                    extracted_xml_attrs[k] = set()
                extracted_xml_attrs[k].add(v)
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)
