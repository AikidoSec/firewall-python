# pylint: skip-file
import time
import random

def database_conn():
    from pymongo import MongoClient

    client = MongoClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]

def run_nosql_find(query):
    db = database_conn()
    dogs = db["dogs"]

    t_start = time.time()
    dogs.find_one(query)
    time.sleep(1/1000) # 1ms simulated cloud delay
    t_end = time.time()

    return t_end - t_start # Delta

def benchmark():
    nosql_without_fw_data = []
    for i in range(5000):
        query = "SELECT * FROM dogs"
        nosql_without_fw_data.append(run_sql_no_fw(query))
        time.sleep(random.uniform(0.001, 0.002))
    print((sum(nosql_without_fw_data)/5000)*1000*1000, "microseconds")
benchmark()
