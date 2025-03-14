from __init__ import events
from utils import App, Request

flask_mongo_app = App(8094)

# Create dog :
status_code_create = Request(route="/create", body={
    "dog_name": "bobby_tables", "pswd": "bobby123"
}, data_type="form").execute(flask_mongo_app.urls["enabled"])
assert status_code_create == 200

# Payloads :
flask_mongo_app.add_payload(
    "nosql", test_event=events["flask_mongo_attack"],
    safe_request=Request("/auth", body={"dog_name": "bobby_tables", "pswd": "bobby123"}),
    unsafe_request=Request("/auth", body={"dog_name": "bobby_tables", "pswd": { "$ne": ""}})
)
flask_mongo_app.add_payload(
    "nosql_force", test_event=events["flask_mongo_attack"],
    safe_request=Request("/auth_force", body={"dog_name": "bobby_tables", "pswd": "bobby123"}),
    unsafe_request=Request("/auth_force", body={"dog_name": "bobby_tables", "pswd": { "$ne": ""}})
)

flask_mongo_app.test_all_payloads()
