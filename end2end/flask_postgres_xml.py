from __init__ import events
from utils import App, Request

flask_xml_app = App(8092)

flask_xml_app.add_payload(
    "sql_with_xml", test_event=events["flask_xml_attack"],
    safe_request=Request(route="/xml_post", body='<dogs><dog dog_name="Bobby" /></dogs>', data_type="form"),
    unsafe_request=Request(route="/xml_post", body='<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>', data_type="form")
)
flask_xml_app.add_payload(
    "sql_with_lxml", test_event=events["flask_xml_attack"],
    safe_request=Request(route="/xml_post_lxml", body='<dogs><dog dog_name="Bobby" /></dogs>', data_type="form"),
    unsafe_request=Request(route="/xml_post_lxml", body='<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>', data_type="form")
)

flask_xml_app.test_all_payloads()
