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
        tag = None
        for element in root_element.iter():
            if isinstance(element.tag, str):
                tag = element.tag
                texts = (element.text, element.tail)
                for key, value in element.items():
                    extracted_xml.setdefault(key, set()).add(value)
            else:
                # The text after a comment or processing instruction is in its tail.
                texts = (element.tail,) if tag else ()
            for text in texts:
                if not text:
                    continue
                stripped = text.strip()
                if not stripped:
                    continue
                extracted_xml.setdefault(tag, set()).update((text, stripped))
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred when extracting XML: %s", e)
