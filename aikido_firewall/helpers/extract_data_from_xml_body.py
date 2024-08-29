"""Exports extract_data_from_xml_body helper function"""

import aikido_firewall.context as ctx


def extract_data_from_xml_body(user_input, root_element):
    """Extracts all attributes from the xml and adds them to context"""
    context = ctx.get_current_context()
    if not isinstance(context.body, str) or user_input != context.body:
        return

    extracted_xml_attrs = context.xml
    for el in root_element:
        print(extracted_xml_attrs)
        for k, v in el.items():
            print("Key : %s, Value : %s", k, v)
            if not extracted_xml_attrs.get(k):
                extracted_xml_attrs[k] = set()
            extracted_xml_attrs[k].add(v)
    context.set_as_current_context()