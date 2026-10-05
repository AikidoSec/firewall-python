"""Exports extract_data_from_xml_body helper function"""

import aikido_zen.context as ctx
from aikido_zen.helpers.logging import logger


def extract_data_from_xml_body(user_input, root_element):
    """Extracts all attributes and text from the xml and adds them to context"""
    try:
        context = ctx.get_current_context()
        if not context or not isinstance(context.body, str):
            return

        if isinstance(user_input, (bytes, bytearray, memoryview)):
            user_input = bytes(user_input).decode("utf-8", errors="replace")
        if user_input != context.body:
            return

        extracted_xml = context.xml
        for element in root_element.iter():
            if not isinstance(element.tag, str):
                continue
            for key, value in element.items():
                extracted_xml.setdefault(key, set()).add(value)
            for text in (element.text, element.tail):
                if text:
                    stripped = text.strip()
                    if stripped:
                        extracted_xml.setdefault(element.tag, set()).update(
                            (text, stripped)
                        )
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)
