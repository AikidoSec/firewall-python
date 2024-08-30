"""SQL algorithm benchmarks"""
import time
import random
import numpy as np
from aikido_firewall.vulnerabilities.path_traversal.detect_path_traversal import detect_path_traversal


def run_path_traversal_timed(path, user_input):
    """Returns in ms the time it took to run the sql algorithm"""
    start_time = time.time()
    detect_path_traversal(path, user_input)
    end_time = time.time()
    return (end_time - start_time) * 1000 # In ms

PATHS_ARRAY = [
    ("..\\test.txt", "..\\"),
    ("../test.txt", "../"),
    ("directory/text.txt", "text.txt"),
    ("/appdata/storage/file.txt", "/storage/file.txt"),
    ("../../../../test.txt", "../../../../"),
    ("", "test"),
    ("directory/alkfjjljlekgslgkslkgsklngsrlknglkrsgnrsklgnslknglkrsg.txt", "alkfjjljlekgslgkslkgsklngsrlknglkrsgnrsklgnslknglkrsg.txt"),
]

def run_all_paths():
    total_time_ms = []
    for path in PATHS_ARRAY:
        total_time_ms.append(run_path_traversal_timed(path[0], path[1]))
    return sum(total_time_ms)/len(total_time_ms)

def main():
    total = []
    for i in range(2000):
        total.append(run_all_paths())
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
