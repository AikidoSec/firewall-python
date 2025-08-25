import json

from utils import App, Request

flask_mongo_app = App(8094)

def create_test_dog():
    Request("/create", data_type="form", body={
        {"dog_name": "bobby", "pswd": "1234"}
    }).execute(flask_mongo_app.urls["enabled"])

flask_mongo_app.add_payload(
    "test_nosql_injection",
    safe_request=Request("/auth", data_type="form", body=json.dumps(
        {"dog_name": "bobby", "pswd": "1234"}
    )),
    unsafe_request=Request("/auth", data_type="form", body=json.dumps(
        {"dog_name": "bobby", "pswd": { "$ne": ""}}
    )),
    test_event={
        "blocked": True,
        "kind": "nosql_injection",
        'metadata': {'filter': '{"dog_name": "bobby_tables", "pswd": {"$ne": ""}}'},
        'operation': "pymongo.collection.Collection.find",
        'pathToPayload': ".pswd",
        'payload': '{"$ne": ""}',
        'source': "body",
    }
)

create_test_dog()
flask_mongo_app.test_all_payloads()
