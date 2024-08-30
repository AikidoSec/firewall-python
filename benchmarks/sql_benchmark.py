"""SQL algorithm benchmarks"""
import time
import os
import random
import numpy as np
from aikido_firewall.vulnerabilities.sql_injection import detect_sql_injection
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL

def run_sql_algorithm_timed_ms(query, user_input, dialect):
    """Returns in ms the time it took to run the sql algorithm"""
    start_time = time.time()
    detect_sql_injection(query, user_input, dialect)
    end_time = time.time()
    return (end_time - start_time) * 1000 # In ms

def file_paths():
    script_dir = os.path.dirname(__file__)
    return [
        # Taken from https://github.com/payloadbox/sql-injection-payload-list/tree/master
        os.path.join(script_dir, "../aikido_firewall/vulnerabilities/sql_injection/payloads/Auth_Bypass.txt"),
        os.path.join(script_dir, "../aikido_firewall/vulnerabilities/sql_injection/payloads/postgres.txt"),
        os.path.join(script_dir, "../aikido_firewall/vulnerabilities/sql_injection/payloads/mysql.txt"),
        os.path.join(script_dir, "../aikido_firewall/vulnerabilities/sql_injection/payloads/mssql_and_db2.txt"),
    ]
QUERIES = [
    "'UNION 123' UNION \"UNION 123\"",
    "Roses are red rollbacks are blue",
    "I'm writting you",
    "Roses are red cREATE are blue",
    "Roses <> violets",
    "abcdefghijklmnop@hotmail.com",
    "Termin;ate",
]
def run_all_files():
    total_time_ms = []
    dialect = MySQL()
    for sql in QUERIES:
        total_time_ms.append(run_sql_algorithm_timed_ms(sql, sql, dialect))
        new_query = f"SELECT * FROM users WHERE id = {sql}"
        total_time_ms.append(run_sql_algorithm_timed_ms(new_query, new_query, dialect))
    return sum(total_time_ms)/len(total_time_ms)

def main():
    total = []
    for i in range(2000):
        total.append(run_all_files())
        time.sleep(random.uniform(0.001, 0.005))
    times = np.array(total)
    mean_time = np.mean(times) * 1000
    median_time = np.median(times) * 1000
    std_dev_time = np.std(times) * 1000
    variance_time = np.var(times) * 1000
    print("Mean time in µs", round(mean_time, 3))
    print("Median time in µs", round(median_time, 3))
    print("Standard Deviation in µs", round(std_dev_time, 3))
    print("Variance in µs", round(variance_time, 3))
main()
