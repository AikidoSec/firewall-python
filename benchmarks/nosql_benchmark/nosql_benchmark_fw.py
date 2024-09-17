# pylint: skip-file
import time
import random

normal_context_json = {
    "source": "django",
    "method": "POST",
    "headers": {
        "HEADER_1": "header 1 value",
        "HEADER_2": "Header 2 value",
        "COOKIE": "sessionId=abc123xyz456;",
        "HOST": "example.com",
    },
    "cookies": {"sessionId": "abc123xyz456"},
    "url": "https://example.com/hello",
    "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
    "body": {
        "query": {"dog_name": "Doggo 1"},
    },
    "route": "/hello",
    "subdomains": [],
    "user": None,
    "remote_address": "198.51.100.23",
    "parsed_userinput": {},
    "xml": {},
    "outgoing_req_redirects": [],
}

def database_conn(MongoClient):

    client = MongoClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]

def run_nosql_find(query, MongoClient):
    db = database_conn(MongoClient)
    dogs = db["dogs"]

    t_start = time.monotonic()
    dogs.find(query)
    time.sleep(1/1000)
    t_end = time.monotonic()

    return t_end - t_start # Delta

def set_context(context_json):
    from aikido_zen.context import Context
    from aikido_zen.background_process.ipc_lifecycle_cache import IPCLifecycleCache
    context = Context(context_obj=context_json)
    context.set_as_current_context()
    IPCLifecycleCache(context)

def benchmark():
    import aikido_zen.sinks.pymongo
    from pymongo import MongoClient
    nosql_with_fw_data = []
    set_context(normal_context_json)
    for i in range(5000):
        query = {"dog_name": "Doggo 1"}
        nosql_with_fw_data.append(run_nosql_find(query, MongoClient))
        time.sleep(random.uniform(0.001, 0.002))
    print((sum(nosql_with_fw_data)/5000)*1000*1000, "microseconds")

benchmark()
