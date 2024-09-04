# pylint: skip-file
import time
import random


def database_conn(MongoClient):

    client = MongoClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]

def run_nosql_find(query, MongoClient):
    db = database_conn(MongoClient)
    dogs = db["dogs"]

    t_start = time.time()
    dogs.find_one(query)
    t_end = time.time()

    return t_end - t_start # Delta


def benchmark():
    from pymongo import MongoClient
    nosql_with_fw_data = []
    for i in range(5000):
        query = {"dog_name": "Doggo 1"}
        nosql_with_fw_data.append(run_nosql_find(query, MongoClient))
        time.sleep(random.uniform(0.001, 0.002))
    print((sum(nosql_with_fw_data)/5000)*1000*1000, "microseconds")

benchmark()
