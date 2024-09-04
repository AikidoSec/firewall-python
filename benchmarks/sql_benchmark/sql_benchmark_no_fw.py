# pylint: skip-file
import time
import random

def database_conn():
    import pymysql

    return pymysql.connect(host="127.0.0.1", user="user", passwd="password", db="db")

def run_sql_no_fw(sql):

    conn = database_conn()
    cursor = conn.cursor()
    t_start = time.time()
    cursor.execute(sql)
    time.sleep(1/1000) # 1ms simulated cloud delay
    t_end = time.time()

    return t_end - t_start # Delta

def benchmark():
    sql_without_fw_data = []
    for i in range(5000):
        query = "INSERT INTO dogs (dog_name, isadmin) VALUES('example.com', 1)"
        sql_without_fw_data.append(run_sql_no_fw(query))
        time.sleep(random.uniform(0.001, 0.002))
    print((sum(sql_without_fw_data)/5000)*1000*1000, "microseconds")
benchmark()
