"""SQL algorithm benchmarks"""
import time
import random
import numpy as np
from aikido_firewall.vulnerabilities.nosql_injection import find_filter_part_with_operators

def run_nosql_timed(user_input, _filter):
    """Returns in ms the time it took to run the sql algorithm"""
    start_time = time.time()
    find_filter_part_with_operators(user_input, _filter)
    end_time = time.time()
    return (end_time - start_time) * 1000 # In ms

JSON_ARRAY = [
    {"$ne": None}, {"username": {"$ne": None}}, 
    {"$gt": "21"}, {"$gt": "21", "$lt": "100"}, 
    {"$and": [{"someAgeField": {"$gt": "21", "$lt": "100"}}]}
]

def run_all_files():
    total_time_ms = []
    for nosql in JSON_ARRAY:
            total_time_ms.append(run_nosql_timed(nosql, nosql))
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
